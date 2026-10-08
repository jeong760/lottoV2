# -*- coding: utf-8 -*-
"""Shared quality gate utilities for lotto candidate validation."""
from __future__ import annotations

from typing import Optional, Sequence

from config import SUM_MIN, SUM_MAX


def calculate_ac_value(numbers: Sequence[int]) -> int:
    try:
        diffs = set()
        valid = [int(n) for n in numbers]
        n = len(valid)
        for i in range(n):
            for j in range(i + 1, n):
                diffs.add(abs(valid[i] - valid[j]))
        return max(0, len(diffs) - (n - 1))
    except Exception:
        return 0


def _max_consecutive_run(numbers: Sequence[int]) -> int:
    if not numbers:
        return 0

    sorted_numbers = sorted(int(n) for n in numbers)
    streak = 1
    max_streak = 1
    for idx in range(len(sorted_numbers) - 1):
        if sorted_numbers[idx + 1] == sorted_numbers[idx] + 1:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 1
    return max_streak


def passes_quality_gate(
    numbers: Sequence[int],
    latest_draw_numbers: Optional[Sequence[int]] = None,
    *,
    strict: bool = True,
    sum_min: int = SUM_MIN,
    sum_max: int = SUM_MAX,
    high_low_cutoff: int = 23,
    min_ac_value: int = 4,
    min_span: Optional[int] = 15,
    min_decades: int = 3,
    max_overlap_with_latest: Optional[int] = 3,
    max_consecutive_run: Optional[int] = None,
) -> bool:
    try:
        cleaned = sorted({int(n) for n in numbers if 1 <= int(n) <= 45})
    except Exception:
        return False

    if len(cleaned) != 6:
        return False

    if not strict:
        return True

    total_sum = sum(cleaned)
    if not (int(sum_min) <= total_sum <= int(sum_max)):
        return False

    odd_count = sum(1 for n in cleaned if n % 2 != 0)
    if odd_count in (0, 6):
        return False

    high_count = sum(1 for n in cleaned if n >= int(high_low_cutoff))
    if high_count in (0, 6):
        return False

    if calculate_ac_value(cleaned) < int(min_ac_value):
        return False

    if min_span is not None and (max(cleaned) - min(cleaned)) < int(min_span):
        return False

    decades = {(n - 1) // 10 for n in cleaned}
    if len(decades) < int(min_decades):
        return False

    if max_consecutive_run is not None:
        if _max_consecutive_run(cleaned) > int(max_consecutive_run):
            return False

    if latest_draw_numbers is not None and max_overlap_with_latest is not None:
        latest_cleaned = {int(n) for n in latest_draw_numbers if 1 <= int(n) <= 45}
        if latest_cleaned and len(set(cleaned).intersection(latest_cleaned)) > int(max_overlap_with_latest):
            return False

    return True
