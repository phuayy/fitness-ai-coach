import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT_DIR / "models"

APP_ENV = os.getenv("APP_ENV", "development")
APP_VERSION = os.getenv("APP_VERSION", "1.1.0")

def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]

POSE_MODEL_PATH = Path(os.getenv("POSE_MODEL_PATH", str(MODEL_DIR / "pose_landmarker_full.task")))
if not POSE_MODEL_PATH.is_absolute():
    POSE_MODEL_PATH = ROOT_DIR / POSE_MODEL_PATH

INFERENCE_FPS = int(os.getenv("INFERENCE_FPS", "15"))
FRAME_PROCESS_EVERY_N = int(os.getenv("FRAME_PROCESS_EVERY_N", "1"))
MAX_ACTIVE_PEERS = int(os.getenv("MAX_ACTIVE_PEERS", "4"))
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "10"))
SESSION_IDLE_TIMEOUT_SECONDS = int(os.getenv("SESSION_IDLE_TIMEOUT_SECONDS", "300"))

_raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
CORS_ORIGINS = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

CORS_ORIGIN_REGEX = os.getenv("CORS_ALLOWED_ORIGIN_REGEX", "").strip() or None

# More forgiving defaults for a first webcam MVP. Tighten after calibration.
MIN_LANDMARK_VISIBILITY = float(os.getenv("MIN_LANDMARK_VISIBILITY", "0.15"))

TURN_ENABLED = os.getenv("TURN_ENABLED", "false").lower() == "true"

# Metered dashboard/static credential setup
TURN_URLS = _split_csv(os.getenv("TURN_URLS", os.getenv("TURN_URL", "")))
TURN_USERNAME = os.getenv("TURN_USERNAME", "")
TURN_CREDENTIAL = os.getenv("TURN_CREDENTIAL", "")

# Keep these optional for future expiring/shared-secret setups
# TURN_SECRET = os.getenv("TURN_SECRET", "")
# TURN_REALM = os.getenv("TURN_REALM", "")
TURN_TTL_SECONDS = int(os.getenv("TURN_TTL_SECONDS", "3600"))
