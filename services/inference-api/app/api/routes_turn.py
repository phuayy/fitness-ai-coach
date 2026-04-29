from __future__ import annotations

import base64
import hashlib
import hmac
import time

from fastapi import APIRouter

from app.config import TURN_ENABLED, TURN_REALM, TURN_SECRET, TURN_TTL_SECONDS, TURN_URL

router = APIRouter(tags=["turn"])


@router.get("/webrtc/ice-servers")
def ice_servers() -> dict:
    """Return optional ephemeral TURN credentials.

    Local development can use public STUN only. For public testing behind NAT/firewalls,
    configure coturn with static-auth-secret and expose TURN_URL/TURN_SECRET.
    """
    if not TURN_ENABLED or not TURN_SECRET or not TURN_URL:
        return {
            "enabled": False,
            "iceServers": [{"urls": "stun:stun.l.google.com:19302"}],
        }

    expires = int(time.time()) + TURN_TTL_SECONDS
    username = f"{expires}:fitness-user"
    digest = hmac.new(TURN_SECRET.encode("utf-8"), username.encode("utf-8"), hashlib.sha1).digest()
    credential = base64.b64encode(digest).decode("utf-8")

    return {
        "enabled": True,
        "realm": TURN_REALM,
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": TURN_URL, "username": username, "credential": credential},
        ],
    }
