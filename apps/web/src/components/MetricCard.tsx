type Props = {
  label: string;
  value?: number | string;
  suffix?: string;
};

export function MetricCard({ label, value, suffix = "" }: Props) {
  return (
    <div className="rounded-3xl border border-[#2A2A2A] bg-[#1A1A1A] p-4">
      <p className="text-sm text-[#9A9A9A]">{label}</p>
      <p className="mt-2 text-2xl font-bold text-[#E5E2E1]">
        {value ?? "--"}{value !== undefined && suffix}
      </p>
    </div>
  );
}
