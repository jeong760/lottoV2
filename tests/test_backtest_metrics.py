# -*- coding: utf-8 -*-
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.lotto_evaluator import LottoEvaluator


def _mock_draws(total: int = 30):
    draws = []
    for draw_no in range(1, total + 1):
        numbers = sorted({((draw_no + (idx * 7)) % 45) + 1 for idx in range(6)})
        if len(numbers) < 6:
            numbers = [1, 8, 15, 23, 34, 42]
        draws.append(
            {
                "draw_no": draw_no,
                "numbers": numbers[:6],
                "bonus": ((draw_no * 3) % 45) + 1,
            }
        )
    return draws


def _dummy_algorithm_engine(_train_pool, set_count: int):
    return [sorted([2, 9, 14, 25, 32, 40]) for _ in range(int(set_count))]


def test_backtest_includes_extended_metrics():
    result = LottoEvaluator.run_backtest_simulation(
        all_draws=_mock_draws(35),
        algorithm_engine=_dummy_algorithm_engine,
        start_test_draw=20,
        sets_per_draw=3,
        test_window_size=8,
    )

    assert result.get("status") == "success"
    metric_definition = result.get("metric_definition", {})
    assert isinstance(metric_definition, dict)
    assert "precision_recall_scope" in metric_definition

    for key in ("algorithm", "random_baseline"):
        section = result.get(key, {})
        metrics = section.get("metrics", {})
        assert isinstance(metrics, dict)

        required = {
            "ticket_count",
            "hit_rate",
            "match_3_rate",
            "match_4_rate",
            "match_5_rate",
            "match_6_rate",
            "precision",
            "recall",
            "f1_score",
            "avg_unique_predictions_per_draw",
            "roi",
        }
        assert required.issubset(set(metrics.keys()))

        assert metrics["ticket_count"] == 24  # 8 draws * 3 sets
        for pct_key in ("hit_rate", "match_3_rate", "match_4_rate", "match_5_rate", "match_6_rate", "precision", "recall", "f1_score"):
            assert 0.0 <= float(metrics[pct_key]) <= 100.0
        assert float(metrics["avg_unique_predictions_per_draw"]) >= 0.0
