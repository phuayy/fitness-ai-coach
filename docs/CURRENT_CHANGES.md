# Current Changed Files

## Frontend

- `apps/web/src/App.tsx` — new page flow and warm connection lifecycle.
- `apps/web/src/hooks/useWarmFitnessWebRTC.ts` — new WebRTC/WebSocket hook with placeholder stream, track replacement, camera error guardrail, control messages, and cleanup.
- `apps/web/src/components/ControlPanel.tsx` — separate Camera On, Camera Off, Start Workout, Stop Set, New Set, and New Rep controls.
- `apps/web/src/components/CameraView.tsx` — preview video with local overlay.
- `apps/web/src/components/PoseOverlay.tsx` — draws landmarks and body connections from backend pose results.
- `apps/web/src/components/ReadinessPanel.tsx` — color-coded readiness checks.
- `apps/web/src/components/RepPanel.tsx` — rep count, phase, stage, and metrics.
- `apps/web/src/components/StatusBanner.tsx` — frontend/backend status and user-friendly error display.
- `apps/web/src/components/SessionHistory.tsx` — latest backend state.
- `apps/web/src/hooks/useVoiceFeedback.ts` — speaks counts and active/preparing feedback only.
- `apps/web/src/services/apiClient.ts` — health, legacy offer, and ICE server helpers.
- `apps/web/src/services/signalingClient.ts` — WebSocket URL builder.
- `apps/web/src/types/*.ts` — pose, signaling, and workout shared types.
- `apps/web/src/utils/cameraErrors.ts` — graceful camera startup error mapping.
- `apps/web/src/utils/createIdleVideoTrack.ts` — low-FPS placeholder canvas stream.
- `apps/web/src/utils/sessionId.ts` — browser session ID helper.

## Backend

- `services/inference-api/app/main.py` — registers health, TURN config, WebSocket signaling, and legacy REST route.
- `services/inference-api/app/config.py` — environment-driven deployment settings.
- `services/inference-api/app/api/routes_health.py` — adds app version and active session count.
- `services/inference-api/app/api/routes_turn.py` — optional ephemeral TURN credential endpoint.
- `services/inference-api/app/api/routes_signaling.py` — WebSocket signaling, control, candidate handling, reset, and heartbeat.
- `services/inference-api/app/session/workout_state.py` — per-session camera/workout state, counter, readiness state, and lazy MediaPipe loading.
- `services/inference-api/app/session/session_manager.py` — active session lifecycle and capacity guard.
- `services/inference-api/app/session/readiness_state.py` — stability window for false-start prevention.
- `services/inference-api/app/webrtc/video_processor.py` — skips inference during idle placeholder stream and analyzes only active camera frames.
- `services/inference-api/app/exercises/pushup_side.py` — readiness gate and push-up rep validity logic.
- `services/inference-api/app/inference/pose_estimator.py` — safer MediaPipe wrapper with warmup and close behavior.

## Deployment

- `.env.example` — local/production environment variables.
- `docker-compose.yml` — starter compose stack.
- `services/inference-api/Dockerfile` — backend container build.
- `apps/web/Dockerfile` — frontend static build container.
- `docker/nginx/default.conf` — SPA static hosting config.
- `docker/coturn/turnserver.conf` — TURN server starter configuration.
