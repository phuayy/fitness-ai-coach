import { useCallback, useRef, useState } from "react";
import { postWebRTCOffer } from "../services/apiClient";
import type { ConnectionState, PoseResult } from "../types/pose";

type BackendAction =
  | "start_workout"
  | "stop_workout"
  | "reset_set"
  | "reset_rep";

export function useFitnessWebRTC() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const dcRef = useRef<RTCDataChannel | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [poseResult, setPoseResult] = useState<PoseResult | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>("idle");
  const [error, setError] = useState<string | null>(null);

  const safeCleanup = useCallback(() => {
    try {
      if (dcRef.current?.readyState === "open") {
        dcRef.current.send(JSON.stringify({ action: "stop_workout" }));
      }
    } catch {
      // Ignore cleanup send errors.
    }

    try {
      dcRef.current?.close();
    } catch {
      // Ignore close errors.
    }

    try {
      pcRef.current?.getSenders().forEach((sender) => {
        try {
          sender.track?.stop();
        } catch {
          // Ignore sender track stop errors.
        }
      });

      pcRef.current?.close();
    } catch {
      // Ignore peer close errors.
    }

    try {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    } catch {
      // Ignore stream stop errors.
    }

    dcRef.current = null;
    pcRef.current = null;
    streamRef.current = null;

    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.srcObject = null;
    }

    setPoseResult(null);
    setConnectionState("idle");
  }, []);

  const sendAction = useCallback((action: BackendAction) => {
    if (dcRef.current?.readyState === "open") {
      dcRef.current.send(JSON.stringify({ action }));
    }
  }, []);

  const turnCameraOff = useCallback(() => {
    safeCleanup();
    setError(null);
  }, [safeCleanup]);

  const turnCameraOn = useCallback(async () => {
    setError(null);
    setConnectionState("connecting");

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera API is not available in this browser.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 960 },
          height: { ideal: 540 },
          frameRate: { ideal: 30 },
          facingMode: "user"
        },
        audio: false
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
      });

      pcRef.current = pc;

      pc.onconnectionstatechange = () => {
        if (
          pc.connectionState === "failed" ||
          pc.connectionState === "disconnected" ||
          pc.connectionState === "closed"
        ) {
          safeCleanup();
          setError("Workout connection was interrupted. Please turn the camera on again.");
        }
      };

      pc.oniceconnectionstatechange = () => {
        if (
          pc.iceConnectionState === "failed" ||
          pc.iceConnectionState === "disconnected" ||
          pc.iceConnectionState === "closed"
        ) {
          safeCleanup();
          setError("Camera stream connection was lost. Please turn the camera on again.");
        }
      };

      const dc = pc.createDataChannel("fitness-events");
      dcRef.current = dc;

      dc.onopen = () => {
        setConnectionState("connected");
        setError(null);
      };

      dc.onerror = () => {
        safeCleanup();
        setError("Unable to open the workout data channel. Please try again.");
      };

      dc.onclose = () => {
        if (connectionState !== "idle") {
          setConnectionState("idle");
        }
      };

      dc.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as PoseResult;
          if (payload.type === "pose_result") {
            setPoseResult(payload);
          }
        } catch {
          // Ignore malformed backend messages.
        }
      };

      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      await waitForIceGatheringComplete(pc);

      if (!pc.localDescription) {
        throw new Error("Failed to create local WebRTC offer.");
      }

      const answer = await postWebRTCOffer(pc.localDescription);
      await pc.setRemoteDescription(answer);
    } catch (err) {
      safeCleanup();
      setError(getCameraStartupErrorMessage(err));
    }
  }, [connectionState, safeCleanup]);

  const startWorkout = useCallback(() => {
    setPoseResult((prev) =>
      prev
        ? {
            ...prev,
            workout_phase: "preparing",
            feedback: "Hold the starting plank position"
          }
        : prev
    );

    sendAction("start_workout");
  }, [sendAction]);

  const stopWorkout = useCallback(() => {
    sendAction("stop_workout");
    setPoseResult((prev) =>
      prev
        ? {
            ...prev,
            workout_phase: "preview",
            feedback: "Workout stopped. Camera preview is still active."
          }
        : prev
    );
  }, [sendAction]);

  const resetSet = useCallback(() => {
    sendAction("reset_set");
    setPoseResult((prev) =>
      prev
        ? {
            ...prev,
            rep_count: 0,
            stage: "top",
            workout_phase: "preview",
            feedback: "Set reset. Hold ready position before starting."
          }
        : prev
    );
  }, [sendAction]);

  const resetRep = useCallback(() => {
    sendAction("reset_rep");
  }, [sendAction]);

  return {
    videoRef,
    poseResult,
    connectionState,
    error,
    turnCameraOn,
    turnCameraOff,
    startWorkout,
    stopWorkout,
    resetSet,
    resetRep
  };
}

function waitForIceGatheringComplete(pc: RTCPeerConnection): Promise<void> {
  if (pc.iceGatheringState === "complete") {
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    const onStateChange = () => {
      if (pc.iceGatheringState === "complete") {
        pc.removeEventListener("icegatheringstatechange", onStateChange);
        resolve();
      }
    };

    pc.addEventListener("icegatheringstatechange", onStateChange);
  });
}

function getCameraStartupErrorMessage(error: unknown): string {
  if (error instanceof DOMException) {
    switch (error.name) {
      case "NotReadableError":
      case "TrackStartError":
        return "Camera is currently busy or being used by another app. Close Zoom, Teams, OBS, browser tabs, or other camera apps, then try again.";

      case "NotAllowedError":
      case "PermissionDeniedError":
        return "Camera permission was blocked. Please allow camera access in your browser settings and try again.";

      case "NotFoundError":
      case "DevicesNotFoundError":
        return "No camera was found. Please connect a camera and try again.";

      case "OverconstrainedError":
      case "ConstraintNotSatisfiedError":
        return "Your camera does not support the requested resolution or frame rate. Try another camera or lower the camera settings.";

      case "SecurityError":
        return "Camera access is blocked because the page is not running in a secure context. Use localhost during development or HTTPS in production.";

      case "AbortError":
        return "Camera startup was interrupted. Please try again.";

      default:
        return `Camera could not be started: ${error.message}`;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Camera could not be started. Please check your camera and try again.";
}