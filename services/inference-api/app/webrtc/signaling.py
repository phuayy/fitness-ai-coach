from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp

from app.webrtc.sessions import session_manager
from app.webrtc.video_processor import process_video_track

router = APIRouter()


def browser_candidate_to_aiortc(candidate_json: dict[str, Any]):
    """
    Browser sends:
    {
      candidate: "candidate:....",
      sdpMid: "0",
      sdpMLineIndex: 0
    }

    aiortc expects a parsed RTCIceCandidate.
    """
    if not candidate_json:
        return None

    raw_candidate = candidate_json.get("candidate")

    if not raw_candidate:
        return None

    candidate_line = raw_candidate.removeprefix("candidate:")
    candidate = candidate_from_sdp(candidate_line)

    candidate.sdpMid = candidate_json.get("sdpMid")
    candidate.sdpMLineIndex = candidate_json.get("sdpMLineIndex")

    return candidate


@router.websocket("/ws/webrtc/{session_id}")
async def webrtc_signaling(websocket: WebSocket, session_id: str):
    await websocket.accept()

    session = session_manager.get_or_create(session_id)

    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")

            if message_type == "offer":
                pc = RTCPeerConnection()
                session.pc = pc

                @pc.on("track")
                def on_track(track):
                    if track.kind == "video":
                        session.video_task = asyncio.create_task(
                            process_video_track(
                                track=track,
                                session=session,
                                websocket=websocket,
                            )
                        )

                @pc.on("connectionstatechange")
                async def on_connectionstatechange():
                    if pc.connectionState in {"failed", "closed", "disconnected"}:
                        await session_manager.close(session_id)

                offer = RTCSessionDescription(
                    sdp=message["sdp"],
                    type="offer",
                )

                await pc.setRemoteDescription(offer)

                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)

                await websocket.send_json(
                    {
                        "type": "answer",
                        "sdp": pc.localDescription.sdp,
                    }
                )

            elif message_type == "candidate":
                if session.pc:
                    candidate = browser_candidate_to_aiortc(message.get("candidate"))
                    await session.pc.addIceCandidate(candidate)

            elif message_type == "control":
                camera = message.get("camera", "idle")
                workout = message.get("workout", "stopped")

                session.set_control(camera=camera, workout=workout)

                await websocket.send_json(
                    {
                        "type": "backend_status",
                        "payload": {
                            "camera": session.camera_mode,
                            "workout": session.workout_mode,
                            "rep_count": session.rep_count,
                        },
                    }
                )

    except WebSocketDisconnect:
        await session_manager.close(session_id)

    except Exception as exc:
        await websocket.send_json(
            {
                "type": "error",
                "message": str(exc),
            }
        )
        await session_manager.close(session_id)