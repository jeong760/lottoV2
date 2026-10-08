# -*- coding: utf-8 -*-
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from itertools import islice, combinations

from core.generation_schema import (
    build_frequency_map_from_history,
    build_generation_metadata,
    build_generation_stats,
    build_top_ranked_combinations,
    derive_score_weights_from_history,
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


def test_build_top_ranked_combinations_schema_and_limit():
    history = [[1, 8, 15, 23, 34, 42], [2, 9, 16, 24, 35, 43], [3, 10, 17, 25, 36, 44]]
    frequency_map = build_frequency_map_from_history(history, lookback=50)

    scored_candidates = [
        (99.0 - (i * 0.5), list(nums))
        for i, nums in enumerate(islice(combinations(range(1, 46), 6), 70))
    ]

    ranked = build_top_ranked_combinations(scored_candidates, limit=50, frequency_map=frequency_map)
    assert len(ranked) == 50

    required_fields = {
        "rank",
        "numbers",
        "confidence_score",
        "probability_score",
        "pattern_score",
        "ai_score",
        "genetic_score",
        "ensemble_score",
    }
    for item in ranked:
        assert required_fields.issubset(set(item.keys()))
        assert isinstance(item["numbers"], list) and len(item["numbers"]) == 6
        for score_key in ("confidence_score", "probability_score", "pattern_score", "ai_score", "genetic_score", "ensemble_score"):
            assert 0.0 <= float(item[score_key]) <= 100.0


def test_derive_score_weights_and_apply_custom_profile():
    history = [
        [1, 8, 15, 23, 34, 42],
        [2, 9, 16, 24, 35, 43],
        [3, 10, 17, 25, 36, 44],
        [4, 11, 18, 26, 37, 45],
        [5, 12, 19, 27, 38, 41],
        [6, 13, 20, 28, 39, 40],
        [7, 14, 21, 29, 30, 31],
        [1, 9, 17, 25, 33, 41],
        [2, 10, 18, 26, 34, 42],
        [3, 11, 19, 27, 35, 43],
    ]
    derived = derive_score_weights_from_history(history, lookback=60)
    for key in ("probability", "pattern", "ai", "genetic", "confidence_probability", "confidence_ensemble"):
        assert key in derived
        assert float(derived[key]) > 0.0

    ensemble_sum = derived["probability"] + derived["pattern"] + derived["ai"] + derived["genetic"]
    confidence_sum = derived["confidence_probability"] + derived["confidence_ensemble"]
    assert abs(ensemble_sum - 1.0) < 1e-9
    assert abs(confidence_sum - 1.0) < 1e-9

    scored_candidates = [
        (96.5, [1, 7, 14, 21, 32, 45]),
        (95.4, [2, 9, 16, 25, 33, 41]),
        (94.1, [3, 11, 18, 27, 34, 42]),
    ]
    ranked = build_top_ranked_combinations(
        scored_candidates,
        limit=3,
        frequency_map=build_frequency_map_from_history(history, lookback=60),
        score_weights=derived,
    )
    assert len(ranked) == 3
    assert ranked[0]["rank"] == 1
