# WebRTC Flow

## Local Development

The frontend runs at `http://127.0.0.1:5173` and the backend runs at `http://127.0.0.1:8000`.

The browser can use camera access on localhost. In production, serve the app over HTTPS.

## DataChannel Actions

The frontend can send:

```json
{ "action": "reset_set" }
{ "action": "reset_rep" }
```

The backend replies with updated pose/session states during frame processing.
