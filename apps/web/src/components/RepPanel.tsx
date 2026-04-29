import type { PoseResult } from "../types/pose";
import { MetricCard } from "./MetricCard";

type Props = { poseResult: PoseResult | null };

export function RepPanel({ poseResult }: Props) {
  const m = poseResult?.metrics ?? {};
  const phase = poseResult?.workout_phase ?? "idle";
  const valid = poseResult?.is_valid ?? false;

  return (
    <aside className="space-y-4 rounded-[2rem] border border-[#2A2A2A] bg-[#1A1A1A] p-5 shadow-2xl">
      <div className="rounded-[1.5rem] bg-[#0F0F0F] p-5 text-center">
        <p className="text-sm uppercase tracking-[0.25em] text-[#9A9A9A]">Valid reps</p>
        <p className="mt-3 text-7xl font-black text-[#DFFF00]">{poseResult?.rep_count ?? 0}</p>
      </div>

      <div className="rounded-3xl border border-[#2A2A2A] p-4">
        <p className="text-sm text-[#9A9A9A]">Form status</p>
        <p className={valid ? "mt-2 text-xl font-bold text-[#DFFF00]" : "mt-2 text-xl font-bold text-[#FFB4AB]"}>
          {poseResult?.feedback ?? "Turn on camera for pose preview"}
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2 text-sm text-[#9A9A9A]">
          <p>Phase: <span className="font-bold text-[#E5E2E1]">{phase}</span></p>
          <p>Stage: <span className="font-bold text-[#E5E2E1]">{poseResult?.stage ?? "idle"}</span></p>
          <p>Ready: <span className="font-bold text-[#E5E2E1]">{poseResult?.is_ready ? "yes" : "no"}</span></p>
          <p>Status: <span className="font-bold text-[#E5E2E1]">{poseResult?.status ?? "idle"}</span></p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="Elbow" value={m.elbow_angle} suffix="°" />
        <MetricCard label="Hip" value={m.hip_angle ?? m.body_line_angle} suffix="°" />
        <MetricCard label="Arm angle" value={m.arm_to_torso_angle} suffix="°" />
        <MetricCard label="Wrist stack" value={m.shoulder_wrist_dx} />
        <MetricCard label="Neck" value={m.neck_angle} suffix="°" />
        <MetricCard label="Stable frames" value={m.readiness_stable_frames} />
      </div>
    </aside>
  );
}
