# What the evidence measures

## Controlled frozen-prediction replay

The CPU release contains 636 ORAD-3D windows from 11 sequences and 650 RELLIS-3D
windows from 3 sequences. Every-update, fixed and adaptive execution share frozen
decoded predictions and recorded motion states. Each trajectory contains six points
at 0.5 s. ADE averages Euclidean point errors; FDE is the final Euclidean error;
RMSE is the square root of mean squared **coordinate** error. Dataset summaries
average per-window metrics, and P95FDE uses linear interpolation.

Admissions read an existing prediction; they do not execute a model. Subsequent states
remain recorded states rather than states caused by the returned actions. These are
open-loop waypoint experiments, without controller, collision or route-success claims.

The archived RELLIS scoring convention and the separate past-only-heading check are
both available. Prediction inputs remain identical; only the scoring reference changes.
The primary 0.266/0.526 values should always be read with that protocol qualification.

## Independent actual-request runs

The paper also records independent serial runs with actual requests to four frozen
backbones. Qwen3 request-wrapper cost changes from 355.4 to 21.4 ms/update on ORAD
and from 443.9 to 21.3 ms/update on RELLIS: approximately 16.6x and 20.8x, respectively.
These measure request-processing cost averaged over logged updates. They are not
measured vehicle control frequency, asynchronous speedup or complete sensor-to-actuator
latency. The CPU replay does not re-run these GPU experiments.

## Interpretation

Persistent measured-motion correction explains most of the observed accuracy gain.
The motion-only control is competitive, including lower RELLIS ADE/FDE than the full
method in the primary replay. Equal-budget uniform refresh is also close to the
plan-conditioned rule. These findings constrain claims about semantic anticipation
and uniquely optimal refresh timing. Three RELLIS sequences limit independent
sequence-level statistical evidence.

The repository releases the execution method and a reproducible numerical subset.
It does not claim that every paper experiment, raw dataset, checkpoint or original
GPU runtime has been redistributed.
