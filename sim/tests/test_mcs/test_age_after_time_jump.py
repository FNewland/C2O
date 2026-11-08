"""A reading stamped after "now" (sim time went backwards: breakpoint load, reset)
has no age, so the console shows no data instead of a live-looking value."""
from smo_mcs.server import _age, TIME_JUMP_TOL_S


def test_age_normal_and_small_jitter():
    assert _age(100.0, 90.0) == 10.0
    assert _age(100.0, 100.0 + TIME_JUMP_TOL_S / 2) == 0.0     # clock jitter: still "now"


def test_age_of_a_pre_jump_reading_is_unknown():
    assert _age(100.0, 6500.0) is None                          # breakpoint took time back ~2 h
    assert _age(100.0, None) is None
