# Deployment Plan

## Phase 1: Local MVP

- Run FastAPI locally on port 8000.
- Run Vite locally on port 5173.
- Use public STUN only.
- Keep the MediaPipe model file under `services/inference-api/models/pose_landmarker_full.task`.

## Phase 2: Public Test Beta

- Build the frontend as static files.
- Run the backend as a containerized ASGI app.
- Serve frontend and backend through HTTPS.
- Use `wss://` for signaling.
- Configure strict `CORS_ALLOWED_ORIGINS`.
- Add a TURN server if external users report connection failures.
- Keep `MAX_SESSIONS` conservative until CPU/GPU usage is measured.

## Phase 3: Production Hardening

- Add Google login or another auth provider.
- Add consent screens before collecting fitness data.
- Persist workout sessions and aggregate metrics in a database.
- Add rate limiting per user/session/IP.
- Add structured logs, request IDs, and metrics dashboards.
- Add health/readiness probes and autoscaling.
- Consider moving pose inference to the client for lower backend compute cost, or to a GPU-backed inference service for heavier models.
