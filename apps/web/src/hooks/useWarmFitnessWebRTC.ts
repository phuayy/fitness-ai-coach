import { useCallback, useRef, useState } from "react";
import { getIceServers } from "../services/apiClient";
import { buildSignalingUrl } from "../services/signalingClient";
import type { PoseResult } from "../types/pose";
import type { ClientSignalingMessage, ServerSignalingMessage } from "../types/signaling";
import type { BackendStatus, CameraMode, WarmConnectionState, WorkoutMode } from "../types/workout";
import { getCameraStartupErrorMessage } from "../utils/cameraErrors";
import { createIdleVideoTrack, type IdleVideoSource } from "../utils/createIdleVideoTrack";

export function useWarmFitnessWebRTC() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const videoSenderRef = useRef<RTCRtpSender | null>(null);
  const idleSourceRef = useRef<IdleVideoSource | null>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const connectPromiseRef = useRef<Promise<void> | null>(null);
  const heartbeatRef = useRef<number | null>(null);

  const [poseResult, setPoseResult] = useState<PoseResult | null>(null);
  const [backendStatus, setBackendStatus] = useState<BackendStatus | null>(null);
  const [connectionState, setConnectionState] = useState<WarmConnectionState>("idle");
  const [error, setError] = useState<string | null>(null);

  const sendJson = useCallback((message: ClientSignalingMessage) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return false;
    }
    ws.send(JSON.stringify(message));
    return true;
  }, []);

  const sendControl = useCallback((camera: CameraMode, workout: WorkoutMode) => {
    sendJson({ type: "control", camera, workout });
  }, [sendJson]);

  const revertToIdleTrack = useCallback(async () => {
    const sender = videoSenderRef.current;
    const idleSource = idleSourceRef.current;

    if (sender && idleSource) {
      await sender.replaceTrack(idleSource.track);
    }

    cameraStreamRef.current?.getTracks().forEach((track) => track.stop());
    cameraStreamRef.current = null;

    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.srcObject = null;
    }
  }, []);

  const disconnect = useCallback(async () => {
    sendControl("idle", "stopped");

    if (heartbeatRef.current !== null) {
      window.clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }

    cameraStreamRef.current?.getTracks().forEach((track) => track.stop());
    cameraStreamRef.current = null;

    idleSourceRef.current?.stop();
    idleSourceRef.current = null;

    wsRef.current?.close();
    pcRef.current?.close();

    wsRef.current = null;
    pcRef.current = null;
    videoSenderRef.current = null;
    connectPromiseRef.current = null;

    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.srcObject = null;
    }

    setPoseResult(null);
    setBackendStatus(null);
    setConnectionState("idle");
  }, [sendControl]);

  const connect = useCallback(async (sessionId: string) => {
    if (pcRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    if (connectPromiseRef.current) {
      return connectPromiseRef.current;
    }

    connectPromiseRef.current = (async () => {
      setError(null);
      setConnectionState("signaling");

      const ws = new WebSocket(buildSignalingUrl(sessionId));
      wsRef.current = ws;

      await new Promise<void>((resolve, reject) => {
        ws.onopen = () => resolve();
        ws.onerror = () => reject(new Error("Unable to connect to the backend signaling WebSocket."));
      });

      setConnectionState("connecting");

      const iceServers = await getIceServers();
      const pc = new RTCPeerConnection({
        iceServers,
        iceCandidatePoolSize: 4
      });
      pcRef.current = pc;

      pc.addEventListener("iceconnectionstatechange", () => {
        console.log("[webrtc] iceConnectionState", pc.iceConnectionState);
      });

      pc.addEventListener("connectionstatechange", () => {
        console.log("[webrtc] connectionState", pc.connectionState);
      });

      const idleSource = createIdleVideoTrack();
      idleSourceRef.current = idleSource;
      videoSenderRef.current = pc.addTrack(idleSource.track, idleSource.stream);

      pc.onicecandidate = (event) => {
        console.log(
          "[webrtc] local ICE candidate",
          event.candidate?.candidate ?? "end-of-candidates"
        );

        if (!event.candidate) return;

        sendJson({
          type: "candidate",
          candidate: event.candidate.toJSON(),
        });
      };

      pc.onconnectionstatechange = () => {
        const state = pc.connectionState;
        if (state === "failed" || state === "disconnected" || state === "closed") {
          setConnectionState(state === "closed" ? "idle" : "error");
          if (state !== "closed") {
            setError("WebRTC connection was interrupted. Please refresh or reconnect.");
          }
        }
      };

      ws.onmessage = async (event) => {
        let message: ServerSignalingMessage;
        try {
          message = JSON.parse(event.data) as ServerSignalingMessage;
        } catch {
          return;
        }

        if (message.type === "answer") {
          await pc.setRemoteDescription({ type: "answer", sdp: message.sdp });
          setConnectionState("connected-idle");
          return;
        }

        if (message.type === "candidate") {
          await pc.addIceCandidate(message.candidate);
          return;
        }

        if (message.type === "pose_result") {
          setPoseResult(message.payload);
          if (message.payload.workout_phase === "active") {
            setConnectionState("active");
          }
          return;
        }

        if (message.type === "backend_status") {
          setBackendStatus(message.payload);
          return;
        }

        if (message.type === "error") {
          setError(message.message);
          setConnectionState("error");
        }
      };

      ws.onclose = () => {
        if (pcRef.current?.connectionState !== "closed") {
          setConnectionState("error");
          setError("Backend signaling WebSocket closed. Please refresh and try again.");
        }
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      if (!pc.localDescription?.sdp) {
        throw new Error("Failed to create WebRTC offer.");
      }

      sendJson({ type: "offer", sdp: pc.localDescription.sdp });
      sendControl("idle", "stopped");

      heartbeatRef.current = window.setInterval(() => {
        sendJson({ type: "ping" });
      }, 25_000);
    })().catch(async (err) => {
      await disconnect();
      setConnectionState("error");
      setError(err instanceof Error ? err.message : "Failed to initialize WebRTC.");
      throw err;
    }).finally(() => {
      connectPromiseRef.current = null;
    });

    return connectPromiseRef.current;
  }, [disconnect, sendControl, sendJson]);

  const turnCameraOn = useCallback(async (videoElement?: HTMLVideoElement | null) => {
    setError(null);

    try {
      if (!videoSenderRef.current) {
        throw new Error("WebRTC is not ready yet. Wait for the status to become connected-idle.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 960 },
          height: { ideal: 540 },
          frameRate: { ideal: 30, max: 30 },
          facingMode: "user"
        },
        audio: false
      });

      const cameraTrack = stream.getVideoTracks()[0];
      if (!cameraTrack) {
        throw new Error("No camera video track found.");
      }

      cameraStreamRef.current?.getTracks().forEach((track) => track.stop());
      cameraStreamRef.current = stream;

      await videoSenderRef.current.replaceTrack(cameraTrack);

      const targetVideo = videoElement ?? videoRef.current;
      if (targetVideo) {
        targetVideo.srcObject = stream;
        await targetVideo.play();
      }

      sendControl("preview", "stopped");
      setConnectionState("camera-preview");
    } catch (err) {
      await revertToIdleTrack();
      sendControl("idle", "stopped");
      setConnectionState("connected-idle");
      setError(getCameraStartupErrorMessage(err));
    }
  }, [revertToIdleTrack, sendControl]);

  const turnCameraOff = useCallback(async () => {
    await revertToIdleTrack();
    sendControl("idle", "stopped");
    setPoseResult(null);
    setConnectionState("connected-idle");
    setError(null);
  }, [revertToIdleTrack, sendControl]);

  const startWorkout = useCallback(() => {
    if (!cameraStreamRef.current) {
      setError("Turn the camera on before starting the workout.");
      return;
    }

    sendControl("preview", "readiness");
    setConnectionState("readiness-check");
  }, [sendControl]);

  const stopWorkout = useCallback(() => {
    if (cameraStreamRef.current) {
      sendControl("preview", "stopped");
      setConnectionState("camera-preview");
    } else {
      sendControl("idle", "stopped");
      setConnectionState("connected-idle");
    }
  }, [sendControl]);

  const resetSet = useCallback(() => {
    sendJson({ type: "reset_set" });
    setPoseResult((prev) => prev ? { ...prev, rep_count: 0, stage: "top", rep_completed: false } : prev);
  }, [sendJson]);

  const resetRep = useCallback(() => {
    sendJson({ type: "reset_rep" });
    setPoseResult((prev) => prev ? { ...prev, stage: "top", rep_completed: false } : prev);
  }, [sendJson]);

  return {
    videoRef,
    poseResult,
    backendStatus,
    connectionState,
    error,
    connect,
    disconnect,
    turnCameraOn,
    turnCameraOff,
    startWorkout,
    stopWorkout,
    resetSet,
    resetRep
  };
}
