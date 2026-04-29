from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_signaling import router as signaling_router
from app.api.routes_turn import router as turn_router
from app.api.routes_webrtc import router as legacy_webrtc_router
from app.config import APP_VERSION, CORS_ORIGINS
from app.session.session_manager import session_manager
from app.webrtc.peer_manager import peer_manager

app = FastAPI(title="Fitness AI Coach Inference API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(turn_router)
app.include_router(signaling_router)
app.include_router(legacy_webrtc_router)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await session_manager.close_all()
    await peer_manager.close_all()
