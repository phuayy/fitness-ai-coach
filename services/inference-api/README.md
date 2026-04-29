# Inference API

FastAPI backend that accepts WebRTC offers, receives browser video frames, runs MediaPipe Pose Landmarker, validates push-up form, and sends JSON feedback through WebRTC DataChannel.

## Run

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Place model file:

```text
models/pose_landmarker_full.task
```
