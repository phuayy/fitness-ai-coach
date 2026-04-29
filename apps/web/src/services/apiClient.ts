const API_HTTP_URL = import.meta.env.VITE_API_HTTP_URL ?? import.meta.env.VITE_API_BASE_URL ?? "https://fitness-ai-coach-theta.vercel.app";
export const API_WS_URL = import.meta.env.VITE_API_WS_URL ?? "ws://fitness-ai-coach-theta.vercel.app";

export type IceServersResponse = {
  enabled: boolean;
  realm?: string;
  iceServers: RTCIceServer[];
};

export type HealthResponse = {
  status: string;
  pose_model_exists: boolean;
  pose_model_path: string;
  active_sessions: number;
  version: string;
};

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_HTTP_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

// Legacy REST offer route kept for rollback/testing. The deploy-ready path uses WebSocket signaling.
export async function postWebRTCOffer(offer: RTCSessionDescriptionInit): Promise<RTCSessionDescriptionInit> {
  const response = await fetch(`${API_HTTP_URL}/webrtc/offer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sdp: offer.sdp, type: offer.type })
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Backend rejected WebRTC offer: ${message}`);
  }

  return response.json();
}

export async function getIceServers(): Promise<RTCIceServer[]> {
  try {
    const response = await fetch(`${API_HTTP_URL}/webrtc/ice-servers`);
    if (!response.ok) {
      throw new Error(`ICE server request failed: ${response.status}`);
    }
    const data = (await response.json()) as IceServersResponse;
    return data.iceServers?.length ? data.iceServers : [{ urls: "stun:stun.l.google.com:19302" }];
  } catch {
    return [{ urls: "stun:stun.l.google.com:19302" }];
  }
}
