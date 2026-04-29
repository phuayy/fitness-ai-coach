# Fitness AI Coach — Deploy-Ready MVP

This version implements the latest architecture discussed in the chat:

- **Warm WebRTC connection:** backend connection is established once at page load using a low-FPS placeholder stream.
- **Separate camera control:** Camera On/Off only swaps the browser video track. The backend does not restart or crash when the camera is busy.
- **Preview overlay:** pose landmarks render during camera preview before workout starts.
- **Readiness gate:** Start Workout first checks whether the user is in a stable push-up starting position.
- **Rep counting after readiness:** counter starts only after readiness passes.
- **Graceful camera errors:** browser camera errors revert the UI back to the previous idle state and show a user-friendly prompt.
- **Public-test path:** WebSocket signaling, optional TURN credentials endpoint, Docker starter files, and environment variables are included.

## Architecture

```text
Browser React UI
  ├─ creates one warm WebRTC PeerConnection at page load
  ├─ sends placeholder canvas stream when camera is off
  ├─ swaps real webcam track when Camera On is clicked
  ├─ sends control messages over WebSocket
  └─ draws backend pose landmarks on a local canvas overlay

FastAPI backend
  ├─ /health
  ├─ /webrtc/ice-servers for STUN/TURN config
  ├─ /ws/webrtc/{session_id} for signaling + control + feedback
  ├─ skips inference when camera mode is idle
  ├─ runs MediaPipe only when camera preview is active
  ├─ validates push-up readiness before starting the active set
  └─ counts valid reps after bottom → top transitions
```

## Quick Start — Local Development

### 1. Backend

```bash
cd services/inference-api
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

Download a MediaPipe Pose Landmarker model and place it here:

```text
services/inference-api/models/pose_landmarker_full.task
```

Run the API:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check:

```text
http://127.0.0.1:8000/health
```

### 2. Frontend

```bash
cd apps/web
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## User Flow

1. Page loads and connects to backend immediately.
2. Backend receives a placeholder stream and stays warm but does not run pose inference.
3. User clicks **Camera On**.
4. Frontend requests the webcam. If the camera is busy, the app reverts to idle and shows an error instead of crashing the backend.
5. Frontend swaps the placeholder track with the real camera track.
6. Backend starts pose inference and sends landmarks, metrics, and feedback.
7. User clicks **Start Workout**.
8. Backend enters readiness mode:
   - Shoulder-to-ankle landmarks visible
   - Hip angle around 170°–180°
   - Shoulder and wrist vertically stacked
   - Elbow locked near full extension
   - Position stable for several frames
9. When readiness passes, backend switches to active counting mode.
10. A valid rep increments after a valid bottom position returns to top.

## Deploy Notes

For a public test deployment:

- Serve the frontend over **HTTPS**. Browser camera access requires localhost or HTTPS.
- Set `CORS_ALLOWED_ORIGINS` on the backend to your frontend domain.
- Set frontend build variables:
  - `VITE_API_HTTP_URL=https://your-api-domain`
  - `VITE_API_WS_URL=wss://your-api-domain`
- Use a TURN server for users behind restrictive NAT/firewalls.
- Keep `MAX_SESSIONS` low for the first beta because each active camera session may load a MediaPipe model.
- Add authentication, consent, rate limits, and database persistence before storing user workout history.

## Docker Starter

```bash
cp .env.example .env
# edit .env for your URLs and allowed origins

docker compose up --build
```

Local compose is a starter. For a real public deployment, put a TLS reverse proxy such as Caddy, Nginx, or a cloud load balancer in front of the containers.

## Project Layout

```text
fitness-ai-coach/
├── apps/web/                       # React + Vite frontend
│   └── src/
│       ├── components/             # Camera, controls, readiness, metrics
│       ├── hooks/                  # Warm WebRTC hook
│       ├── services/               # HTTP/WebSocket API helpers
│       ├── types/                  # Shared frontend types
│       └── utils/                  # Camera error + placeholder track helpers
├── services/inference-api/          # FastAPI + MediaPipe backend
│   ├── app/api/                    # Health, signaling, TURN config
│   ├── app/exercises/              # Push-up form/readiness logic
│   ├── app/inference/              # MediaPipe wrapper + serialization
│   ├── app/session/                # Per-user session state
│   └── app/webrtc/                 # Video consume/analyze loop
├── docker/                         # Nginx/coturn starter config
├── docs/                           # Design notes
└── docker-compose.yml
```
