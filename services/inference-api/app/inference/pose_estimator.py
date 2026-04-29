from __future__ import annotations

import logging
import time

import cv2
import mediapipe as mp
import numpy as np

from app.config import POSE_MODEL_PATH

logger = logging.getLogger(__name__)


class PoseEstimator:
    def __init__(self, warmup: bool = False) -> None:
        self.status = "not_loaded"
        self.error_message = ""
        self._last_timestamp_ms = 0
        self._landmarker = None
        self._load_model()
        if warmup and self.status == "running":
            self.warmup()

    def _load_model(self) -> None:
        self.status = "loading"

        if not POSE_MODEL_PATH.exists() or POSE_MODEL_PATH.stat().st_size == 0:
            self.status = "model_missing"
            self.error_message = f"Pose model missing or empty at {POSE_MODEL_PATH}"
            logger.warning(self.error_message)
            return

        try:
            BaseOptions = mp.tasks.BaseOptions
            VisionRunningMode = mp.tasks.vision.RunningMode
            PoseLandmarker = mp.tasks.vision.PoseLandmarker
            PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions

            options = PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(POSE_MODEL_PATH)),
                running_mode=VisionRunningMode.VIDEO,
                num_poses=1,
                min_pose_detection_confidence=0.45,
                min_pose_presence_confidence=0.45,
                min_tracking_confidence=0.45,
            )
            self._landmarker = PoseLandmarker.create_from_options(options)
            self.status = "running"
            logger.info("Pose model loaded from %s", POSE_MODEL_PATH)
        except Exception as exc:  # pragma: no cover - depends on local MediaPipe installation/model file
            self.status = "error"
            self.error_message = f"Failed to load pose model: {exc}"
            logger.exception(self.error_message)

    def warmup(self) -> None:
        if self._landmarker is None:
            return
        blank = np.zeros((256, 256, 3), dtype=np.uint8)
        self.detect(blank)

    def detect(self, frame_bgr):
        if self._landmarker is None:
            return None

        try:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            timestamp_ms = int(time.time() * 1000)
            if timestamp_ms <= self._last_timestamp_ms:
                timestamp_ms = self._last_timestamp_ms + 1
            self._last_timestamp_ms = timestamp_ms

            result = self._landmarker.detect_for_video(mp_image, timestamp_ms)
            if not result.pose_landmarks:
                return None
            return result.pose_landmarks[0]
        except Exception as exc:  # pragma: no cover - runtime camera/model issue
            self.status = "error"
            self.error_message = f"Pose detection failed: {exc}"
            logger.exception(self.error_message)
            return None

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
        self.status = "closed"
