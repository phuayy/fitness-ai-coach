import { Camera, CameraOff, Play, RotateCcw, Square, StepForward } from "lucide-react";
import type { WarmConnectionState } from "../types/workout";

type Props = {
  connectionState: WarmConnectionState;
  onCameraOn: () => void;
  onCameraOff: () => void;
  onStartWorkout: () => void;
  onStopWorkout: () => void;
  onResetSet: () => void;
  onResetRep: () => void;
};

export function ControlPanel({
  connectionState,
  onCameraOn,
  onCameraOff,
  onStartWorkout,
  onStopWorkout,
  onResetSet,
  onResetRep
}: Props) {
  const isConnecting = connectionState === "signaling" || connectionState === "connecting";
  const canUseCamera = connectionState !== "idle" && !isConnecting;
  const cameraLikelyOn = ["camera-preview", "readiness-check", "active"].includes(connectionState);

  return (
    <div className="flex flex-wrap gap-3">
      <button
        onClick={onCameraOn}
        disabled={!canUseCamera || cameraLikelyOn}
        className="inline-flex items-center gap-2 rounded-full bg-[#DFFF00] px-5 py-3 font-bold text-black disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Camera size={18} /> Camera On
      </button>

      <button
        onClick={onCameraOff}
        disabled={!cameraLikelyOn}
        className="inline-flex items-center gap-2 rounded-full border border-[#2A2A2A] bg-[#1A1A1A] px-5 py-3 font-bold text-[#E5E2E1] disabled:cursor-not-allowed disabled:opacity-40"
      >
        <CameraOff size={18} /> Camera Off
      </button>

      <button
        onClick={onStartWorkout}
        disabled={!cameraLikelyOn || connectionState === "readiness-check" || connectionState === "active"}
        className="inline-flex items-center gap-2 rounded-full bg-[#00E5FF] px-5 py-3 font-bold text-black disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Play size={18} /> Start Workout
      </button>

      <button
        onClick={onStopWorkout}
        disabled={!cameraLikelyOn}
        className="inline-flex items-center gap-2 rounded-full border border-[#2A2A2A] bg-[#1A1A1A] px-5 py-3 font-bold text-[#E5E2E1] disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Square size={18} /> Stop Set
      </button>

      <button onClick={onResetSet} className="inline-flex items-center gap-2 rounded-full border border-[#2A2A2A] bg-[#1A1A1A] px-5 py-3 font-bold text-[#E5E2E1]">
        <RotateCcw size={18} /> New Set
      </button>

      <button onClick={onResetRep} className="inline-flex items-center gap-2 rounded-full border border-[#2A2A2A] bg-[#1A1A1A] px-5 py-3 font-bold text-[#E5E2E1]">
        <StepForward size={18} /> New Rep
      </button>
    </div>
  );
}
