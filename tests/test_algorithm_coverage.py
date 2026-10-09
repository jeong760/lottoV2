import os
import sys
import logging
import numpy as np

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("TestAlgorithmCoverage")

from core.algorithms import MasterAlgorithmRegistry, FUNCTION_ALGORITHM_REGISTRY
from core.algorithms.base import HistoricalContext
from core.algorithms import group_statistics, group_frequency, group_ml_ai, group_pattern, group_advanced
from core.engines.markov_transition_engine import MarkovTransitionEngine
from core.engines.monte_carlo_validator import MonteCarloValidator
from ai.ai_learning_model import LottoAILearningModel


def _build_history_sets(draw_count: int = 160):
    sets = []
    for i in range(draw_count):
        nums = sorted({((i + (j * 7)) % 45) + 1 for j in range(6)})
        if len(nums) < 6:
            nums = [1, 8, 15, 23, 34, 42]
        sets.append(nums[:6])
    return sets


def _build_history_records(draw_count: int = 160):
    records = []
    for idx, nums in enumerate(_build_history_sets(draw_count), start=1):
        records.append(
            {
                "draw_no": idx,
                "drwNo": idx,
                "num1": nums[0],
                "num2": nums[1],
                "num3": nums[2],
                "num4": nums[3],
                "num5": nums[4],
                "num6": nums[5],
            }
        )
    return records


def _validate_six_numbers(numbers):
    assert isinstance(numbers, list)
    assert len(numbers) == 6
    assert len(set(numbers)) == 6
    assert all(1 <= int(n) <= 45 for n in numbers)


def test_group_variant_counts_are_fully_implemented():
    registry = MasterAlgorithmRegistry()
    registry.initialize_all()
    names = list(registry.algorithms.keys())

    assert sum("Stat_TimeSeries_Model_" in n for n in names) == 48
    assert sum("Prob_Constraint_Model_" in n for n in names) == 49
    assert sum("Unified_ML_AI_Model_" in n for n in names) == 90
    assert sum("ComplexSystem_MetaHeuristic_" in n for n in names) == 99
    assert sum("Advanced_Quantum_Hybrid_" in n for n in names) == 149


def test_required_function_algorithms_are_registered_and_callable(monkeypatch):
    history_records = _build_history_records(120)

    monkeypatch.setattr(group_statistics.LottoRepository, "get_all_draws", lambda: history_records)
    monkeypatch.setattr(group_frequency.LottoRepository, "get_all_draws", lambda: history_records)
    monkeypatch.setattr(group_pattern.LottoRepository, "get_all_draws", lambda: history_records)
    monkeypatch.setattr(group_advanced.LottoRepository, "get_all_draws", lambda: history_records)
    monkeypatch.setattr(group_ml_ai.LottoRepository, "get_all_draws", lambda: history_records)

    monkeypatch.setattr(group_ml_ai.MLModelRepository, "load_model_state", staticmethod(lambda *args, **kwargs: None))
    monkeypatch.setattr(group_ml_ai.MLModelRepository, "save_model_state", staticmethod(lambda *args, **kwargs: True))

    required_function_ids = {
        "stat_001",
        "stat_002",
        "freq_balanced_01",
        "ml_001",
        "ml_002",
        "ml_003",
        "ml_004",
        "ml_ts_001",
        "ALG-AI-01",
        "dl_001",
        "dl_002",
        "dl_003",
        "pattern_real_01",
        "adv_custom_01",
    }

    assert required_function_ids.issubset(set(FUNCTION_ALGORITHM_REGISTRY.keys()))

    for algorithm_id in sorted(required_function_ids):
        func = FUNCTION_ALGORITHM_REGISTRY[algorithm_id]["func"]
        numbers = func()
        _validate_six_numbers(numbers)


def test_lightgbm_ranker_access_violation_fallback_and_disable(monkeypatch):
    history_records = _build_history_records(120)
    monkeypatch.setattr(group_ml_ai.LottoRepository, "get_all_draws", lambda: history_records)
    monkeypatch.setattr(group_ml_ai, "LIGHTGBM_AVAILABLE", True)
    monkeypatch.setattr(group_ml_ai, "LIGHTGBM_RUNTIME_DISABLED", False)

    fallback_numbers = [1, 7, 14, 21, 28, 35]
    monkeypatch.setattr(group_ml_ai, "generate_by_timeseries_momentum", lambda: fallback_numbers)

    fit_call_count = {"count": 0}

    class BrokenLGBM:
        def __init__(self, *args, **kwargs):
            pass

        def fit(self, X, y):
            fit_call_count["count"] += 1
            raise OSError("exception: access violation reading 0x0000000000000000")

    monkeypatch.setattr(group_ml_ai, "LGBMClassifier", BrokenLGBM, raising=False)

    first = group_ml_ai.generate_by_lightgbm_ranker()
    second = group_ml_ai.generate_by_lightgbm_ranker()

    assert first == fallback_numbers
    assert second == fallback_numbers
    assert fit_call_count["count"] == 1
    assert group_ml_ai.LIGHTGBM_RUNTIME_DISABLED is True


def test_class_variant_algorithms_generate_valid_sets():
    history_sets = _build_history_sets(140)
    context = HistoricalContext.build(history_sets)

    registry = MasterAlgorithmRegistry()
    registry.initialize_all()

    sample_markers = [
        "Stat_TimeSeries_Model_",
        "Prob_Constraint_Model_",
        "Unified_ML_AI_Model_",
        "ComplexSystem_MetaHeuristic_",
        "Advanced_Quantum_Hybrid_",
    ]

    for marker in sample_markers:
        algorithm = next((a for name, a in registry.algorithms.items() if marker in name), None)
        assert algorithm is not None, f"Missing class variant for marker: {marker}"
        outcome = algorithm.generate(context)
        _validate_six_numbers(outcome.numbers)


def test_engine_components_and_ai_training_stack_exist_and_work():
    history_sets = _build_history_sets(80)

    markov = MarkovTransitionEngine(history_sets)
    sampled = markov.sample_markov_biased_numbers(6, reference_draw=history_sets[-1])
    _validate_six_numbers(sampled)

    validator = MonteCarloValidator(history_sets)
    verdict = validator.evaluate_set_probability(history_sets[-1])
    assert isinstance(verdict, dict)
    assert "is_valid" in verdict
    assert "confidence" in verdict

    ai_model = LottoAILearningModel()
    assert hasattr(ai_model, "build_lstm_model")
    assert hasattr(ai_model, "build_gru_model")
    assert hasattr(ai_model, "train_xgboost_model")
    assert hasattr(ai_model, "_analyze_arima_trend")

    trend_val = ai_model._analyze_arima_trend(np.array([0.2, 0.4, 0.3, 0.6, 0.5], dtype=np.float64))
    assert isinstance(float(trend_val), float)

    xgb_weights = ai_model.train_xgboost_model(_build_history_records(40))
    assert isinstance(xgb_weights, dict)
    assert len(xgb_weights) == 45
