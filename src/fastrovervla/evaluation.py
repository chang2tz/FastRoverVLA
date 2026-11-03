"""Frozen-prediction replay. Model requests during this evaluation: zero."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from statistics import fmean

from .execution import FastRoverPolicy, FrameContext, PolicyConfig
from .geometry import blend, fill, integrate, speed_bound
from .refresh import RefreshConfig, percentile


def load_config(path: str | Path) -> tuple[PolicyConfig, RefreshConfig]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return PolicyConfig(**payload["execution"]), RefreshConfig(**payload["refresh"])


def load_rows(path: str | Path) -> list[dict]:
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("Replay input must contain at least one window")
    keys = [(r["sequence_id"], r["frame_index"]) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate sequence/frame keys in replay input")
    if keys != sorted(keys):
        raise ValueError("Replay rows must be ordered by sequence_id and frame_index")
    return rows


def metrics(prediction: Sequence, target: Sequence) -> dict[str, float]:
    if len(prediction) != len(target) or not target:
        raise ValueError("Prediction and target must share a nonempty horizon")
    distances = [math.dist(p, t) for p, t in zip(prediction, target)]
    squared = [(p[j] - t[j]) ** 2 for p, t in zip(prediction, target) for j in range(2)]
    return {"ade": fmean(distances), "fde": distances[-1],
            "rmse": math.sqrt(fmean(squared)), "l2": math.sqrt(sum(squared))}


def replay(rows: Sequence[dict], config: PolicyConfig, refresh: RefreshConfig,
           *, mode: str = "adaptive", target: str = "ground_truth",
           control: str = "full") -> tuple[dict, list[dict]]:
    controls = {"full", "direct_stale", "no_reuse_correction", "no_alignment", "no_writeback",
                "no_fresh_blend", "no_speed_bound", "kinematic", "null", "motion_only"}
    if control not in controls:
        raise ValueError(f"Unknown control: {control}")
    if mode not in {"adaptive", "fixed", "every", "reference"}:
        raise ValueError(f"Unknown replay mode: {mode}")
    if not rows:
        raise ValueError("Replay needs at least one window")
    cfg = replace(config, beta=1.0) if control == "no_alignment" else config
    if control == "no_fresh_blend":
        cfg = replace(cfg, alpha=1.0)
    if control == "no_speed_bound":
        cfg = replace(cfg, speed_step=None)
    if control == "null":
        # The archived null control directly initializes a zero action plan.
        # It does not blend that substitute with motion before beta alignment.
        cfg = replace(cfg, alpha=1.0)
    policy = FastRoverPolicy(cfg, replace(refresh, mode="adaptive" if mode == "reference" else mode))
    # A separate, unmodified policy supplies the common refresh schedule for controls.
    scheduler = FastRoverPolicy(config, replace(refresh, mode="adaptive" if mode == "reference" else mode))
    predictions = []
    retained = []
    sequence = None
    refreshes = 0
    for row in rows:
        if row["sequence_id"] != sequence:
            retained = []
            sequence = row["sequence_id"]
        context = FrameContext(sequence, *row["observed_action"])
        primary = scheduler.step(context, lambda _: row["decoded_actions"],
                                 force_refresh=bool(row["reference_refresh"]) if mode == "reference" else None)
        request = primary.refreshed
        observed = (max(0.0, float(row["observed_action"][0])), float(row["observed_action"][1]))
        if control == "motion_only":
            fresh = not retained
            active = [observed] * config.horizon if fresh else fill(retained, observed, config.horizon)
            corrected = speed_bound(blend(active, observed, config.beta), observed, config.speed_step)
            retained = list(corrected[1:])
            positions = integrate(corrected, config.dt_s)
            request = False
        elif control in {"direct_stale", "no_reuse_correction", "no_writeback"}:
            if request:
                from .geometry import actions
                raw = actions(row["decoded_actions"], config.horizon)
                retained = blend(fill(raw, observed, config.horizon), observed, config.alpha)
                if control == "no_reuse_correction":
                    retained = speed_bound(blend(retained, observed, config.beta), observed, config.speed_step)
            active = fill(retained, observed, config.horizon)
            corrected = (speed_bound(blend(active, observed, config.beta), observed, config.speed_step)
                         if control == "no_writeback" else active)
            positions = integrate(corrected, config.dt_s)
            retained = list(active[1:])
        else:
            raw = ([observed] * config.horizon if control == "kinematic" else
                   [(0.0, 0.0)] * config.horizon if control == "null" else row["decoded_actions"])
            step = policy.step(context, lambda _: raw, force_refresh=request)
            corrected, positions = list(step.actions), list(step.waypoints)
        refreshes += int(request)
        item = {"id": row["id"], "sequence_id": sequence, "frame_index": row["frame_index"],
                "refreshed": request, "actions": corrected, "waypoints": positions,
                **metrics(positions, row[target])}
        predictions.append(item)
    summary = {"protocol": "frozen_prediction_replay", "actual_model_requests": 0,
               "mode": mode, "control": control, "target": target, "windows": len(rows),
               "plan_admissions": refreshes, "admission_rate": refreshes / len(rows),
               **{k: fmean(r[k] for r in predictions) for k in ("ade", "fde", "rmse", "l2")},
               "fde_p95": percentile([r["fde"] for r in predictions], 0.95)}
    return summary, predictions
