import asyncio
import json
import logging
from typing import Any

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.rtcdatachannel import RTCDataChannel

from app.config import FRAME_PROCESS_EVERY_N
from app.exercises.pushup_side import PushUpSideValidator
from app.inference.landmark_serializer import serialize_landmarks
from app.inference.pose_estimator import PoseEstimator
from app.session.rep_counter import RepCounter
from app.webrtc.peer_manager import peer_manager

logger = logging.getLogger(__name__)

class FitnessPeer:
    def __init__(self) -> None:
        self.pc = RTCPeerConnection()
        self.data_channel: RTCDataChannel | None = None
        self.pose_estimator = PoseEstimator()
        self.validator = PushUpSideValidator()
        self.counter = RepCounter()
        self._closed = False
        self._frame_index = 0
        self._tasks: set[asyncio.Task] = set()
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            logger.info("Peer connection state: %s", self.pc.connectionState)
            if self.pc.connectionState in {"failed", "closed", "disconnected"}:
                await self.close()
                peer_manager.discard(self)

        @self.pc.on("datachannel")
        def on_datachannel(channel: RTCDataChannel) -> None:
            logger.info("Data channel received: %s", channel.label)
            self.data_channel = channel
            self._configure_data_channel(channel)

        @self.pc.on("track")
        def on_track(track) -> None:
            logger.info("Track received: %s", track.kind)
            if track.kind == "video":
                task = asyncio.create_task(self._consume_video(track))
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)

    def _configure_data_channel(self, channel: RTCDataChannel) -> None:
        @channel.on("open")
        def on_open() -> None:
            logger.info("Data channel open")
            self._send_json({
                "type": "pose_result",
                "status": self.pose_estimator.status,
                "exercise": "push_up_side",
                "rep_count": self.counter.count,
                "rep_completed": False,
                "stage": self.counter.stage,
                "is_valid": False,
                "feedback": self._model_feedback(),
                "landmarks": [],
                "metrics": {},
            })

        @channel.on("message")
        def on_message(message: Any) -> None:
            try:
                payload = json.loads(message) if isinstance(message, str) else {}
            except json.JSONDecodeError:
                return
            action = payload.get("action")
            if action == "reset_set":
                self.counter.reset_set()
            elif action == "reset_rep":
                self.counter.reset_rep()

    async def handle_offer(self, sdp: str, offer_type: str) -> RTCSessionDescription:
        offer = RTCSessionDescription(sdp=sdp, type=offer_type)
        await self.pc.setRemoteDescription(offer)
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        return self.pc.localDescription

    async def _consume_video(self, track) -> None:
        while not self._closed:
            try:
                frame = await track.recv()
            except Exception as exc:
                logger.info("Video track ended: %s", exc)
                break

            self._frame_index += 1
            if self._frame_index % FRAME_PROCESS_EVERY_N != 0:
                continue

            try:
                frame_bgr = frame.to_ndarray(format="bgr24")
                result = self._analyze_frame(frame_bgr)
            except Exception as exc:
                logger.exception("Frame analysis failed")
                result = self._error_payload(f"Frame analysis failed: {exc}")
            self._send_json(result)

    def _analyze_frame(self, frame_bgr) -> dict:
        landmarks = self.pose_estimator.detect(frame_bgr)
        if landmarks is None:
            return {
                "type": "pose_result",
                "status": self.pose_estimator.status,
                "exercise": "push_up_side",
                "rep_count": self.counter.count,
                "rep_completed": False,
                "stage": self.counter.stage,
                "is_valid": False,
                "feedback": self._model_feedback(),
                "landmarks": [],
                "metrics": {},
            }

        analysis = self.validator.analyze(landmarks)
        rep_completed = self.counter.update(
            position_state=analysis.position_state,
            is_valid=analysis.is_valid,
            feedback=analysis.feedback,
        )
        return {
            "type": "pose_result",
            "status": "running",
            "exercise": "push_up_side",
            "rep_count": self.counter.count,
            "rep_completed": rep_completed,
            "stage": self.counter.stage,
            "is_valid": analysis.is_valid,
            "feedback": analysis.feedback,
            "landmarks": serialize_landmarks(landmarks),
            "metrics": analysis.metrics,
        }

    def _model_feedback(self) -> str:
        if self.pose_estimator.status == "running":
            return "No pose detected"
        if self.pose_estimator.error_message:
            return self.pose_estimator.error_message
        return "Pose model is not running"

    def _error_payload(self, message: str) -> dict:
        return {
            "type": "pose_result",
            "status": "error",
            "exercise": "push_up_side",
            "rep_count": self.counter.count,
            "rep_completed": False,
            "stage": self.counter.stage,
            "is_valid": False,
            "feedback": message,
            "landmarks": [],
            "metrics": {},
        }

    def _send_json(self, payload: dict) -> None:
        if self.data_channel and self.data_channel.readyState == "open":
            try:
                self.data_channel.send(json.dumps(payload))
            except Exception:
                logger.exception("Failed to send data channel message")

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for task in list(self._tasks):
            task.cancel()
        self.pose_estimator.close()
        await self.pc.close()
