from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from aiortc import RTCPeerConnection, RTCSessionDescription
from app.webrtc.ice_config import make_aiortc_configuration
from aiortc.sdp import candidate_from_sdp
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.config import TURN_CREDENTIAL, TURN_ENABLED, TURN_URLS, TURN_USERNAME

from app.session.session_manager import session_manager
from app.session.workout_state import WorkoutSession
from app.webrtc.video_processor import consume_video, make_pose_payload, send_pose_result
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer

logger = logging.getLogger(__name__)
router = APIRouter(tags=["signaling"])

def build_peer_connection() -> RTCPeerConnection:
    ice_servers: list[RTCIceServer] = [
        RTCIceServer(urls="stun:stun.l.google.com:19302")
    ]

    if TURN_ENABLED and TURN_URLS and TURN_USERNAME and TURN_CREDENTIAL:
        logger.info(
            "TURN enabled for backend peer connection with %d TURN URL(s)",
            len(TURN_URLS),
        )

        ice_servers.append(
            RTCIceServer(
                urls=TURN_URLS,
                username=TURN_USERNAME,
                credential=TURN_CREDENTIAL,
            )
        )
    else:
        logger.warning(
            "TURN is not fully configured for backend peer connection. "
            "TURN_ENABLED=%s, TURN_URLS=%s, TURN_USERNAME set=%s, TURN_CREDENTIAL set=%s",
            TURN_ENABLED,
            bool(TURN_URLS),
            bool(TURN_USERNAME),
            bool(TURN_CREDENTIAL),
        )

    return RTCPeerConnection(
        configuration=RTCConfiguration(iceServers=ice_servers)
    )

@router.websocket("/ws/webrtc/{session_id}")
async def webrtc_signaling(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()

    try:
        session = await session_manager.create(session_id=session_id, websocket=websocket)
    except RuntimeError as exc:
        await websocket.send_text(json.dumps({"type": "error", "message": str(exc)}))
        await websocket.close(code=1013)
        return

    try:
        await send_backend_status(session)
        await _message_loop(session)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session %s", session_id)
    finally:
        await session_manager.remove(session_id)


async def _message_loop(session: WorkoutSession) -> None:
    pending_candidates: list[dict[str, Any]] = []

    async for raw in session.websocket.iter_text():
        session.touch()
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            await send_error(session, "Malformed JSON message")
            continue

        message_type = message.get("type")

        if message_type == "offer":
            await handle_offer(session, message, pending_candidates)
            await send_backend_status(session)
            continue

        if message_type == "candidate":
            candidate = message.get("candidate")
            if not session.pc or not session.pc.remoteDescription:
                if candidate:
                    pending_candidates.append(candidate)
                continue
            await add_browser_candidate(session, candidate)
            continue

        if message_type == "control":
            camera = message.get("camera")
            workout = message.get("workout")
            if camera not in {"idle", "preview"} or workout not in {"stopped", "readiness", "active", "paused"}:
                await send_error(session, "Invalid control message")
                continue
            session.set_control(camera=camera, workout=workout)
            await send_backend_status(session)
            if camera == "idle":
                await send_pose_result(session, make_pose_payload(session=session, status="idle", workout_phase="idle", feedback="Camera off"))
            continue

        if message_type == "reset_set":
            session.reset_set()
            await send_backend_status(session)
            continue

        if message_type == "reset_rep":
            session.reset_rep()
            await send_backend_status(session)
            continue

        if message_type == "ping":
            await session.websocket.send_text(json.dumps({"type": "pong"}))
            continue

        await send_error(session, f"Unsupported message type: {message_type}")


async def handle_offer(session: WorkoutSession, message: dict[str, Any], pending_candidates: list[dict[str, Any]]) -> None:
    sdp = message.get("sdp")
    if not isinstance(sdp, str):
        await send_error(session, "Offer SDP is missing")
        return
    
    pc = build_peer_connection()
    session.pc = pc

    @pc.on("icecandidate")
    async def on_icecandidate(candidate) -> None:
        if candidate is None:
            return

        await session.websocket.send_text(json.dumps({
            "type": "candidate",
            "candidate": {
                "candidate": candidate.to_sdp(),
                "sdpMid": candidate.sdpMid,
                "sdpMLineIndex": candidate.sdpMLineIndex,
            },
        }))

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        logger.info("Session %s WebRTC state: %s", session.session_id, pc.connectionState)
        if pc.connectionState in {"failed", "closed", "disconnected"}:
            session.closed = True

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange() -> None:
        logger.info(
            "Session %s ICE state: %s",
            session.session_id,
            pc.iceConnectionState,
        )


    @pc.on("icegatheringstatechange")
    async def on_icegatheringstatechange() -> None:
        logger.info(
            "Session %s ICE gathering state: %s",
            session.session_id,
            pc.iceGatheringState,
        )

    @pc.on("track")
    def on_track(track) -> None:
        logger.info("Session %s track received: %s", session.session_id, track.kind)
        if track.kind == "video":
            session.video_task = asyncio.create_task(consume_video(session, track))

    offer = RTCSessionDescription(sdp=sdp, type="offer")
    await pc.setRemoteDescription(offer)

    for candidate in pending_candidates:
        await add_browser_candidate(session, candidate)
    pending_candidates.clear()

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    logger.info(
        "Local SDP for session %s:\n%s",
        session.session_id,
        pc.localDescription.sdp,
    )

    await session.websocket.send_text(
        json.dumps({"type": "answer", "sdp": pc.localDescription.sdp})
    )

    # Warm MediaPipe after signaling starts. This moves model-loading cost away from the Camera On click.
    asyncio.create_task(_warm_pose_model(session))


async def add_browser_candidate(session: WorkoutSession, candidate_payload: dict[str, Any] | None) -> None:
    if not candidate_payload or not session.pc:
        return

    candidate_sdp = candidate_payload.get("candidate")
    if not candidate_sdp:
        return

    try:
        raw = candidate_sdp.split(":", 1)[1] if candidate_sdp.startswith("candidate:") else candidate_sdp
        candidate = candidate_from_sdp(raw)
        candidate.sdpMid = candidate_payload.get("sdpMid")
        candidate.sdpMLineIndex = candidate_payload.get("sdpMLineIndex")
        await session.pc.addIceCandidate(candidate)
    except Exception as exc:
        logger.warning("Failed to add browser ICE candidate for session %s: %s", session.session_id, exc)


async def _warm_pose_model(session: WorkoutSession) -> None:
    try:
        await session.get_pose_estimator()
    except Exception:
        logger.exception("Pose model warmup failed for session %s", session.session_id)


async def send_backend_status(session: WorkoutSession) -> None:
    await session.websocket.send_text(json.dumps({
        "type": "backend_status",
        "payload": session.backend_status_payload(active_sessions=session_manager.active_count),
    }))


async def send_error(session: WorkoutSession, message: str) -> None:
    await session.websocket.send_text(json.dumps({"type": "error", "message": message}))
