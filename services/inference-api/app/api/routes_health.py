from fastapi import APIRouter

from app.config import APP_VERSION, POSE_MODEL_PATH
from app.session.session_manager import session_manager

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": APP_VERSION,
        "pose_model_exists": POSE_MODEL_PATH.exists() and POSE_MODEL_PATH.stat().st_size > 0,
        "pose_model_path": str(POSE_MODEL_PATH),
        "active_sessions": session_manager.active_count,
    }
