import { useEffect, useMemo } from "react";
import { Activity } from "lucide-react";
import { Analytics } from "@vercel/analytics/react";
import { CameraView } from "./components/CameraView";
import { ControlPanel } from "./components/ControlPanel";
import { ReadinessPanel } from "./components/ReadinessPanel";
import { RepPanel } from "./components/RepPanel";
import { SessionHistory } from "./components/SessionHistory";
import { StatusBanner } from "./components/StatusBanner";
import { useWarmFitnessWebRTC } from "./hooks/useWarmFitnessWebRTC";
import { useVoiceFeedback } from "./hooks/useVoiceFeedback";
import { createSessionId } from "./utils/sessionId";

export default function App() {
  const sessionId = useMemo(() => createSessionId(), []);
  const {
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
  } = useWarmFitnessWebRTC();

  useVoiceFeedback(poseResult);

  useEffect(() => {
    connect(sessionId).catch(() => undefined);
    return () => {
      disconnect().catch(() => undefined);
    };
  }, [connect, disconnect, sessionId]);

  return (
    <>
      <main className="mx-auto min-h-screen max-w-7xl px-4 py-6 md:px-8">
        <header className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-[#2A2A2A] bg-[#1A1A1A] px-4 py-2 text-sm text-[#9A9A9A]">
              <Activity size={16} className="text-[#DFFF00]" /> Real-time AI fitness coach
            </div>
            <h1 className="mt-4 text-4xl font-black tracking-tight md:text-6xl">Push-Up Form Coach</h1>
            <p className="mt-3 max-w-3xl text-[#9A9A9A]">
              WebRTC is warmed once with an idle placeholder stream. Camera On only swaps in the real camera, Start Workout triggers readiness, and valid reps count only after readiness passes.
            </p>
          </div>
          <div className="rounded-full border border-[#2A2A2A] bg-[#1A1A1A] px-4 py-2 text-sm font-bold uppercase tracking-[0.18em] text-[#DFFF00]">
            {connectionState}
          </div>
        </header>

        <ControlPanel
          connectionState={connectionState}
          onCameraOn={() => turnCameraOn(videoRef.current)}
          onCameraOff={turnCameraOff}
          onStartWorkout={startWorkout}
          onStopWorkout={stopWorkout}
          onResetSet={resetSet}
          onResetRep={resetRep}
        />

        <StatusBanner connectionState={connectionState} backendStatus={backendStatus} error={error} />

        <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_380px]">
          <CameraView videoRef={videoRef} poseResult={poseResult} connectionState={connectionState} />
          <RepPanel poseResult={poseResult} />
        </section>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_380px]">
          <ReadinessPanel poseResult={poseResult} />
          <SessionHistory poseResult={poseResult} backendStatus={backendStatus} />
        </div>
      </main>
      <Analytics />
    </>
  );
}
