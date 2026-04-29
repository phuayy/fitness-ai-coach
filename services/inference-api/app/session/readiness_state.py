from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field


@dataclass
class ReadinessState:
    required_ready_frames: int = 12
    center_history_window: int = 8
    max_center_jitter: float = 0.025
    ready_history: deque[bool] = field(default_factory=lambda: deque(maxlen=12))
    center_history: deque[tuple[float, float]] = field(default_factory=lambda: deque(maxlen=8))

    def __post_init__(self) -> None:
        self.ready_history = deque(maxlen=self.required_ready_frames)
        self.center_history = deque(maxlen=self.center_history_window)

    def reset(self) -> None:
        self.ready_history.clear()
        self.center_history.clear()

    def update(self, base_ready: bool, center: tuple[float, float] | None) -> tuple[bool, int]:
        if center is not None:
            self.center_history.append(center)

        stable = self._is_stable()
        ready_this_frame = base_ready and stable
        self.ready_history.append(ready_this_frame)

        stable_ready_frames = sum(1 for value in self.ready_history if value)
        is_ready = len(self.ready_history) >= self.required_ready_frames and stable_ready_frames == self.required_ready_frames
        return is_ready, stable_ready_frames

    def _is_stable(self) -> bool:
        if len(self.center_history) < min(4, self.center_history_window):
            return False

        xs = [point[0] for point in self.center_history]
        ys = [point[1] for point in self.center_history]
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        return math.hypot(dx, dy) <= self.max_center_jitter
