from fastapi import APIRouter, HTTPException

from app.schemas import RTCAnswer, RTCOffer
from app.webrtc.peer import FitnessPeer
from app.webrtc.peer_manager import peer_manager

router = APIRouter(prefix="/webrtc", tags=["webrtc"])

@router.post("/offer", response_model=RTCAnswer)
async def create_offer(offer: RTCOffer) -> RTCAnswer:
    if not peer_manager.can_accept_peer():
        raise HTTPException(status_code=429, detail="Maximum active peers reached")

    peer = FitnessPeer()
    peer_manager.add(peer)
    try:
        answer = await peer.handle_offer(offer.sdp, offer.type)
        return RTCAnswer(sdp=answer.sdp, type=answer.type)
    except Exception:
        await peer.close()
        peer_manager.discard(peer)
        raise
