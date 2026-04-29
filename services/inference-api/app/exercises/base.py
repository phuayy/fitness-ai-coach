from dataclasses import dataclass

@dataclass
class ExerciseAnalysis:
    position_state: str
    is_valid: bool
    feedback: str
    metrics: dict
