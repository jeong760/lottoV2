import os
import sys
import logging

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("TestLottoEngineRouting")

from core.algorithm_catalog import resolve_algorithm_mode_id
from core.engines.lotto_engine import LottoEngine


def _mock_history(draw_count: int = 80):
    draws = []
    for i in range(draw_count):
        draw = sorted({((i + (j * 7)) % 45) + 1 for j in range(6)})
        if len(draw) < 6:
            draw = [1, 8, 15, 23, 34, 42]
        draws.append(draw[:6])
    return draws


def test_algorithm_mode_alias_resolution():
    assert resolve_algorithm_mode_id("Machine Learning Gradient Engine") == "ml_gradient"
    assert resolve_algorithm_mode_id("Markov Chain & Monte Carlo Hybrid (Recommended)") == "advanced_markov"


def test_strategy_routing_uses_selected_persona_and_constraints(monkeypatch):
    engine = LottoEngine(historical_draws=_mock_history())

    monkeypatch.setattr(engine, "_get_persona_profile", lambda strategy_key: {"pattern": 1.0})
    monkeypatch.setattr(engine, "_passes_quality_gate", lambda raw_set, relaxed=False: True)
    monkeypatch.setattr(
        engine.monte_carlo_validator,
        "evaluate_set_probability",
        lambda candidate: {"is_valid": True, "confidence": 92.0},
    )

    strategy_calls = []

    def _fake_build_strategy_candidate_bank(strategy_key, target_size=120):
        strategy_calls.append(strategy_key)
        return [
            {
                "numbers": [1, 5, 13, 22, 29, 34],
                "source": "function:pattern_real_01",
                "source_title": "pattern_real_01",
                "strategy": strategy_key,
            },
            {
                "numbers": [1, 7, 18, 26, 33, 41],
                "source": "class:PatternAlgo",
                "source_title": "PatternAlgo",
                "strategy": strategy_key,
            },
        ]

    monkeypatch.setattr(engine, "_build_strategy_candidate_bank", _fake_build_strategy_candidate_bank)

    results = engine.generate_prediction_sets(
        set_count=2,
        fixed_numbers=[1],
        excluded_numbers=[2],
        selected_algorithm_id="historical_pattern",
    )

    assert len(results) == 2
    assert "pattern" in strategy_calls

    for result in results:
        numbers = result["numbers"]
        assert len(numbers) == 6
        assert 1 in numbers
        assert 2 not in numbers
        assert result["persona"] == "pattern"


def test_registry_bank_includes_function_and_class_algorithms():
    engine = LottoEngine(historical_draws=_mock_history())

    class DummyAlgorithm:
        def __init__(self, name, category, numbers):
            self.name = name
            self.category = category
            self._numbers = numbers

        def generate(self, context):
            return type("Outcome", (), {"numbers": self._numbers})()

    engine._strategy_candidate_cache.clear()
    engine.runtime_dependencies["scipy"] = True
    engine.function_algorithm_registry = {
        "stat_001": lambda: [3, 12, 19, 28, 34, 42],
    }
    engine.function_algorithm_titles = {"stat_001": "Stat Function"}
    engine.class_algorithm_registry = {
        "ALG-TEST": DummyAlgorithm("ALG-TEST", "CAT-01", [4, 11, 20, 27, 36, 45]),
    }

    bank = engine._build_strategy_candidate_bank("statistics", target_size=4)

    assert any(entry["source"].startswith("function:") for entry in bank)
    assert any(entry["source"].startswith("class:") for entry in bank)


def test_dependency_filtering_disables_ml_function_algorithms():
    engine = LottoEngine(historical_draws=_mock_history())

    engine._strategy_candidate_cache.clear()
    engine.runtime_dependencies["sklearn"] = False
    engine.runtime_dependencies["lightgbm"] = False
    engine.runtime_dependencies["catboost"] = False
    engine.function_algorithm_registry = {
        "ml_001": lambda: [2, 9, 14, 25, 32, 40],
        "ml_005": lambda: [3, 11, 16, 24, 37, 44],
        "ml_006": lambda: [4, 10, 17, 21, 35, 43],
    }
    engine.function_algorithm_titles = {
        "ml_001": "ML Function",
        "ml_005": "LightGBM Function",
        "ml_006": "CatBoost Function",
    }
    engine.class_algorithm_registry = {}

    bank = engine._build_strategy_candidate_bank("ml_ai", target_size=3)

    assert all(entry["source"] != "function:ml_001" for entry in bank)
    assert all(entry["source"] != "function:ml_005" for entry in bank)
    assert all(entry["source"] != "function:ml_006" for entry in bank)


def test_ml_strategy_mapping_contains_new_algorithms():
    engine = LottoEngine(historical_draws=_mock_history())
    ml_ids = engine.STRATEGY_FUNCTION_IDS["ml_ai"]
    hybrid_ids = engine.STRATEGY_FUNCTION_IDS["hybrid"]

    assert "ml_005" in ml_ids
    assert "ml_006" in ml_ids
    assert "ml_005" in hybrid_ids
    assert "ml_006" in hybrid_ids
