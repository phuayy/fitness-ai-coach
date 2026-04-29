from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_signaling import router as signaling_router
from app.api.routes_turn import router as turn_router
from app.api.routes_webrtc import router as legacy_webrtc_router
from app.config import APP_VERSION, CORS_ORIGINS, CORS_ORIGIN_REGEX
from app.session.session_manager import session_manager
from app.webrtc.peer_manager import peer_manager
import ctypes

app = FastAPI(title="Fitness AI Coach Inference API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(turn_router)
app.include_router(signaling_router)
app.include_router(legacy_webrtc_router)

@app.get("/")
def root():
    return {
        "service": "fitness-ai-coach-backend",
        "status": "running",
    }

@app.get("/health")
def health():
    checks = {
        "api": "ok",
        "libGLESv2": "unknown",
        "libEGL": "unknown",
        "mediapipe": "unknown",
    }

    try:
        ctypes.CDLL("libGLESv2.so.2")
        checks["libGLESv2"] = "ok"
    except Exception as exc:
        checks["libGLESv2"] = f"failed: {exc}"

    try:
        ctypes.CDLL("libEGL.so.1")
        checks["libEGL"] = "ok"
    except Exception as exc:
        checks["libEGL"] = f"failed: {exc}"

    try:
        import mediapipe as mp
        checks["mediapipe"] = "ok"
    except Exception as exc:
        checks["mediapipe"] = f"failed: {exc}"

    overall_ok = all(value == "ok" for key, value in checks.items() if key != "api")

    return {
        "status": "ok" if overall_ok else "degraded",
        "checks": checks,
    }

@app.on_event("shutdown")
async def on_shutdown() -> None:
    await session_manager.close_all()
    await peer_manager.close_all()
