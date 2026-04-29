import math
from typing import Protocol

class PointLike(Protocol):
    x: float
    y: float
    z: float


def angle_3_points(a: PointLike, b: PointLike, c: PointLike) -> float:
    """Angle ABC in degrees."""
    ba = (a.x - b.x, a.y - b.y)
    bc = (c.x - b.x, c.y - b.y)
    return vector_angle_degrees(ba, bc)


def vector_angle_degrees(v1: tuple[float, float], v2: tuple[float, float]) -> float:
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = math.hypot(v1[0], v1[1])
    n2 = math.hypot(v2[0], v2[1])
    if n1 == 0 or n2 == 0:
        return 0.0
    cos_theta = max(-1.0, min(1.0, dot / (n1 * n2)))
    return math.degrees(math.acos(cos_theta))


def horizontal_drift_score(a: PointLike, b: PointLike) -> float:
    dy = abs(a.y - b.y)
    dx = abs(a.x - b.x)
    if dy == 0:
        return 999.0
    return dx / dy


def avg_visibility(landmarks, indices: list[int]) -> float:
    vals = [float(getattr(landmarks[i], "visibility", 0.0)) for i in indices]
    return sum(vals) / len(vals)
