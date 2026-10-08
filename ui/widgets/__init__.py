# -*- coding: utf-8 -*-
# ui/widgets/__init__.py
import logging
import os
import sys

# Ensure project root is in python path and initialize centralized logging
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("WidgetsModule")

from .header_widget import HeaderWidget
from .ai_status_widget import AIStatusWidget
from .heatmap_widget import LottoHeatmapWidget
from .official_draw_history_widget import OfficialDrawHistoryWidget
from .venus_drum_widget import VenusDrumWidget
from .drawing_startstop_widget import DrawingStartStopWidget
from .lotto_ball_widget import LottoBallWidget
from .live_console_widget import LiveConsoleWidget
from .odd_even_widget import OddEvenWidget
from .high_low_widget import HighLowWidget
from .ac_widget import ACWidget
from .sum_widget import SumWidget
from .decade_dist_widget import DecadeDistWidget
from .consecutive_widget import ConsecutiveWidget
from .statistical_metrics_widget import StatisticalMetricsWidget
from .ratio_balance_widget import RatioBalanceWidget
from .system_parameters_widget import SystemParametersWidget
from .ai_training_widget import AITrainingWidget
from .ai_system_widget import AISystemWidget
from .generated_sets_widget import GeneratedSetsWidget      # [Fix] Added missing GeneratedSetsWidget
from .backtest_widget import BacktestWidget                # [Fix] Added missing BacktestWidget
from .db_management_widget import DBManagementWidget        # [Fix] Added missing DBManagementWidget

_log.info("[WidgetsModule] Widgets package initialization completed safely.")

__all__ = [
    "HeaderWidget",
    "AIStatusWidget",
    "LottoHeatmapWidget",
    "OfficialDrawHistoryWidget",
    "VenusDrumWidget",
    "DrawingStartStopWidget",
    "LottoBallWidget",
    "LiveConsoleWidget",
    "OddEvenWidget",
    "HighLowWidget",
    "ACWidget",
    "SumWidget",
    "DecadeDistWidget",
    "ConsecutiveWidget",
    "StatisticalMetricsWidget",
    "RatioBalanceWidget",
    "SystemParametersWidget",
    "AITrainingWidget",
    "AISystemWidget",
    "GeneratedSetsWidget",
    "BacktestWidget",
    "DBManagementWidget",
]