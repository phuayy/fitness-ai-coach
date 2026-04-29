from aiortc import RTCConfiguration, RTCIceServer

from app.config import (
    TURN_CREDENTIAL,
    TURN_ENABLED,
    TURN_URLS,
    TURN_USERNAME,
)


def make_aiortc_configuration() -> RTCConfiguration:
    ice_servers: list[RTCIceServer] = [
        RTCIceServer(urls="stun:stun.l.google.com:19302")
    ]

    if TURN_ENABLED and TURN_URLS and TURN_USERNAME and TURN_CREDENTIAL:
        ice_servers.append(
            RTCIceServer(
                urls=TURN_URLS,
                username=TURN_USERNAME,
                credential=TURN_CREDENTIAL,
            )
        )

    return RTCConfiguration(iceServers=ice_servers)