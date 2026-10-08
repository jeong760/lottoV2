# -*- coding: utf-8 -*-
"""Shared reporting helpers for dashboard visualization and backtest reporting."""
from __future__ import annotations

from typing import Any, Dict, List


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def build_realtime_dashboard_payload(stats_payload: Dict[str, Any], hot_limit: int = 5) -> Dict[str, Any]:
    """
    Normalizes comprehensive statistics payload into widget-friendly structure.
    """
    stats_payload = stats_payload if isinstance(stats_payload, dict) else {}
    phase_c = stats_payload.get("phase_c_analytics", stats_payload)
    if not isinstance(phase_c, dict):
        phase_c = {}

    total_draws = max(1, _safe_int(stats_payload.get("total_draws", 1), default=1))
    hot_source = phase_c.get("hot_numbers", [])
    cold_source = phase_c.get("cold_numbers", [])

    hot_numbers: List[Dict[str, Any]] = []
    if isinstance(hot_source, list) and hot_source:
        for row in hot_source[: max(1, int(hot_limit))]:
            if not isinstance(row, dict):
                continue
            number = _safe_int(row.get("number"), 0)
            if not (1 <= number <= 45):
                continue
            rate_pct = _safe_float(row.get("rate_pct"), 0.0)
            count = _safe_int(row.get("count"), 0)
            hot_numbers.append(
                {
                    "number": number,
                    "count": count,
                    "rate_pct": max(0.0, min(100.0, rate_pct)),
                }
            )

    if not hot_numbers:
        top_20 = stats_payload.get("top_20_numbers", [])
        if isinstance(top_20, list):
            for row in top_20[: max(1, int(hot_limit))]:
                if not isinstance(row, dict):
                    continue
                number = _safe_int(row.get("number"), 0)
                if not (1 <= number <= 45):
                    continue
                count = _safe_int(row.get("count"), 0)
                rate_pct = (float(count) / float(total_draws)) * 100.0
                hot_numbers.append(
                    {
                        "number": number,
                        "count": count,
                        "rate_pct": max(0.0, min(100.0, rate_pct)),
                    }
                )

    cold_numbers: List[Dict[str, Any]] = []
    if isinstance(cold_source, list):
        for row in cold_source[:3]:
            if not isinstance(row, dict):
                continue
            number = _safe_int(row.get("number"), 0)
            if not (1 <= number <= 45):
                continue
            cold_numbers.append(
                {
                    "number": number,
                    "count": _safe_int(row.get("count"), 0),
                    "rate_pct": max(0.0, min(100.0, _safe_float(row.get("rate_pct"), 0.0))),
                }
            )

    odd_even_dist = stats_payload.get("odd_even_distribution", {})
    odd_even_label = "3 : 3"
    odd_even_sub = "Balanced Ratio"
    if isinstance(odd_even_dist, dict) and odd_even_dist:
        dominant = max(odd_even_dist.items(), key=lambda item: _safe_int(item[1], 0))[0]
        if isinstance(dominant, str) and "Odd" in dominant and "Even" in dominant:
            try:
                left, right = dominant.replace("Odd", "").replace("Even", "").split(":")
                odd_even_label = f"{left.strip()} : {right.strip()}"
            except Exception:
                odd_even_label = dominant

    high_low_dist = stats_payload.get("high_low_distribution", {})
    high_low_label = "3 : 3"
    high_low_sub = "Balanced Ratio"
    if isinstance(high_low_dist, dict) and high_low_dist:
        dominant = max(high_low_dist.items(), key=lambda item: _safe_int(item[1], 0))[0]
        if isinstance(dominant, str) and "High" in dominant and "Low" in dominant:
            try:
                left, right = dominant.replace("High", "").replace("Low", "").split(":")
                high_low_label = f"{left.strip()} : {right.strip()}"
            except Exception:
                high_low_label = dominant

    sum_stats = stats_payload.get("sum_statistics", {})
    sum_avg = _safe_float(sum_stats.get("average", 0.0) if isinstance(sum_stats, dict) else 0.0, 0.0)
    sum_label = str(int(round(sum_avg))) if sum_avg > 0 else "-"
    sum_sub = f"(Average : {sum_avg:.1f})" if sum_avg > 0 else "(Average : -)"

    ac_distribution = stats_payload.get("ac_value_distribution", {})
    ac_label = "-"
    ac_sub = "(Average : -)"
    if isinstance(ac_distribution, dict) and ac_distribution:
        total_count = 0.0
        weighted_sum = 0.0
        for k, v in ac_distribution.items():
            key = _safe_float(k, 0.0)
            count = max(0.0, _safe_float(v, 0.0))
            weighted_sum += key * count
            total_count += count
        if total_count > 0:
            avg_ac = weighted_sum / total_count
            ac_label = f"{avg_ac:.1f}"
            ac_sub = f"(Average : {avg_ac:.1f})"

    trend_series: List[float] = []
    trends = phase_c.get("historical_trends", {})
    if isinstance(trends, dict):
        rising = trends.get("rising_numbers", [])
        if isinstance(rising, list):
            for item in rising[:15]:
                if not isinstance(item, dict):
                    continue
                delta = _safe_float(item.get("delta_rate", 0.0), 0.0)
                recent = _safe_float(item.get("recent_rate", 0.0), 0.0)
                trend_score = (recent * 100.0) + (delta * 35.0)
                trend_series.append(max(0.0, min(100.0, trend_score)))

    if not trend_series:
        trend_series = [50.0, 45.0, 55.0, 35.0, 40.0, 25.0, 45.0, 50.0, 30.0, 20.0, 40.0, 55.0]

    summary_lines: List[str] = []
    if hot_numbers:
        summary_lines.append(
            "Hot: " + ", ".join(f"{item['number']}({item['rate_pct']:.1f}%)" for item in hot_numbers[:3])
        )
    if cold_numbers:
        summary_lines.append(
            "Cold: " + ", ".join(f"{item['number']}({item['rate_pct']:.1f}%)" for item in cold_numbers[:3])
        )

    return {
        "hot_numbers": hot_numbers,
        "cold_numbers": cold_numbers,
        "odd_even": {"value": odd_even_label, "sub": odd_even_sub},
        "high_low": {"value": high_low_label, "sub": high_low_sub},
        "sum_distribution": {"value": sum_label, "sub": sum_sub},
        "ac_value": {"value": ac_label, "sub": ac_sub},
        "trend_series": trend_series,
        "summary_lines": summary_lines,
    }


