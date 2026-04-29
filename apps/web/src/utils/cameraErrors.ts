export function getCameraStartupErrorMessage(error: unknown): string {
  if (error instanceof DOMException) {
    switch (error.name) {
      case "NotReadableError":
      case "TrackStartError":
        return "Camera is currently busy or being used by another app. Close Zoom, Teams, OBS, browser tabs, or other camera apps, then try again.";

      case "NotAllowedError":
      case "PermissionDeniedError":
        return "Camera permission was blocked. Please allow camera access in your browser settings and try again.";

      case "NotFoundError":
      case "DevicesNotFoundError":
        return "No camera was found. Please connect a camera and try again.";

      case "OverconstrainedError":
      case "ConstraintNotSatisfiedError":
        return "Your camera does not support the requested resolution or frame rate. Try another camera or lower the camera settings.";

      case "SecurityError":
        return "Camera access is blocked because this page is not running on localhost or HTTPS.";

      case "AbortError":
        return "Camera startup was interrupted. Please try again.";

      default:
        return `Camera could not be started: ${error.message}`;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Camera could not be started. Please check your camera and try again.";
}
