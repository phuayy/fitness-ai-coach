from pydantic import BaseModel

class RTCOffer(BaseModel):
    sdp: str
    type: str

class RTCAnswer(BaseModel):
    sdp: str
    type: str
