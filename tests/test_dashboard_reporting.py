import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.reporting.dashboard_reporting import (
    build_backtest_report_lines,
    build_backtest_report_text,
    build_generation_batch_report_lines,
    build_generation_batch_report_text,
    build_realtime_dashboard_payload,
)


def test_build_realtime_dashboard_payload_from_phase_c():
    stats_payload = {
        "total_draws": 120,
        "odd_even_distribution": {"Odd 3 : Even 3": 70, "Odd 4 : Even 2": 20},
        "high_low_distribution": {"High 3 : Low 3": 55, "High 4 : Low 2": 18},
        "sum_statistics": {"average": 138.7},
        "ac_value_distribution": {6: 20, 7: 50, 8: 30},
        "phase_c_analytics": {
            "hot_numbers": [
                {"number": 3, "count": 20, "rate_pct": 25.0},
                {"number": 11, "count": 18, "rate_pct": 22.5},
                {"number": 28, "count": 16, "rate_pct": 20.0},
            ],
            "cold_numbers": [
                {"number": 2, "count": 3, "rate_pct": 3.75},
                {"number": 41, "count": 2, "rate_pct": 2.5},
            ],
            "historical_trends": {
                "rising_numbers": [
                    {"number": 3, "recent_rate": 0.45, "delta_rate": 0.13},
                    {"number": 11, "recent_rate": 0.40, "delta_rate": 0.08},
                ]
            },
        },
    }

    payload = build_realtime_dashboard_payload(stats_payload, hot_limit=5)
    assert isinstance(payload, dict)
    assert "hot_numbers" in payload and len(payload["hot_numbers"]) >= 3
    assert payload["hot_numbers"][0]["number"] == 3
    assert payload["odd_even"]["value"] == "3 : 3"
    assert payload["high_low"]["value"] == "3 : 3"
    assert payload["sum_distribution"]["value"] == "139"
    assert float(payload["ac_value"]["value"]) > 0.0
    assert isinstance(payload["trend_series"], list) and len(payload["trend_series"]) >= 2


def test_build_backtest_report_lines_success_and_text():
    result = {
        "status": "success",
        "test_total_draws": 50,
        "metric_definition": {"precision_recall_scope": "number-level coverage"},
        "algorithm": {
            "total_cost": 250000,
            "total_prize": 310000,
            "roi": 124.0,
            "ranks": {"5th": 12},
            "metrics": {
                "hit_rate": 11.0,
                "match_3_rate": 10.0,
                "match_4_rate": 1.0,
                "match_5_rate": 0.0,
                "match_6_rate": 0.0,
                "precision": 22.3,
                "recall": 40.1,
                "f1_score": 28.7,
                "ticket_count": 250,
                "avg_unique_predictions_per_draw": 18.4,
            },
        },
        "random_baseline": {
            "total_cost": 250000,
            "total_prize": 180000,
            "roi": 72.0,
            "ranks": {"5th": 8},
            "metrics": {
                "hit_rate": 8.0,
                "match_3_rate": 7.2,
                "match_4_rate": 0.8,
                "match_5_rate": 0.0,
                "match_6_rate": 0.0,
                "precision": 16.2,
                "recall": 30.5,
                "f1_score": 21.0,
                "ticket_count": 250,
                "avg_unique_predictions_per_draw": 16.9,
            },
        },
    }

    lines = build_backtest_report_lines(result)
    report_text = build_backtest_report_text(result)
    assert isinstance(lines, list) and len(lines) > 10
    assert any("AI Algorithm Model" in line for line in lines)
    assert any("Random Baseline Comparison" in line for line in lines)
    assert "number-level coverage" in report_text


def test_build_backtest_report_lines_error():
    lines = build_backtest_report_lines({"status": "Error", "msg": "failure"})
    assert lines == ["Backtest failed: failure"]


def test_build_generation_batch_report_lines_and_text():
    batch_summary = {
        "batch_id": "batch-abc123",
        "is_fallback_batch": False,
        "session_count": 2,
        "set_count": 2,
        "algorithm_titles": ["Advanced AI Ensemble"],
        "first_timestamp": "2026-10-08 10:00:00",
        "latest_timestamp": "2026-10-08 10:01:00",
        "has_top_ranked": True,
        "score_weight_profile": {
            "probability": 0.33,
            "pattern": 0.22,
            "ai": 0.24,
            "genetic": 0.21,
            "confidence_probability": 0.44,
            "confidence_ensemble": 0.56,
        },
    }
    sessions = [
        {
            "id": 101,
            "timestamp": "2026-10-08 10:00:00",
            "algorithm_title": "Advanced AI Ensemble",
            "sets_detail": [{"set_no": 1}],
            "metadata": {
                "confidence_score": 93.2,
                "top_ranked_combinations": [{"rank": 1}],
                "leading_algorithms": ["A", "B", "C"],
            },
        },
        {
            "id": 102,
            "timestamp": "2026-10-08 10:01:00",
            "algorithm_title": "Advanced AI Ensemble",
            "sets_detail": [{"set_no": 1}],
            "metadata": {
                "confidence_score": 91.7,
                "top_ranked_combinations": [{"rank": 1}, {"rank": 2}],
                "leading_algorithms": ["A", "B"],
            },
        },
    ]

    lines = build_generation_batch_report_lines(batch_summary, sessions)
    text = build_generation_batch_report_text(batch_summary, sessions)
    assert isinstance(lines, list) and len(lines) > 10
    assert any("GENERATION BATCH EXPLAINABILITY REPORT" in line for line in lines)
    assert any("batch-abc123" in line for line in lines)
    assert "Session #101" in text
    assert "Session #102" in text
    assert "Score Weight Profile" in text
