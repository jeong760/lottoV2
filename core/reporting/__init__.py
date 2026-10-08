# -*- coding: utf-8 -*-
"""Reporting helpers for dashboard and backtest outputs."""

from .dashboard_reporting import (
    build_backtest_report_lines,
    build_backtest_report_text,
    build_generation_batch_report_lines,
    build_generation_batch_report_text,
    build_realtime_dashboard_payload,
)

__all__ = [
    "build_backtest_report_lines",
    "build_backtest_report_text",
    "build_generation_batch_report_lines",
    "build_generation_batch_report_text",
    "build_realtime_dashboard_payload",
]
