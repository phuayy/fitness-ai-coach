from app.session.rep_counter import RepCounter


def test_valid_bottom_to_top_increments():
    c = RepCounter()
    assert c.update("bottom", True, "Good") is False
    assert c.update("top", True, "Good") is True
    assert c.count == 1


def test_invalid_bottom_to_top_does_not_increment():
    c = RepCounter()
    c.update("bottom", False, "Keep your body straight")
    assert c.update("top", True, "Good") is False
    assert c.count == 0


def test_reset_set():
    c = RepCounter()
    c.count = 3
    c.stage = "bottom_valid"
    c.reset_set()
    assert c.count == 0
    assert c.stage == "top"
