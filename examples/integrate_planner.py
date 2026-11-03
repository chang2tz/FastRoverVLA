"""Replace the callback with your own frozen VLA; no GPU needed for this demo."""

from fastrovervla import FastRoverPolicy, FrameContext

policy = FastRoverPolicy()


def frozen_planner(context):
    # Pass context.observation and context.instruction to your model here.
    # Convert its output to [(speed_mps, curvature_m_inv), ...].
    return [(1.2, 0.02)] * 6


for tick in range(24):
    result = policy.step(
        FrameContext(sequence_id="example", speed_mps=1.0 + tick * 0.01,
                     curvature_m_inv=0.015, observation=None,
                     instruction="Follow the trail."),
        frozen_planner,
    )
    print(tick, "refresh" if result.refreshed else "reuse", result.waypoints[-1])
