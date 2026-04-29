from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from starlette.websockets import WebSocketDisconnect

from app.config import FRAME_PROCESS_EVERY_N, INFERENCE_FPS
from app.inference.landmark_serializer import serialize_landmarks
from app.session.workout_state import WorkoutSession

logger = logging.getLogger(__name__)


def make_pose_payload(
    *,
    session: WorkoutSession,
    status: str,
    workout_phase: str,
    feedback: str,
    landmarks: list[dict] | None = None,
    metrics: dict | None = None,
    is_valid: bool = False,
    is_ready: bool = False,
    rep_completed: bool = False,
    readiness: dict | None = None,
) -> dict:
    return {
        "type": "pose_result",
        "status": status,
        "exercise": "push_up_side",
        "workout_phase": workout_phase,
        "rep_count": session.counter.count,
        "rep_completed": rep_completed,
        "stage": session.counter.stage,
        "is_valid": is_valid,
        "is_ready": is_ready,
        "feedback": feedback,
        "landmarks": landmarks or [],
        "metrics": metrics or {},
        "readiness": readiness or {
            "visibility": False,
            "body_line": False,
            "vertical_stack": False,
            "arm_extension": False,
            "stability": False,
        },
    }


async def send_pose_result(session: WorkoutSession, payload: dict) -> None:
    if session.closed:
        return
    try:
        await session.websocket.send_text(json.dumps({"type": "pose_result", "payload": payload}))
    except WebSocketDisconnect:
        session.closed = True
    except RuntimeError:
        session.closed = True
    except Exception:
        logger.exception("Failed to send pose result")


async def consume_video(session: WorkoutSession, track: Any) -> None:
    frame_index = 0
    min_interval_seconds = 1.0 / max(INFERENCE_FPS, 1)
    last_processed_at = 0.0

    while not session.closed:
        try:
            frame = await track.recv()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.info("Video track ended for session %s: %s", session.session_id, exc)
            break

        frame_index += 1
        if frame_index % max(FRAME_PROCESS_EVERY_N, 1) != 0:
            continue

        now = time.monotonic()
        if now - last_processed_at < min_interval_seconds:
            continue
        last_processed_at = now

        session.touch()

        if session.camera_mode == "idle":
            # Placeholder stream path: intentionally no ndarray conversion and no MediaPipe inference.
            continue

        try:
            frame_bgr = frame.to_ndarray(format="bgr24")
            payload = await analyze_frame(session, frame_bgr)
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            logger.exception("Frame analysis failed")
            payload = make_pose_payload(
                session=session,
                status="error",
                workout_phase="error",
                feedback=f"Frame analysis failed: {exc}",
            )

        await send_pose_result(session, payload)


async def analyze_frame(session: WorkoutSession, frame_bgr) -> dict:
    pose_estimator = await session.get_pose_estimator()
    landmarks = pose_estimator.detect(frame_bgr)

    if landmarks is None:
        return make_pose_payload(
            session=session,
            status=pose_estimator.status,
            workout_phase=_workout_phase(session),
            feedback=_model_feedback(pose_estimator),
        )

    serialized_landmarks = serialize_landmarks(landmarks)

    if session.workout_mode == "stopped":
        preview_analysis = session.validator.analyze(landmarks)
        return make_pose_payload(
            session=session,
            status="running",
            workout_phase="preview",
            feedback="Pose preview active",
            landmarks=serialized_landmarks,
            metrics=preview_analysis.metrics,
            is_valid=preview_analysis.is_valid,
        )

    if session.workout_mode == "readiness":
        readiness = session.validator.check_readiness(landmarks, session.readiness_state)
        if readiness.is_ready:
            session.workout_mode = "active"
            session.counter.reset_rep()

        return make_pose_payload(
            session=session,
            status="running",
            workout_phase="active" if readiness.is_ready else "preparing",
            feedback=readiness.feedback,
            landmarks=serialized_landmarks,
            metrics=readiness.metrics,
            is_ready=readiness.is_ready,
            is_valid=readiness.is_ready,
            readiness=readiness.checks,
        )

    if session.workout_mode == "active":
        analysis = session.validator.analyze(landmarks)
        rep_completed = session.counter.update(
            position_state=analysis.position_state,
            is_valid=analysis.is_valid,
            feedback=analysis.feedback,
        )
        return make_pose_payload(
            session=session,
            status="running",
            workout_phase="active",
            feedback=analysis.feedback,
            landmarks=serialized_landmarks,
            metrics=analysis.metrics,
            is_valid=analysis.is_valid,
            is_ready=True,
            rep_completed=rep_completed,
            readiness={
                "visibility": True,
                "body_line": analysis.is_valid,
                "vertical_stack": True,
                "arm_extension": True,
                "stability": True,
            },
        )

    return make_pose_payload(
        session=session,
        status="running",
        workout_phase="paused",
        feedback="Workout paused",
        landmarks=serialized_landmarks,
    )


def _workout_phase(session: WorkoutSession) -> str:
    if session.camera_mode == "idle":
        return "idle"
    if session.workout_mode == "readiness":
        return "preparing"
    if session.workout_mode == "active":
        return "active"
    if session.workout_mode == "paused":
        return "paused"
    return "preview"


def _model_feedback(pose_estimator) -> str:
    if pose_estimator.status == "running":
        return "No pose detected"
    if pose_estimator.error_message:
        return pose_estimator.error_message
    return "Pose model is not running"
