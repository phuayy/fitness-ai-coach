import { useRef, useState } from "react";

type CameraMode = "idle" | "preview";
type WorkoutMode = "stopped" | "readiness" | "active" | "paused";

type BackendControlMessage = {
  type: "control";
  camera: CameraMode;
  workout: WorkoutMode;
};

function makeWsUrl(sessionId: string) {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const host =
    import.meta.env.VITE_API_WS_HOST ||
    window.location.host.replace("5173", "8000");

  return `${protocol}://${host}/ws/webrtc/${sessionId}`;
}

function createIdleVideoTrack(): MediaStreamTrack {
  const canvas = document.createElement("canvas");
  canvas.width = 640;
  canvas.height = 480;

  const ctx = canvas.getContext("2d");

  const draw = () => {
    if (!ctx) return;

    ctx.fillStyle = "#111827";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#e5e7eb";
    ctx.font = "28px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Camera Off", canvas.width / 2, canvas.height / 2 - 10);

    ctx.font = "16px sans-serif";
    ctx.fillText("Idle placeholder stream", canvas.width / 2, canvas.height / 2 + 25);
  };

  draw();

  const stream = canvas.captureStream(1);
  const track = stream.getVideoTracks()[0];
  track.contentHint = "detail";

  return track;
}

export function useWarmWebRTC() {
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const senderRef = useRef<RTCRtpSender | null>(null);
  const idleTrackRef = useRef<MediaStreamTrack | null>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);

  const [status, setStatus] = useState("idle");
  const [error, setError] = useState<string | null>(null);

  function sendControl(camera: CameraMode, workout: WorkoutMode) {
    const ws = wsRef.current;

    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    const message: BackendControlMessage = {
      type: "control",
      camera,
      workout,
    };

    ws.send(JSON.stringify(message));
  }

  async function connect(sessionId: string) {
    if (pcRef.current && wsRef.current) return;

    setStatus("connecting");
    setError(null);

    const ws = new WebSocket(makeWsUrl(sessionId));
    wsRef.current = ws;

    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => resolve();
      ws.onerror = () => reject(new Error("WebSocket connection failed"));
    });

    const pc = new RTCPeerConnection({
      iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        // Add TURN here before public beta:
        // {
        //   urls: "turn:your-turn-domain.com:3478",
        //   username: "...",
        //   credential: "..."
        // }
      ],
      iceCandidatePoolSize: 4,
    });

    pcRef.current = pc;

    idleTrackRef.current = createIdleVideoTrack();
    const idleStream = new MediaStream([idleTrackRef.current]);
    senderRef.current = pc.addTrack(idleTrackRef.current, idleStream);

    pc.onicecandidate = (event) => {
      if (!event.candidate) return;

      ws.send(
        JSON.stringify({
          type: "candidate",
          candidate: event.candidate.toJSON(),
        })
      );
    };

    pc.onconnectionstatechange = () => {
      setStatus(pc.connectionState);
    };

    ws.onmessage = async (event) => {
      const message = JSON.parse(event.data);

      if (message.type === "answer") {
        await pc.setRemoteDescription({
          type: "answer",
          sdp: message.sdp,
        });
      }

      if (message.type === "candidate" && message.candidate) {
        await pc.addIceCandidate(message.candidate);
      }

      if (message.type === "feedback") {
        window.dispatchEvent(
          new CustomEvent("fitness-feedback", {
            detail: message.payload,
          })
        );
      }
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    ws.send(
      JSON.stringify({
        type: "offer",
        sdp: offer.sdp,
      })
    );

    sendControl("idle", "stopped");
    setStatus("connected-idle");
  }

  async function turnCameraOn(videoElement?: HTMLVideoElement | null) {
    try {
      setError(null);

      if (!senderRef.current) {
        throw new Error("WebRTC is not connected yet.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30, max: 30 },
        },
        audio: false,
      });

      cameraStreamRef.current = stream;

      const cameraTrack = stream.getVideoTracks()[0];

      await senderRef.current.replaceTrack(cameraTrack);

      if (videoElement) {
        videoElement.srcObject = stream;
        await videoElement.play();
      }

      sendControl("preview", "stopped");
      setStatus("camera-preview");
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Unable to start camera. It may be busy or blocked.";

      setError(message);

      if (idleTrackRef.current && senderRef.current) {
        await senderRef.current.replaceTrack(idleTrackRef.current);
      }

      sendControl("idle", "stopped");
      setStatus("connected-idle");
    }
  }

  async function turnCameraOff() {
    if (idleTrackRef.current && senderRef.current) {
      await senderRef.current.replaceTrack(idleTrackRef.current);
    }

    cameraStreamRef.current?.getTracks().forEach((track) => track.stop());
    cameraStreamRef.current = null;

    sendControl("idle", "stopped");
    setStatus("connected-idle");
  }

  function startWorkout() {
    sendControl("preview", "readiness");
    setStatus("readiness-check");
  }

  function stopWorkout() {
    sendControl("preview", "stopped");
    setStatus("camera-preview");
  }

  async function disconnect() {
    sendControl("idle", "stopped");

    cameraStreamRef.current?.getTracks().forEach((track) => track.stop());
    idleTrackRef.current?.stop();

    wsRef.current?.close();
    pcRef.current?.close();

    wsRef.current = null;
    pcRef.current = null;
    senderRef.current = null;
    idleTrackRef.current = null;
    cameraStreamRef.current = null;

    setStatus("idle");
  }

  return {
    status,
    error,
    connect,
    turnCameraOn,
    turnCameraOff,
    startWorkout,
    stopWorkout,
    disconnect,
  };
}