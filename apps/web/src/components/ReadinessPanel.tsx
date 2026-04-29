import type { PoseResult } from "../types/pose";
import type { ReadinessChecks } from "../types/workout";

type Props = {
  poseResult: PoseResult | null;
};

const LABELS: Record<keyof ReadinessChecks, string> = {
  visibility: "Shoulder-to-ankle visible",
  body_line: "Straight plank body line",
  vertical_stack: "Shoulder stacked above wrist",
  arm_extension: "Elbows locked at top",
  stability: "Stable for several frames"
};

export function ReadinessPanel({ poseResult }: Props) {
  const checks = poseResult?.readiness;
  const isReady = poseResult?.is_ready ?? false;
  const stableFrames = poseResult?.metrics.readiness_stable_frames ?? 0;

  return (
    <section className="rounded-[2rem] border border-[#2A2A2A] bg-[#1A1A1A] p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold">Starting Position Readiness</h2>
          <p className="mt-1 text-sm text-[#9A9A9A]">Counting begins only after all checks stay stable.</p>
        </div>
        <div className={isReady ? "rounded-full bg-[#DFFF00] px-3 py-1 text-xs font-black text-black" : "rounded-full bg-[#3A2A10] px-3 py-1 text-xs font-black text-[#FFD166]"}>
          {isReady ? "READY" : `STABLE ${stableFrames}`}
        </div>
      </div>

      <div className="mt-4 grid gap-2">
        {(Object.keys(LABELS) as Array<keyof ReadinessChecks>).map((key) => {
          const passed = checks?.[key] ?? false;
          return (
            <div key={key} className="flex items-center justify-between rounded-2xl bg-[#0F0F0F] px-4 py-3">
              <span className="text-sm text-[#E5E2E1]">{LABELS[key]}</span>
              <span className={passed ? "font-bold text-[#DFFF00]" : "font-bold text-[#FFB4AB]"}>
                {passed ? "Pass" : "Fix"}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
