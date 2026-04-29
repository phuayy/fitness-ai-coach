def serialize_landmarks(landmarks) -> list[dict]:
    serialized = []
    for idx, lm in enumerate(landmarks):
        visibility = getattr(lm, "visibility", None)
        presence = getattr(lm, "presence", None)
        confidence = visibility if visibility is not None else presence
        if confidence is None:
            confidence = 1.0
        serialized.append({
            "index": idx,
            "x": float(lm.x),
            "y": float(lm.y),
            "z": float(getattr(lm, "z", 0.0)),
            "visibility": float(confidence),
        })
    return serialized
