from fastapi import APIRouter
import logging
import os

from app.config import (
    TURN_CREDENTIAL,
    TURN_ENABLED,
    TURN_URLS,
    TURN_USERNAME,
)

router = APIRouter()
logger = logging.getLogger(__name__)

def csv_env(name: str, default: str = "") -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


TURN_ENABLED = os.getenv("TURN_ENABLED", "false").lower() in {"1", "true", "yes", "on"}

STUN_URLS = csv_env(
    "STUN_URLS",
    "stun:stun.relay.metered.ca:80,stun:stun.l.google.com:19302",
)

TURN_URLS = csv_env(
    "TURN_URLS",
    "turn:global.relay.metered.ca:80,"
    "turn:global.relay.metered.ca:80?transport=tcp,"
    "turn:global.relay.metered.ca:443,"
    "turns:global.relay.metered.ca:443?transport=tcp",
)

TURN_USERNAME = os.getenv("TURN_USERNAME", "").strip()
TURN_CREDENTIAL = os.getenv("TURN_CREDENTIAL", "").strip()

import logging
import os

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)


def csv_env(name: str, default: str = "") -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


TURN_ENABLED = os.getenv("TURN_ENABLED", "false").lower() in {"1", "true", "yes", "on"}

STUN_URLS = csv_env(
    "STUN_URLS",
    "stun:stun.relay.metered.ca:80,stun:stun.l.google.com:19302",
)

TURN_URLS = csv_env(
    "TURN_URLS",
    "turn:global.relay.metered.ca:80,"
    "turn:global.relay.metered.ca:80?transport=tcp,"
    "turn:global.relay.metered.ca:443,"
    "turns:global.relay.metered.ca:443?transport=tcp",
)

TURN_USERNAME = os.getenv("TURN_USERNAME", "").strip()
TURN_CREDENTIAL = os.getenv("TURN_CREDENTIAL", "").strip()


@router.get("/webrtc/ice-servers")
async def get_ice_servers():
    ice_servers: list[dict] = []

    for stun_url in STUN_URLS:
        ice_servers.append({"urls": stun_url})

    if TURN_ENABLED:
        if not TURN_URLS or not TURN_USERNAME or not TURN_CREDENTIAL:
            logger.warning(
                "[turn] TURN enabled but missing TURN_URLS / TURN_USERNAME / TURN_CREDENTIAL"
            )
        else:
            ice_servers.append(
                {
                    "urls": TURN_URLS,
                    "username": TURN_USERNAME,
                    "credential": TURN_CREDENTIAL,
                    "credentialType": "password",
                }
            )

    logger.info(
        "[turn] Returning ICE servers. enabled=%s stun_count=%s turn_url_count=%s has_username=%s has_credential=%s",
        TURN_ENABLED,
        len(STUN_URLS),
        len(TURN_URLS) if TURN_ENABLED else 0,
        bool(TURN_USERNAME),
        bool(TURN_CREDENTIAL),
    )

    return {
        "enabled": TURN_ENABLED,
        "iceServers": ice_servers,
    }

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