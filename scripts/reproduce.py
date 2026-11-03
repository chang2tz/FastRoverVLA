"""Recompute the main Qwen3 table and matched-refresh controls on a CPU."""

import argparse
import csv
import json
import math
from pathlib import Path

from fastrovervla.evaluation import load_config, load_rows, replay

ROOT = Path(__file__).resolve().parents[1]

# Displayed ADE/FDE cells in the manuscript's controlled Qwen3 tables.
PAPER = {
    "orad": {"every": (.384, .726), "fixed": (.330, .599),
             "no_reuse_correction": (.507, .924), "no_alignment": (.454, .852),
             "no_writeback": (.396, .728), "no_fresh_blend": (.327, .593),
             "no_speed_bound": (.326, .592), "null": (.394, .733),
             "motion_only": (.330, .599)},
    "rellis": {"every": (.387, .820), "fixed": (.289, .584),
               "no_reuse_correction": (.455, .876), "no_alignment": (.419, .844),
               "no_writeback": (.371, .738), "no_fresh_blend": (.266, .527),
               "no_speed_bound": (.267, .527), "null": (.335, .646),
               "motion_only": (.261, .515)},
}


def check_displayed(summary, expected):
    assert tuple(round(summary[key], 3) for key in ("ade", "fde")) == expected, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Fail on a trajectory, schedule or result mismatch")
    parser.add_argument("--output", type=Path, default=ROOT / "results/reproduction")
    args = parser.parse_args()
    expected = json.loads((ROOT / "data/benchmark/reference_metrics.json").read_text())
    summaries, errors = [], []
    for dataset in ("orad", "rellis"):
        rows = load_rows(ROOT / f"data/benchmark/{dataset}.jsonl")
        cfg, rule = load_config(ROOT / f"configs/{dataset}_qwen3.json")
        for mode in ("every", "fixed", "adaptive"):
            summary, predictions = replay(rows, cfg, rule, mode=mode)
            summaries.append({"dataset": dataset, **summary})
            if args.verify and mode in PAPER[dataset]:
                check_displayed(summary, PAPER[dataset][mode])
            if mode == "adaptive" and args.verify:
                for row, pred in zip(rows, predictions):
                    assert row["reference_refresh"] == pred["refreshed"], (dataset, row["id"], "schedule")
                    for key, ref in (("actions", "reference_actions"), ("waypoints", "reference_waypoints")):
                        error = max(abs(a - b) for p, q in zip(pred[key], row[ref]) for a, b in zip(p, q))
                        errors.append(error)
                        assert error < 1e-12, (row["id"], key, error)
                assert summary["plan_admissions"] == (37 if dataset == "orad" else 31)
                for key in ("ade", "fde", "rmse", "l2", "fde_p95"):
                    assert math.isclose(summary[key], expected[dataset]["valid"][key], abs_tol=1e-12)
        for control in ("direct_stale", "no_reuse_correction", "no_alignment", "no_writeback",
                        "no_fresh_blend", "no_speed_bound", "kinematic", "null", "motion_only"):
            summary, predictions = replay(rows, cfg, rule, mode="reference", control=control)
            summaries.append({"dataset": dataset, **summary})
            if args.verify and control in PAPER[dataset]:
                check_displayed(summary, PAPER[dataset][control])
            if args.verify and control == "kinematic":
                for key in ("ade", "fde", "rmse", "l2", "fde_p95"):
                    assert math.isclose(summary[key], expected[dataset]["kinematic"][key], abs_tol=1e-12)
            if args.verify and control == "direct_stale":
                for key in ("ade", "fde", "rmse", "l2", "fde_p95"):
                    assert math.isclose(summary[key], expected[dataset]["direct_stale"][key], abs_tol=1e-12)
            if args.verify and control == "no_reuse_correction":
                for row, pred in zip(rows, predictions):
                    if row["reference_refresh"]:
                        assert max(abs(a - b) for p, q in zip(pred["actions"], row["reference_actions"])
                                   for a, b in zip(p, q)) < 1e-12
        print(f"{dataset.upper()}: {len(rows)} windows; primary schedule and controls computed")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
    with (args.output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    proof = {"verified": args.verify, "windows": 1286, "actual_model_requests": 0,
             "max_primary_trajectory_difference": max(errors) if errors else None}
    (args.output / "verification.json").write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
