# Integrate a frozen planner

```python
from fastrovervla import FastRoverPolicy, FrameContext

policy = FastRoverPolicy()  # generic fixed K=8 defaults, not a dataset-tuned claim

def planner(context):
    # Run your model using context.observation and context.instruction.
    # Return decoded (speed in m/s, curvature in 1/m) pairs.
    return [(1.2, 0.02)] * 6

result = policy.step(
    FrameContext("scene-001", speed_mps=1.0, curvature_m_inv=0.01,
                 observation=current_image, instruction="Follow the trail."),
    planner,
)
waypoints = result.waypoints
```

The callback is invoked only on refresh; it is not evaluated and discarded at reuse
updates. Use one policy instance per ordered stream, and provide a stable sequence
identifier. The caller supplies measured state at each update. `observation` is an
opaque payload; the execution core never loads a new image during reuse.

For paper configurations:

```python
from fastrovervla.evaluation import load_config
config, refresh = load_config("configs/orad_qwen3.json")
policy = FastRoverPolicy(config, refresh)
```

The callback must provide finite numeric pairs. Negative decoded speeds are clamped
to zero; nonfinite values raise `ValueError`. Empty lists deliberately use current
motion fallback; `used_motion_fallback` and `parsed_actions` expose this distinction.
Parsing free-form model text and retries belong in the backbone adapter. Do not
silently present malformed output as a successful model response.

Backbone examples and model setup are documented by their maintainers:

- [Qwen3-VL](https://huggingface.co/docs/transformers/en/model_doc/qwen3_vl)
- [Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL)
- [MiniCPM-V](https://github.com/OpenBMB/MiniCPM-V)
- [InternVL](https://github.com/OpenGVLab/InternVL)

These are upstream references, not bundled or newly tested GPU adapters. The archived
paper's independently measured real-request numbers describe its original prompts,
decoding settings and hardware. Plugging in a new callback does not reproduce those
latency measurements automatically.
