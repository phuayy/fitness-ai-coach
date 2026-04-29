from fastapi import APIRouter

from app.config import (
    TURN_CREDENTIAL,
    TURN_ENABLED,
    TURN_URLS,
    TURN_USERNAME,
)

router = APIRouter()


@router.get("/turn")
async def get_turn_servers() -> dict:
    ice_servers: list[dict] = [
        {
            "urls": ["stun:stun.l.google.com:19302"]
        }
    ]

    if TURN_ENABLED and TURN_URLS and TURN_USERNAME and TURN_CREDENTIAL:
        ice_servers.append(
            {
                "urls": TURN_URLS,
                "username": TURN_USERNAME,
                "credential": TURN_CREDENTIAL,
            }
        )

    return {"iceServers": ice_servers}