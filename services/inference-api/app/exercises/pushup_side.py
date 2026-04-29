from __future__ import annotations

from dataclasses import dataclass

from app.config import MIN_LANDMARK_VISIBILITY
from app.exercises.base import ExerciseAnalysis
from app.exercises.geometry import angle_3_points, avg_visibility, horizontal_drift_score
from app.session.readiness_state import ReadinessState

LEFT = {"ear": 7, "shoulder": 11, "elbow": 13, "wrist": 15, "hip": 23, "knee": 25, "ankle": 27}
RIGHT = {"ear": 8, "shoulder": 12, "elbow": 14, "wrist": 16, "hip": 24, "knee": 26, "ankle": 28}


@dataclass
class ReadinessAnalysis:
    is_ready: bool
    feedback: str
    checks: dict[str, bool]
    metrics: dict


class PushUpSideValidator:
    def __init__(self) -> None:
        self.top_angle = 145.0
        self.bottom_angle = 110.0
        self.min_body_line_angle = 150.0
        self.min_arm_to_torso_angle = 15.0
        self.max_arm_to_torso_angle = 95.0
        self.max_forearm_vertical_score = 1.25
        self.min_neck_angle = 120.0
        self.min_side_visibility = MIN_LANDMARK_VISIBILITY

        # Readiness thresholds. These are intentionally a little forgiving for webcam MVPs.
        self.min_readiness_hip_angle = 170.0
        self.max_readiness_hip_angle = 180.0
        self.max_shoulder_wrist_dx = 0.12
        self.min_locked_elbow_angle = 160.0
        self.required_readiness_indices = ["shoulder", "elbow", "wrist", "hip", "knee", "ankle"]

    def analyze(self, landmarks) -> ExerciseAnalysis:
        side = self._select_side(landmarks)
        if side is None:
            return ExerciseAnalysis("moving", False, "Move into side profile", {})

        ear = landmarks[side["ear"]]
        shoulder = landmarks[side["shoulder"]]
        elbow = landmarks[side["elbow"]]
        wrist = landmarks[side["wrist"]]
        hip = landmarks[side["hip"]]
        ankle = landmarks[side["ankle"]]

        elbow_angle = angle_3_points(shoulder, elbow, wrist)
        body_line_angle = angle_3_points(shoulder, hip, ankle)
        arm_to_torso_angle = angle_3_points(elbow, shoulder, hip)
        neck_angle = angle_3_points(ear, shoulder, hip)
        forearm_vertical_score = horizontal_drift_score(elbow, wrist)

        if elbow_angle >= self.top_angle:
            position_state = "top"
        elif elbow_angle <= self.bottom_angle:
            position_state = "bottom"
        else:
            position_state = "moving"

        is_body_straight = body_line_angle >= self.min_body_line_angle
        is_arm_angle_ok = self.min_arm_to_torso_angle <= arm_to_torso_angle <= self.max_arm_to_torso_angle
        is_forearm_vertical = forearm_vertical_score <= self.max_forearm_vertical_score
        is_neck_neutral = neck_angle >= self.min_neck_angle

        # Count validity remains body/neck focused to keep the early MVP usable.
        is_valid = is_body_straight and is_neck_neutral
        feedback = self._feedback(position_state, is_body_straight, is_arm_angle_ok, is_forearm_vertical, is_neck_neutral)

        return ExerciseAnalysis(
            position_state=position_state,
            is_valid=is_valid,
            feedback=feedback,
            metrics={
                "elbow_angle": round(elbow_angle, 1),
                "hip_angle": round(body_line_angle, 1),
                "body_line_angle": round(body_line_angle, 1),
                "arm_to_torso_angle": round(arm_to_torso_angle, 1),
                "neck_angle": round(neck_angle, 1),
                "forearm_vertical_score": round(forearm_vertical_score, 2),
            },
        )

    def check_readiness(self, landmarks, state: ReadinessState) -> ReadinessAnalysis:
        side = self._select_side(landmarks)
        if side is None:
            state.reset()
            return ReadinessAnalysis(
                is_ready=False,
                feedback="Move into a clear side plank position",
                checks=self._empty_checks(),
                metrics={"readiness_stable_frames": 0},
            )

        shoulder = landmarks[side["shoulder"]]
        elbow = landmarks[side["elbow"]]
        wrist = landmarks[side["wrist"]]
        hip = landmarks[side["hip"]]
        knee = landmarks[side["knee"]]
        ankle = landmarks[side["ankle"]]

        visible = self._required_points_visible(landmarks, side)
        hip_angle = angle_3_points(shoulder, hip, knee)
        elbow_angle = angle_3_points(shoulder, elbow, wrist)
        shoulder_wrist_dx = abs(float(shoulder.x) - float(wrist.x))

        body_line_ok = self.min_readiness_hip_angle <= hip_angle <= self.max_readiness_hip_angle
        vertical_stack_ok = shoulder_wrist_dx <= self.max_shoulder_wrist_dx
        arm_extension_ok = elbow_angle >= self.min_locked_elbow_angle

        center = ((float(shoulder.x) + float(hip.x) + float(ankle.x)) / 3, (float(shoulder.y) + float(hip.y) + float(ankle.y)) / 3)
        base_ready = visible and body_line_ok and vertical_stack_ok and arm_extension_ok
        is_ready, stable_frames = state.update(base_ready=base_ready, center=center if visible else None)
        stability_ok = stable_frames >= state.required_ready_frames

        checks = {
            "visibility": visible,
            "body_line": body_line_ok,
            "vertical_stack": vertical_stack_ok,
            "arm_extension": arm_extension_ok,
            "stability": stability_ok,
        }

        feedback = self._readiness_feedback(checks)
        if is_ready:
            feedback = "Ready. Start pushing."

        return ReadinessAnalysis(
            is_ready=is_ready,
            feedback=feedback,
            checks=checks,
            metrics={
                "elbow_angle": round(elbow_angle, 1),
                "hip_angle": round(hip_angle, 1),
                "body_line_angle": round(hip_angle, 1),
                "shoulder_wrist_dx": round(shoulder_wrist_dx, 3),
                "readiness_stable_frames": stable_frames,
            },
        )

    def _select_side(self, landmarks) -> dict | None:
        left_score = avg_visibility(landmarks, list(LEFT.values()))
        right_score = avg_visibility(landmarks, list(RIGHT.values()))
        if max(left_score, right_score) < self.min_side_visibility:
            return None
        return LEFT if left_score >= right_score else RIGHT

    def _required_points_visible(self, landmarks, side: dict[str, int]) -> bool:
        for name in self.required_readiness_indices:
            lm = landmarks[side[name]]
            visibility = float(getattr(lm, "visibility", 1.0))
            x = float(getattr(lm, "x", -1.0))
            y = float(getattr(lm, "y", -1.0))
            if visibility < self.min_side_visibility:
                return False
            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                return False
        return True

    def _empty_checks(self) -> dict[str, bool]:
        return {
            "visibility": False,
            "body_line": False,
            "vertical_stack": False,
            "arm_extension": False,
            "stability": False,
        }

    def _feedback(self, position_state, body_ok, arm_ok, forearm_ok, neck_ok) -> str:
        if not body_ok:
            return "Keep your body straight"
        if not arm_ok:
            return "Keep arms around 45 degrees"
        if not forearm_ok:
            return "Keep forearms vertical"
        if not neck_ok:
            return "Keep neck neutral"
        if position_state == "moving":
            return "Keep going"
        return "Good"

    def _readiness_feedback(self, checks: dict[str, bool]) -> str:
        if not checks["visibility"]:
            return "Move shoulder, wrist, hip, knee, and ankle fully into frame"
        if not checks["body_line"]:
            return "Straighten your body into a plank"
        if not checks["vertical_stack"]:
            return "Stack your shoulder above your wrist"
        if not checks["arm_extension"]:
            return "Lock your elbows before starting"
        if not checks["stability"]:
            return "Hold still for a moment"
        return "Ready"
