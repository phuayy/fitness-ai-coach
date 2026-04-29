import { useEffect, useRef, type RefObject } from "react";
import type { PoseResult } from "../types/pose";

const CONNECTIONS: Array<[number, number]> = [
  [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
  [11, 23], [12, 24], [23, 24], [23, 25], [25, 27], [24, 26], [26, 28]
];

const MIN_VISIBILITY = 0.15;

type Props = {
  poseResult: PoseResult | null;
  videoRef: RefObject<HTMLVideoElement | null>;
};

export function PoseOverlay({ poseResult, videoRef }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const rect = video.getBoundingClientRect();
    const width = Math.max(1, Math.floor(rect.width || video.videoWidth || 960));
    const height = Math.max(1, Math.floor(rect.height || video.videoHeight || 540));

    if (canvas.width !== width) canvas.width = width;
    if (canvas.height !== height) canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!poseResult?.landmarks?.length) return;

    const byIndex = new Map(poseResult.landmarks.map((lm) => [lm.index, lm]));
    const strokeColor = poseResult.is_ready || poseResult.is_valid ? "#DFFF00" : "#FFB4AB";

    ctx.lineWidth = 4;
    ctx.strokeStyle = strokeColor;
    ctx.fillStyle = poseResult.workout_phase === "preparing" ? "#FFD166" : "#00E5FF";

    for (const [a, b] of CONNECTIONS) {
      const la = byIndex.get(a);
      const lb = byIndex.get(b);
      if (!la || !lb || la.visibility < MIN_VISIBILITY || lb.visibility < MIN_VISIBILITY) continue;
      ctx.beginPath();
      ctx.moveTo(la.x * canvas.width, la.y * canvas.height);
      ctx.lineTo(lb.x * canvas.width, lb.y * canvas.height);
      ctx.stroke();
    }

    for (const lm of poseResult.landmarks) {
      if (lm.visibility < MIN_VISIBILITY) continue;
      ctx.beginPath();
      ctx.arc(lm.x * canvas.width, lm.y * canvas.height, 5, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [poseResult, videoRef]);

  return <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />;
}
