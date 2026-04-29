import type { PoseResult } from "../types/pose";
import type { BackendStatus } from "../types/workout";

type Props = {
  poseResult: PoseResult | null;
  backendStatus: BackendStatus | null;
};

export function SessionHistory({ poseResult, backendStatus }: Props) {
  return (
    <section className="rounded-[2rem] border border-[#2A2A2A] bg-[#1A1A1A] p-5">
      <h2 className="text-lg font-bold">Session Notes</h2>
      <p className="mt-2 text-sm text-[#9A9A9A]">
        Current deploy-ready MVP keeps session state in backend memory. The next production phase should add login, database persistence, consent, and progress analytics.
      </p>
      <div className="mt-4 grid gap-3 rounded-2xl bg-[#0F0F0F] p-4 text-sm text-[#E5E2E1] md:grid-cols-3">
        <div>Latest backend status: <span className="font-bold text-[#DFFF00]">{poseResult?.status ?? "idle"}</span></div>
        <div>Camera mode: <span className="font-bold text-[#DFFF00]">{backendStatus?.camera ?? "unknown"}</span></div>
        <div>Workout mode: <span className="font-bold text-[#DFFF00]">{backendStatus?.workout ?? "unknown"}</span></div>
      </div>
    </section>
  );
}
