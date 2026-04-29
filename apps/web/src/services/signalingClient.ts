import { API_WS_URL } from "./apiClient";

export function buildSignalingUrl(sessionId: string): string {
  const base = API_WS_URL.replace(/\/$/, "");
  return `${base}/ws/webrtc/${encodeURIComponent(sessionId)}`;
}
