from dataclasses import dataclass

from app.exercises.pushup_side import PushUpSideValidator
from app.session.readiness_state import ReadinessState


@dataclass
class Landmark:
    x: float
    y: float
    visibility: float = 1.0
    z: float = 0.0


def make_ready_landmarks():
    landmarks = [Landmark(0.5, 0.5, 0.0) for _ in range(33)]
    # Left side profile points.
    landmarks[11] = Landmark(0.40, 0.30)  # shoulder
    landmarks[13] = Landmark(0.40, 0.40)  # elbow
    landmarks[15] = Landmark(0.40, 0.50)  # wrist aligned with shoulder
    landmarks[23] = Landmark(0.55, 0.40)  # hip
    landmarks[25] = Landmark(0.70, 0.50)  # knee, colinear through hip
    landmarks[27] = Landmark(0.85, 0.60)  # ankle
    landmarks[7] = Landmark(0.35, 0.24)   # ear
    return landmarks


def test_readiness_requires_stability_window():
    validator = PushUpSideValidator()
    state = ReadinessState(required_ready_frames=4, center_history_window=4, max_center_jitter=0.05)
    landmarks = make_ready_landmarks()

    results = [validator.check_readiness(landmarks, state).is_ready for _ in range(7)]

    assert results[-1] is True


def test_readiness_fails_when_wrist_not_stacked_under_shoulder():
    validator = PushUpSideValidator()
    state = ReadinessState(required_ready_frames=4, center_history_window=4, max_center_jitter=0.05)
    landmarks = make_ready_landmarks()
    landmarks[15] = Landmark(0.70, 0.50)

    result = validator.check_readiness(landmarks, state)

    assert result.checks["vertical_stack"] is False
    assert result.is_ready is False
