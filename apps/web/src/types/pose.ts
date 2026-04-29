import type { ReadinessChecks } from "./workout";

export type PoseLandmark = {
  index: number;
  x: number;
  y: number;
  z: number;
  visibility: number;
};

export type WorkoutPhase =
  | "idle"
  | "preview"
  | "preparing"
  | "active"
  | "paused"
  | "error";

export type PoseMetrics = {
  elbow_angle?: number;
  hip_angle?: number;
  body_line_angle?: number;
  arm_to_torso_angle?: number;
  neck_angle?: number;
  forearm_vertical_score?: number;
  shoulder_wrist_dx?: number;
  readiness_stable_frames?: number;
};

export type PoseResult = {
  type: "pose_result";
  status: string;
  exercise: string;
  workout_phase: WorkoutPhase;
  rep_count: number;
  rep_completed: boolean;
  stage: string;
  is_valid: boolean;
  is_ready: boolean;
  feedback: string;
  landmarks: PoseLandmark[];
  metrics: PoseMetrics;
  readiness?: ReadinessChecks;
};

export type ConnectionState = "idle" | "connecting" | "connected" | "error";
