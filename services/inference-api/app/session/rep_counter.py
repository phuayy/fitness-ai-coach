class RepCounter:
    def __init__(self) -> None:
        self.count = 0
        self.stage = "top"
        self.last_feedback = ""

    def update(self, position_state: str, is_valid: bool, feedback: str) -> bool:
        self.last_feedback = feedback
        rep_completed = False

        if position_state == "bottom":
            self.stage = "bottom_valid" if is_valid else "bottom_invalid"
            return False

        if position_state == "top":
            if self.stage == "bottom_valid":
                self.count += 1
                rep_completed = True
            self.stage = "top"
            return rep_completed

        if self.stage not in {"bottom_valid", "bottom_invalid"}:
            self.stage = "moving"
        return False

    def reset_set(self) -> None:
        self.count = 0
        self.stage = "top"
        self.last_feedback = ""

    def reset_rep(self) -> None:
        self.stage = "top"
        self.last_feedback = ""
