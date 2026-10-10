import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.engines.statistics_engine import StatisticsEngine
from core.engines import statistics_engine as statistics_engine_module


def _build_draw_records(total: int = 90):
    rows = []
    for draw_no in range(1, total + 1):
        numbers = sorted({((draw_no + (idx * 7)) % 45) + 1 for idx in range(6)})
        if len(numbers) < 6:
            numbers = [1, 8, 15, 23, 34, 42]
        rows.append(
            {
                "draw_no": draw_no,
                "drwNo": draw_no,
                "draw": draw_no,
                "num1": numbers[0],
                "num2": numbers[1],
                "num3": numbers[2],
                "num4": numbers[3],
                "num5": numbers[4],
                "num6": numbers[5],
                "numbers": numbers,
                "bonus": ((draw_no * 3) % 45) + 1,
            }
        )
    return rows


def test_phase_c_analytics_has_required_sections():
    analytics = StatisticsEngine.build_phase_c_analytics(_build_draw_records(100), lookback_draws=80)

    required_sections = {
        "hot_numbers",
        "cold_numbers",
        "delayed_numbers",
        "overdue_numbers",
        "frequent_pairs",
        "frequent_triplets",
        "number_associations",
        "number_network",
        "historical_trends",
        "cycle_detection",
        "repeat_prediction",
        "gap_prediction",
    }
    assert required_sections.issubset(set(analytics.keys()))
    assert isinstance(analytics["hot_numbers"], list)
    assert isinstance(analytics["cold_numbers"], list)
    assert isinstance(analytics["frequent_pairs"], list)
    assert isinstance(analytics["frequent_triplets"], list)
    assert isinstance(analytics["number_associations"], dict)
    assert isinstance(analytics["number_network"], dict)
    assert isinstance(analytics["historical_trends"], dict)
    assert isinstance(analytics["repeat_prediction"], dict)
    assert isinstance(analytics["gap_prediction"], dict)


def test_comprehensive_statistics_exposes_phase_c_payload(monkeypatch):
    draws = _build_draw_records(85)
    monkeypatch.setattr(
        statistics_engine_module.LottoRepository,
        "get_all_draws",
        staticmethod(lambda: draws),
    )

    report = StatisticsEngine.get_comprehensive_statistics()
    assert report.get("total_draws") == 85
    assert "phase_c_analytics" in report
    for key in ("hot_numbers", "cold_numbers", "gap_prediction", "repeat_prediction", "number_network"):
        assert key in report
        assert key in report["phase_c_analytics"]


def test_comprehensive_statistics_uses_draw_no_for_gap_ordering(monkeypatch):
    draws = [
        {"draw_no": 100, "num1": 1, "num2": 2, "num3": 3, "num4": 4, "num5": 5, "num6": 6},
        {"draw_no": 200, "num1": 7, "num2": 8, "num3": 9, "num4": 10, "num5": 11, "num6": 12},
        {"draw_no": 201, "num1": 13, "num2": 14, "num3": 15, "num4": 16, "num5": 17, "num6": 18},
        {"draw_no": 202, "num1": 19, "num2": 20, "num3": 21, "num4": 22, "num5": 23, "num6": 24},
        {"draw_no": 203, "num1": 25, "num2": 26, "num3": 27, "num4": 28, "num5": 29, "num6": 30},
        {"draw_no": 204, "num1": 31, "num2": 32, "num3": 33, "num4": 34, "num5": 35, "num6": 36},
    ]

    monkeypatch.setattr(
        statistics_engine_module.LottoRepository,
        "get_all_draws",
        staticmethod(lambda: draws),
    )

    report = StatisticsEngine.get_comprehensive_statistics()
    periodicity = report.get("periodicity_analysis", {})
    assert periodicity[1]["current_gap"] == 104
