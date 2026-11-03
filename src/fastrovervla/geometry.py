"""Planar Euler integration in a forward-x, left-y local frame."""

from __future__ import annotations

import math
from collections.abc import Sequence

Action = tuple[float, float]
Point = tuple[float, float]


def finite(value: float) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Actions and measured states must be finite")
    return result


def actions(value: Sequence[Sequence[float]], horizon: int) -> list[Action]:
    """Validate decoded pairs, truncate the horizon and clamp negative speeds."""
    result = []
    for pair in value[:horizon]:
        if len(pair) != 2:
            raise ValueError("Each action must contain speed (m/s) and curvature (1/m)")
        result.append((max(0.0, finite(pair[0])), finite(pair[1])))
    return result


def fill(plan: Sequence[Action], fallback: Action, horizon: int) -> list[Action]:
    result = list(plan[:horizon])
    while len(result) < horizon:
        result.append(result[-1] if result else fallback)
    return result


def blend(plan: Sequence[Action], measured: Action, weight: float) -> list[Action]:
    return [(weight * v + (1.0 - weight) * measured[0],
             weight * k + (1.0 - weight) * measured[1]) for v, k in plan]


def speed_bound(plan: Sequence[Action], measured: Action, step: float | None) -> list[Action]:
    previous = measured[0]
    result = []
    for v, k in plan:
        speed = v if step is None else max(previous - step, min(previous + step, v))
        speed = max(0.0, speed)
        result.append((speed, k))
        previous = speed
    return result


def integrate(plan: Sequence[Action], dt_s: float = 0.5) -> list[Point]:
    """Update x/y using the previous heading, then update heading."""
    x = y = heading = 0.0
    result = []
    for speed, curvature in plan:
        x += speed * math.cos(heading) * dt_s
        y += speed * math.sin(heading) * dt_s
        heading += curvature * speed * dt_s
        result.append((x, y))
    return result
