import type { PoseResult } from "./pose";
import type { BackendStatus, CameraMode, WorkoutMode } from "./workout";

export type ClientSignalingMessage =
  | { type: "offer"; sdp: string }
  | { type: "candidate"; candidate: RTCIceCandidateInit }
  | { type: "control"; camera: CameraMode; workout: WorkoutMode }
  | { type: "reset_set" }
  | { type: "reset_rep" }
  | { type: "ping" };

export type ServerSignalingMessage =
  | { type: "answer"; sdp: string }
  | { type: "candidate"; candidate: RTCIceCandidateInit }
  | { type: "pose_result"; payload: PoseResult }
  | { type: "backend_status"; payload: BackendStatus }
  | { type: "error"; message: string }
  | { type: "pong" };
