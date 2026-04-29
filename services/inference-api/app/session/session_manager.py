from __future__ import annotations

import asyncio
import time

from starlette.websockets import WebSocket

from app.config import MAX_SESSIONS, SESSION_IDLE_TIMEOUT_SECONDS
from app.session.workout_state import WorkoutSession


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, WorkoutSession] = {}
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        return len(self._sessions)

    async def create(self, session_id: str, websocket: WebSocket) -> WorkoutSession:
        async with self._lock:
            await self._cleanup_expired_locked()
            existing = self._sessions.get(session_id)
            if existing:
                await existing.close()
                self._sessions.pop(session_id, None)

            if len(self._sessions) >= MAX_SESSIONS:
                raise RuntimeError("Server is at active session capacity. Please try again later.")

            session = WorkoutSession(session_id=session_id, websocket=websocket)
            self._sessions[session_id] = session
            return session

    async def remove(self, session_id: str) -> None:
        async with self._lock:
            session = self._sessions.pop(session_id, None)
        if session:
            await session.close()

    async def close_all(self) -> None:
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        await asyncio.gather(*(session.close() for session in sessions), return_exceptions=True)

    async def _cleanup_expired_locked(self) -> None:
        now = time.time()
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if now - session.last_seen_at > SESSION_IDLE_TIMEOUT_SECONDS
        ]
        for session_id in expired_ids:
            session = self._sessions.pop(session_id)
            await session.close()


session_manager = SessionManager()
