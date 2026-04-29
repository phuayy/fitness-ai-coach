from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Literal, Optional

from aiortc import RTCPeerConnection

CameraMode = Literal["idle", "preview"]
WorkoutMode = Literal["stopped", "readiness", "active", "paused"]


@dataclass
class WorkoutSession:
    session_id: str
    pc: Optional[RTCPeerConnection] = None
    camera_mode: CameraMode = "idle"
    workout_mode: WorkoutMode = "stopped"
    video_task: Optional[asyncio.Task] = None
    rep_count: int = 0
    last_feedback: dict = field(default_factory=dict)

    def set_control(self, camera: CameraMode, workout: WorkoutMode) -> None:
        self.camera_mode = camera
        self.workout_mode = workout

        if camera == "idle":
            self.workout_mode = "stopped"


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, WorkoutSession] = {}

    def get_or_create(self, session_id: str) -> WorkoutSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = WorkoutSession(session_id=session_id)
        return self._sessions[session_id]

    async def close(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if not session:
            return

        if session.video_task:
            session.video_task.cancel()

        if session.pc:
            await session.pc.close()


session_manager = SessionManager()