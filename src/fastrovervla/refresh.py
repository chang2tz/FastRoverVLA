"""Validation-calibrated plan roughness and bounded reuse budgets."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import fmean
from collections.abc import Sequence

from .geometry import Action


def percentile(values: Sequence[float], quantile: float) -> float:
    if not values:
        raise ValueError("Percentiles need at least one value")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def roughness(plan: Sequence[Action]) -> Action:
    # Use the parsed, unpadded plan. Empty and single-action cases match the paper.
    if not plan:
        return 1.0, 1.0
    if len(plan) == 1:
        return 0.0, 0.0
    return (fmean(abs(b[0] - a[0]) for a, b in zip(plan, plan[1:])),
            fmean(abs(b[1] - a[1]) for a, b in zip(plan, plan[1:])))


@dataclass(frozen=True)
class RefreshConfig:
    mode: str = "fixed"
    fixed_k: int = 8
    short_k: int = 8
    long_k: int = 24
    threshold: float = 1.0
    speed_scale: float = 1.0
    curvature_scale: float = 1.0

    def __post_init__(self) -> None:
        if self.mode not in {"every", "fixed", "adaptive"}:
            raise ValueError("Refresh mode must be every, fixed or adaptive")
        for k in (self.fixed_k, self.short_k, self.long_k):
            if isinstance(k, bool) or not isinstance(k, int) or k < 0:
                raise ValueError("Reuse budgets must be nonnegative integers")
        if self.mode == "adaptive" and self.short_k >= self.long_k:
            raise ValueError("Adaptive refresh requires short_k < long_k")
        if not all(math.isfinite(v) for v in (self.threshold, self.speed_scale, self.curvature_scale)):
            raise ValueError("Refresh parameters must be finite")
        if min(self.speed_scale, self.curvature_scale) < 1e-4:
            raise ValueError("Roughness scales must be at least 1e-4")

    def score(self, plan: Sequence[Action]) -> float:
        dv, dk = roughness(plan)
        return max(dv / self.speed_scale, dk / self.curvature_scale)

    def budget(self, plan: Sequence[Action]) -> int:
        if self.mode == "every":
            return 0
        if self.mode == "fixed":
            return self.fixed_k
        return self.short_k if self.score(plan) >= self.threshold else self.long_k


def calibrate_scales(validation_plans: Sequence[Sequence[Action]]) -> Action:
    """Estimate P90 scales on validation predictions only; no test data."""
    features = [roughness(plan) for plan in validation_plans]
    if not features:
        raise ValueError("Validation plans must not be empty")
    return (max(percentile([v for v, _ in features], 0.9), 1e-4),
            max(percentile([k for _, k in features], 0.9), 1e-4))
