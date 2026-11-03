"""Synchronous planner callback with a persistent corrected action buffer."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .geometry import Action, Point, actions, blend, fill, finite, integrate, speed_bound
from .refresh import RefreshConfig


@dataclass(frozen=True)
class PolicyConfig:
    horizon: int = 6
    dt_s: float = 0.5
    alpha: float = 0.65
    beta: float = 0.65
    speed_step: float | None = 0.25

    def __post_init__(self) -> None:
        if isinstance(self.horizon, bool) or not isinstance(self.horizon, int) or self.horizon < 2:
            raise ValueError("horizon must be an integer >= 2 for a retained tail")
        if not math.isfinite(self.dt_s) or self.dt_s <= 0:
            raise ValueError("dt_s must be finite and positive")
        if not all(math.isfinite(w) and 0 <= w <= 1 for w in (self.alpha, self.beta)):
            raise ValueError("alpha and beta must be in [0, 1]")
        if self.speed_step is not None and (not math.isfinite(self.speed_step) or self.speed_step < 0):
            raise ValueError("speed_step must be nonnegative or None")


@dataclass(frozen=True)
class FrameContext:
    sequence_id: str
    speed_mps: float
    curvature_m_inv: float
    observation: object = None
    instruction: str = ""


@dataclass(frozen=True)
class StepResult:
    actions: tuple[Action, ...]
    waypoints: tuple[Point, ...]
    refreshed: bool
    reuse_age: int
    reuse_budget: int
    plan_score: float | None
    parsed_actions: int | None
    used_motion_fallback: bool


Planner = Callable[[FrameContext], Sequence[Sequence[float]]]


class FastRoverPolicy:
    """One policy per ordered stream. The callback is called only on refresh.

    The callback may wrap any VLA that emits speed/curvature actions. Ground
    truth and future motion are deliberately absent from the callback contract.
    This object is serial, not a background/asynchronous execution system.
    """

    def __init__(self, config: PolicyConfig | None = None,
                 refresh: RefreshConfig | None = None) -> None:
        self.config = config or PolicyConfig()
        self.refresh = refresh or RefreshConfig()
        self.reset()

    def reset(self) -> None:
        self._sequence: str | None = None
        self._buffer: list[Action] = []
        self._age = 0
        self._budget = 0

    def needs_refresh(self, sequence_id: str) -> bool:
        return self._sequence != sequence_id or not self._buffer or self._age >= self._budget

    def step(self, context: FrameContext, planner: Planner, *,
             force_refresh: bool | None = None) -> StepResult:
        measured = (max(0.0, finite(context.speed_mps)), finite(context.curvature_m_inv))
        if context.sequence_id != self._sequence:
            self.reset()
            self._sequence = context.sequence_id
        refresh = self.needs_refresh(context.sequence_id) if force_refresh is None else force_refresh
        if not self._buffer and not refresh:
            raise ValueError("Cannot reuse an empty buffer; refresh at each sequence boundary")
        cfg = self.config
        score = None
        parsed = None
        fallback = False
        if refresh:
            raw = actions(list(planner(context)), cfg.horizon)
            score = self.refresh.score(raw)
            budget = self.refresh.budget(raw)
            parsed, fallback = len(raw), not raw
            active = blend(fill(raw, measured, cfg.horizon), measured, cfg.alpha)
            self._budget, self._age = budget, 0
        else:
            active = fill(self._buffer, measured, cfg.horizon)
        corrected = speed_bound(blend(active, measured, cfg.beta), measured, cfg.speed_step)
        self._buffer = list(corrected[1:])
        if not refresh:
            self._age += 1
        return StepResult(tuple(corrected), tuple(integrate(corrected, cfg.dt_s)),
                          refresh, self._age, self._budget, score, parsed, fallback)
