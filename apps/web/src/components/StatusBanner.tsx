import type { BackendStatus, WarmConnectionState } from "../types/workout";

type Props = {
  connectionState: WarmConnectionState;
  backendStatus: BackendStatus | null;
  error: string | null;
};

export function StatusBanner({ connectionState, backendStatus, error }: Props) {
  if (error) {
    return (
      <div className="mt-4 rounded-2xl border border-[#FFB4AB]/40 bg-[#2A1010] p-4 text-[#FFB4AB]">
        {error}
      </div>
    );
  }

  return (
    <div className="mt-4 rounded-2xl border border-[#2A2A2A] bg-[#1A1A1A] p-4 text-sm text-[#E5E2E1]">
      <span className="font-bold text-[#DFFF00]">Frontend:</span> {connectionState}
      <span className="mx-3 text-[#555]">|</span>
      <span className="font-bold text-[#DFFF00]">Backend:</span> {backendStatus ? `${backendStatus.camera}/${backendStatus.workout}` : "waiting"}
    </div>
  );
}
