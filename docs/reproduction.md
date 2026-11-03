# Reproduce the numerical experiments

Run from the repository root after the editable install:

```bash
python scripts/reproduce.py --verify
```

This recomputes every-update, fixed and adaptive execution, plus nine controls for
each dataset. It verifies all 1,286 primary action horizons and trajectories against
the archived reference, all refresh decisions, exact 37/31 admission counts and full
precision ADE/FDE/RMSE/L2/P95FDE. It also verifies historical stale-reuse aggregates
and identical refresh-time outputs for the matched `no_reuse_correction` control.
Results are written to `results/reproduction/summary.csv`, `summary.json` and
`verification.json`. This is deterministic frozen-prediction replay: **zero actual
model requests**. The saved GT and measured states come from recorded sequences.

For individual policies and per-window outputs:

```bash
python -m fastrovervla replay --input data/benchmark/orad.jsonl --config configs/orad_qwen3.json --mode adaptive --output results/orad
python -m fastrovervla replay --input data/benchmark/rellis.jsonl --config configs/rellis_qwen3.json --mode adaptive --output results/rellis
```

| Dataset | Mode | ADE (m) | FDE (m) | Admissions / updates |
|---|---|---:|---:|---:|
| ORAD-3D | Every update | 0.384 | 0.726 | 636 / 636 |
| ORAD-3D | Fixed | 0.330 | 0.599 | 52 / 636 |
| ORAD-3D | FastRoverVLA | 0.327 | 0.593 | 37 / 636 |
| RELLIS-3D | Every update | 0.387 | 0.820 | 650 / 650 |
| RELLIS-3D | Fixed | 0.289 | 0.584 | 74 / 650 |
| RELLIS-3D | FastRoverVLA | 0.266 | 0.526 | 31 / 650 |

## Controls

`--mode reference` uses the archived primary refresh flags. The other modes derive
the schedule from decoded actions and the frozen configuration. All component controls
use the unmodified full-method refresh schedule, so an ablation does not quietly
change its own refresh times.

- `direct_stale`: alpha blend at refresh, then consume/hold without beta or speed bound.
- `no_reuse_correction`: identical full processing at refresh, then consume/hold.
- `no_alignment`: beta = 1 at every update.
- `no_writeback`: correct for output but retain the uncorrected tail.
- `no_fresh_blend`: alpha = 1.
- `no_speed_bound`: remove only the speed-step bound.
- `kinematic` / `null`: directly initialize the active plan from measured motion /
  zero actions while sharing VLA-derived refresh times. The null substitute skips
  fresh-plan alpha blending, matching the archived source-control definition.
- `motion_only`: initialize from measured motion once per sequence, then retain corrections;
  no subsequent visual refresh and zero visual admissions. This competitive control is
  included to make the contribution of recurrent correction assessable.

## Reference-frame check

The primary table reproduces the archived benchmark reference frame. For RELLIS, its
heading preparation used a future position to define the reference orientation. The
separate past-only-heading check changes the scoring target while keeping action
inputs, predictions and schedules fixed:

```bash
python -m fastrovervla replay --input data/benchmark/rellis.jsonl --config configs/rellis_qwen3.json --mode adaptive --target past_heading_ground_truth --output results/rellis_past_heading
```

Expected ADE/FDE: approximately **0.316/0.606 m**. This release makes both target arrays
explicit; the archived heading convention must not be interpreted as a causal online
pose estimator. See [evaluation.md](evaluation.md).

The source numerical snapshot and output SHA-256 checksums are recorded in
`data/benchmark/provenance.json`. Validation-derived rule values are frozen in the
configs. The supplied primary test traces alone do not recreate validation selection,
all cross-backbone inference or the full paper's extended experiment suite.
