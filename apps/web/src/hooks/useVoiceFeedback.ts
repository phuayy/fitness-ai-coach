import { useEffect, useRef } from "react";
import type { PoseResult } from "../types/pose";

export function useVoiceFeedback(poseResult: PoseResult | null) {
  const lastRepRef = useRef(0);
  const lastWarningRef = useRef("");
  const lastWarningAtRef = useRef(0);

  useEffect(() => {
    if (!poseResult || !("speechSynthesis" in window)) return;

    if (poseResult.rep_completed && poseResult.rep_count > lastRepRef.current) {
      lastRepRef.current = poseResult.rep_count;
      speak(String(poseResult.rep_count));
      return;
    }

    const shouldSpeakFormFeedback = poseResult.workout_phase === "preparing" || poseResult.workout_phase === "active";
    if (!shouldSpeakFormFeedback) return;

    const warning = poseResult.feedback;
    const now = Date.now();
    const canSpeakWarning =
      warning &&
      warning !== "Good" &&
      warning !== "Keep going" &&
      warning !== "Pose preview active" &&
      (warning !== lastWarningRef.current || now - lastWarningAtRef.current > 3500);

    if (canSpeakWarning) {
      lastWarningRef.current = warning;
      lastWarningAtRef.current = now;
      speak(warning);
    }
  }, [poseResult]);
}

function speak(text: string) {
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.05;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}
