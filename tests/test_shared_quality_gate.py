# -*- coding: utf-8 -*-
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.quality_gate import calculate_ac_value, passes_quality_gate


def test_quality_gate_strict_and_relaxed_behavior():
    strict_fail = [1, 2, 3, 4, 5, 6]
    assert passes_quality_gate(strict_fail, strict=True) is False
    assert passes_quality_gate(strict_fail, strict=False) is True


def test_quality_gate_worker_profile_constraints():
    latest_draw = [10, 11, 12, 13, 14, 15]
    valid = [5, 17, 22, 29, 34, 41]
    assert passes_quality_gate(
        valid,
        latest_draw_numbers=latest_draw,
        strict=True,
        min_span=None,
        min_decades=3,
        max_overlap_with_latest=2,
        max_consecutive_run=3,
    ) is True

    overlap_fail = [10, 11, 12, 29, 34, 41]
    assert passes_quality_gate(
        overlap_fail,
        latest_draw_numbers=latest_draw,
        strict=True,
        min_span=None,
        min_decades=3,
        max_overlap_with_latest=2,
        max_consecutive_run=3,
    ) is False


def test_ac_value_helper_returns_integer():
    assert isinstance(calculate_ac_value([3, 12, 24, 27, 35, 42]), int)
