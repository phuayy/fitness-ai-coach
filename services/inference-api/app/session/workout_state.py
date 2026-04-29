from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Literal

from aiortc import RTCPeerConnection
from starlette.websockets import WebSocket

from app.exercises.pushup_side import PushUpSideValidator
from app.inference.pose_estimator import PoseEstimator
from app.session.readiness_state import ReadinessState
from app.session.rep_counter import RepCounter

CameraMode = Literal["idle", "preview"]
WorkoutMode = Literal["stopped", "readiness", "active", "paused"]


@dataclass
class WorkoutSession:
    session_id: str
    websocket: WebSocket
    pc: RTCPeerConnection | None = None
    camera_mode: CameraMode = "idle"
    workout_mode: WorkoutMode = "stopped"
    counter: RepCounter = field(default_factory=RepCounter)
    validator: PushUpSideValidator = field(default_factory=PushUpSideValidator)
    readiness_state: ReadinessState = field(default_factory=ReadinessState)
    pose_estimator: PoseEstimator | None = None
    pose_estimator_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    video_task: asyncio.Task | None = None
    created_at: float = field(default_factory=time.time)
    last_seen_at: float = field(default_factory=time.time)
    closed: bool = False

    def touch(self) -> None:
        self.last_seen_at = time.time()

    async def get_pose_estimator(self) -> PoseEstimator:
        async with self.pose_estimator_lock:
            if self.pose_estimator is None or self.pose_estimator.status == "closed":
                self.pose_estimator = await asyncio.to_thread(PoseEstimator, True)
            return self.pose_estimator

    def set_control(self, camera: CameraMode, workout: WorkoutMode) -> None:
        self.camera_mode = camera
        previous_workout = self.workout_mode
        self.workout_mode = workout

        if workout == "readiness" and previous_workout != "readiness":
            self.counter.reset_set()
            self.readiness_state.reset()
        if camera == "idle":
            self.workout_mode = "stopped"
            self.readiness_state.reset()

    def reset_set(self) -> None:
        self.counter.reset_set()
        self.readiness_state.reset()

    def reset_rep(self) -> None:
        self.counter.reset_rep()

    def backend_status_payload(self, active_sessions: int | None = None) -> dict:
        payload = {
            "camera": self.camera_mode,
            "workout": self.workout_mode,
            "rep_count": self.counter.count,
        }
        if active_sessions is not None:
            payload["active_sessions"] = active_sessions
        return payload

    async def close(self) -> None:
        if self.closed:
            return
        self.closed = True

        if self.video_task:
            self.video_task.cancel()

        if self.pose_estimator:
            self.pose_estimator.close()

        if self.pc and self.pc.connectionState != "closed":
            await self.pc.close()
