# -*- coding: utf-8 -*-
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.generation_schema import (
    build_generation_metadata,
    build_generation_stats,
    resolve_total_algorithms_active,
)


class _DummyEngine:
    def __init__(self):
        self.class_algorithm_registry = {"A": object(), "B": object()}
        self.function_algorithm_registry = {"f1": lambda: None}


class _DummyHub:
    def __init__(self):
        self.engine = _DummyEngine()


def test_resolve_total_algorithms_active_for_engine_and_hub():
    assert resolve_total_algorithms_active(_DummyEngine()) == 3
    assert resolve_total_algorithms_active(_DummyHub()) == 3
    assert resolve_total_algorithms_active(None, default=7) == 7


def test_build_generation_stats_schema():
    stats = build_generation_stats([3, 12, 24, 27, 35, 42], confidence=93.5, contributors=15)
    for key in ("sum", "odd_count", "even_count", "high_count", "low_count", "ac_value", "confidence", "contributors"):
        assert key in stats
    assert stats["sum"] == 143
    assert stats["contributors"] == 15


def test_build_generation_metadata_schema():
    metadata = build_generation_metadata(
        algorithm_id="ml_gradient",
        algorithm_title="Machine Learning Gradient Engine",
        total_algorithms_active=451,
        confidence_score=92.1,
        discarded_count=120,
        leading_algorithms=["Registry Strategy Router", "Markov Transition Engine"],
    )
    for key in ("schema_version", "algorithm_id", "algorithm_title", "total_algorithms_active", "confidence_score"):
        assert key in metadata
    assert metadata["total_algorithms_active"] == 451
    assert metadata["discarded_count"] == 120
