# Method and execution order

An action is `(speed_mps, curvature_m_inv)`. A plan contains six actions, integrated
at 0.5 s to produce a 3 s local trajectory. Coordinates use forward x and left y.

1. On refresh, truncate decoded actions to the horizon. Compute roughness **before
   padding**. Pad a short output by repeating its final action; use measured motion
   for an empty output. Blend this fresh plan with measured motion using `alpha`.
2. At every update, including refresh, blend the active plan with measured motion
   using `beta`. Bound successive speed changes, starting from current measured
   speed; keep curvature unchanged.
3. Integrate x/y using the previous heading, then update heading by `curvature *
   speed * dt`. Return six waypoints in the current ego frame.
4. Consume the first corrected action and retain the remaining five **corrected**
   actions. The next update completes this tail to six actions before alignment.

This write-back is essential: repeatedly correcting an unmodified original plan is a
different control. `alpha` acts only at refresh; `beta` acts at every update.

## Bounded refresh

For a parsed plan, compute mean absolute successive changes in speed and curvature.
Normalize each by its validation P90, floored at `1e-4`, and take their maximum.
A single action has zero roughness; an empty output has raw roughness `(1, 1)`.
If the normalized score is **greater than or equal to** the threshold, choose the
short budget; otherwise choose the long budget. Roughness describes decoded action
variation, not an estimated terrain condition.

A budget `K` counts **reuse updates**. A refresh at update `t` is followed by reuse
at `t+1` through `t+K`; the next refresh is at `t+K+1`. Every-update execution is `K=0`.
Reset all buffer state at sequence boundaries. Never carry state across unrelated clips.

| Parameter | ORAD-3D / Qwen3 | RELLIS-3D / Qwen3 |
|---|---:|---:|
| Fresh-plan weight alpha | 0.4 | 0.65 |
| Per-update weight beta | 0.65 | 0.65 |
| Speed step (m/s per horizon step) | 0.25 | 0.25 |
| Fixed K | 12 | 8 |
| Adaptive short K | 12 | 8 |
| Adaptive long K | 32 | 24 |
| Threshold | 0.146341463414634 | 1.2073987765802507 |
| Speed roughness scale | 0.10933333333333335 | 0.11986 |
| Curvature roughness scale | 0.061 | 0.13732 |

Use the full-precision JSON configurations. Rounding the ORAD threshold to 0.1463
changes one decision and produces 38 admissions instead of 37.

The policy is a serial callback implementation. The evaluated log replay does not
demonstrate asynchronous foreground/background overlap or closed-loop vehicle control.