def build_backtest_report_lines(result: Dict[str, Any]) -> List[str]:
    """
    Builds reusable text lines for backtest reporting.
    """
    result = result if isinstance(result, dict) else {}
    if result.get("status") != "success":
        message = result.get("msg", result.get("message", "Unknown error"))
        return [f"Backtest failed: {message}"]

    test_window = _safe_int(result.get("test_total_draws", 0), 0)
    metric_definition = result.get("metric_definition", {})
    algo = result.get("algorithm", {})
    rand = result.get("random_baseline", {})
    algo_metrics = algo.get("metrics", {}) if isinstance(algo, dict) else {}
    rand_metrics = rand.get("metrics", {}) if isinstance(rand, dict) else {}

    lines: List[str] = []
    lines.append("")
    lines.append("==================================================")
    lines.append(f" BACKTEST & ROI PERFORMANCE REPORT (Last {test_window} Draws)")
    lines.append("==================================================")
    lines.append("")
    lines.append("[AI Algorithm Model]")
    if isinstance(metric_definition, dict) and metric_definition:
        lines.append(
            " - Metric Scope: "
            + str(metric_definition.get("precision_recall_scope", "ticket-level summary"))
        )
    lines.append(f" - Total Cost: {_safe_int(algo.get('total_cost', 0), 0):,} KRW")
    lines.append(f" - Total Prize: {_safe_int(algo.get('total_prize', 0), 0):,} KRW")
    lines.append(f" - Return on Investment (ROI): {_safe_float(algo.get('roi', 0.0), 0.0)}%")
    lines.append(f" - Ranks Breakdown: {algo.get('ranks', {}) if isinstance(algo, dict) else {}}")
    lines.append(
        " - Hit/Match Rates: "
        f"Hit={_safe_float(algo_metrics.get('hit_rate', 0.0), 0.0)}% | "
        f"M3={_safe_float(algo_metrics.get('match_3_rate', 0.0), 0.0)}% | "
        f"M4={_safe_float(algo_metrics.get('match_4_rate', 0.0), 0.0)}% | "
        f"M5={_safe_float(algo_metrics.get('match_5_rate', 0.0), 0.0)}% | "
        f"M6={_safe_float(algo_metrics.get('match_6_rate', 0.0), 0.0)}%"
    )
    lines.append(
        " - Classification Metrics: "
        f"Precision={_safe_float(algo_metrics.get('precision', 0.0), 0.0)}% | "
        f"Recall={_safe_float(algo_metrics.get('recall', 0.0), 0.0)}% | "
        f"F1={_safe_float(algo_metrics.get('f1_score', 0.0), 0.0)}% | "
        f"Tickets={_safe_int(algo_metrics.get('ticket_count', 0), 0)} | "
        f"Coverage={_safe_float(algo_metrics.get('avg_unique_predictions_per_draw', 0.0), 0.0)}"
    )
    lines.append("")
    lines.append("[Random Baseline Comparison]")
    lines.append(f" - Total Cost: {_safe_int(rand.get('total_cost', 0), 0):,} KRW")
    lines.append(f" - Total Prize: {_safe_int(rand.get('total_prize', 0), 0):,} KRW")
    lines.append(f" - Return on Investment (ROI): {_safe_float(rand.get('roi', 0.0), 0.0)}%")
    lines.append(f" - Ranks Breakdown: {rand.get('ranks', {}) if isinstance(rand, dict) else {}}")
    lines.append(
        " - Hit/Match Rates: "
        f"Hit={_safe_float(rand_metrics.get('hit_rate', 0.0), 0.0)}% | "
        f"M3={_safe_float(rand_metrics.get('match_3_rate', 0.0), 0.0)}% | "
        f"M4={_safe_float(rand_metrics.get('match_4_rate', 0.0), 0.0)}% | "
        f"M5={_safe_float(rand_metrics.get('match_5_rate', 0.0), 0.0)}% | "
        f"M6={_safe_float(rand_metrics.get('match_6_rate', 0.0), 0.0)}%"
    )
    lines.append(
        " - Classification Metrics: "
        f"Precision={_safe_float(rand_metrics.get('precision', 0.0), 0.0)}% | "
        f"Recall={_safe_float(rand_metrics.get('recall', 0.0), 0.0)}% | "
        f"F1={_safe_float(rand_metrics.get('f1_score', 0.0), 0.0)}% | "
        f"Tickets={_safe_int(rand_metrics.get('ticket_count', 0), 0)} | "
        f"Coverage={_safe_float(rand_metrics.get('avg_unique_predictions_per_draw', 0.0), 0.0)}"
    )
    lines.append("")
    lines.append("==================================================")
    return lines


def build_backtest_report_text(result: Dict[str, Any]) -> str:
    return "\n".join(build_backtest_report_lines(result))
