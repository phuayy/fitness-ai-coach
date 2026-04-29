# Architecture

The app follows a split-responsibility real-time architecture:

1. React captures and renders webcam video locally.
2. React sends the camera track to FastAPI using WebRTC.
3. FastAPI receives frames through `aiortc`.
4. MediaPipe detects pose landmarks.
5. Python validates exercise form and updates rep state.
6. FastAPI sends compact JSON through a WebRTC DataChannel.
7. React draws skeleton overlay and updates the workout dashboard.

The backend does **not** return annotated video frames. This keeps bandwidth and latency lower.

## Signaling Flow

```text
React creates RTCPeerConnection
React creates DataChannel
React adds webcam video track
React creates offer
POST /webrtc/offer
FastAPI creates RTCPeerConnection
FastAPI sets remote description
FastAPI creates answer
React sets remote description
WebRTC media + DataChannel flow begins
```

## Payload Shape

```json
{
  "type": "pose_result",
  "status": "running",
  "exercise": "push_up_side",
  "rep_count": 3,
  "rep_completed": true,
  "stage": "top",
  "is_valid": true,
  "feedback": "Good",
  "landmarks": [],
  "metrics": {
    "elbow_angle": 170.1,
    "body_line_angle": 166.2,
    "arm_to_torso_angle": 47.9,
    "neck_angle": 151.5,
    "forearm_vertical_score": 0.2
  }
}
```
