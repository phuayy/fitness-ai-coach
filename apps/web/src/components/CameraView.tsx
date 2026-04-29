import type { RefObject } from "react";
import type { PoseResult } from "../types/pose";
import type { WarmConnectionState } from "../types/workout";
import { PoseOverlay } from "./PoseOverlay";

type Props = {
  videoRef: RefObject<HTMLVideoElement | null>;
  poseResult: PoseResult | null;
  connectionState: WarmConnectionState;
};

function fallbackLabel(connectionState: WarmConnectionState) {
  if (connectionState === "connected-idle") return "Camera off. WebRTC is warm.";
  if (connectionState === "signaling" || connectionState === "connecting") return "Connecting to backend...";
  if (connectionState === "camera-preview") return "Camera preview active";
  if (connectionState === "readiness-check") return "Checking starting position";
  if (connectionState === "active") return "Workout active";
  if (connectionState === "error") return "Connection error";
  return "Camera idle";
}

export function CameraView({ videoRef, poseResult, connectionState }: Props) {
  return (
    <section className="relative min-h-[300px] overflow-hidden rounded-[2rem] border border-[#2A2A2A] bg-[#0F0F0F] shadow-2xl">
      <div className="absolute left-5 top-5 z-10 max-w-[80%] rounded-full border border-[#2A2A2A] bg-black/70 px-4 py-2 text-sm font-semibold text-[#E5E2E1] backdrop-blur">
        {poseResult?.feedback ?? fallbackLabel(connectionState)}
      </div>

      <video
        ref={videoRef}
        className="aspect-video h-full w-full scale-x-[-1] object-cover"
        playsInline
        muted
        autoPlay
      />

      <div className="pointer-events-none absolute inset-0 scale-x-[-1]">
        <PoseOverlay poseResult={poseResult} videoRef={videoRef} />
      </div>
    </section>
  );
}
