export type IdleVideoSource = {
  stream: MediaStream;
  track: MediaStreamTrack;
  canvas: HTMLCanvasElement;
  stop: () => void;
};

export function createIdleVideoTrack(width = 960, height = 540): IdleVideoSource {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("Unable to create placeholder canvas context.");
  }

  const draw = () => {
    ctx.fillStyle = "#0F172A";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#DFFF00";
    ctx.font = "700 42px Inter, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Camera Off", canvas.width / 2, canvas.height / 2 - 12);

    ctx.fillStyle = "#CBD5E1";
    ctx.font = "500 22px Inter, system-ui, sans-serif";
    ctx.fillText("Idle placeholder stream", canvas.width / 2, canvas.height / 2 + 32);
  };

  draw();
  const intervalId = window.setInterval(draw, 1000);

  const stream = canvas.captureStream(1);
  const track = stream.getVideoTracks()[0];

  if (!track) {
    window.clearInterval(intervalId);
    throw new Error("Unable to create placeholder video track.");
  }

  track.contentHint = "detail";

  return {
    stream,
    track,
    canvas,
    stop: () => {
      window.clearInterval(intervalId);
      stream.getTracks().forEach((streamTrack) => streamTrack.stop());
    }
  };
}
