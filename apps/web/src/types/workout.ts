export type CameraMode = "idle" | "preview";
export type WorkoutMode = "stopped" | "readiness" | "active" | "paused";

export type WarmConnectionState =
  | "idle"
  | "signaling"
  | "connecting"
  | "connected-idle"
  | "camera-preview"
  | "readiness-check"
  | "active"
  | "error";

export type ReadinessChecks = {
  visibility: boolean;
  body_line: boolean;
  vertical_stack: boolean;
  arm_extension: boolean;
  stability: boolean;
};

export type BackendStatus = {
  camera: CameraMode;
  workout: WorkoutMode;
  rep_count: number;
  active_sessions?: number;
};
