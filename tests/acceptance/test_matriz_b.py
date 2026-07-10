from __future__ import annotations

from acceptance.matrices.matriz_b import check_direction, check_monotonic_sequence


def test_tm01_non_up_sequence():
    assert check_monotonic_sequence([1200, 1190, 1180, 1170], "non_up")


def test_tm03_down_sequence():
    assert check_monotonic_sequence([1200, 1180, 1160, 1140], "down")


def test_compare_direction_down():
    assert check_direction(1200.0, 1100.0, "down")


def test_compare_direction_up():
    assert check_direction(1100.0, 1200.0, "up")
