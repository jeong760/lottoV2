# ui/main_window.py
import sys
import os
import logging
import random
import math
import time
import psutil
import traceback
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QSplitter, QDesktopWidget, QSizePolicy
from PyQt5.QtCore import Qt, QTimer

_log = logging.getLogger("LottoMainWindow")

AlgorithmHub = None
try:
    import importlib
    _core_hub_mod = importlib.import_module("core.algorithm_hub")
    if hasattr(_core_hub_mod, "AlgorithmHub"):
        AlgorithmHub = _core_hub_mod.AlgorithmHub
except Exception as e:
    _log.critical(f"[CRITICAL DEBUG] AlgorithmHub import failed: {e}\n{traceback.format_exc()}")

from ui.controllers.simulation_controller import SimulationController
from ui.controllers.data_sync_controller import DataSyncController

from ui.widgets.header_widget import HeaderWidget
from ui.widgets.ai_status_widget import AIStatusWidget
from ui.widgets.official_draw_history_widget import OfficialDrawHistoryWidget
from ui.widgets.generated_sets_widget import GeneratedSetsWidget
from ui.widgets.backtest_widget import BacktestWidget

from ui.widgets.heatmap_widget import LottoHeatmapWidget
from ui.widgets.venus_drum_widget import VenusDrumWidget
from ui.widgets.drawing_startstop_widget import DrawingStartStopWidget
from ui.widgets.live_console_widget import LiveConsoleWidget
from ui.widgets.system_parameters_widget import SystemParametersWidget
from ui.widgets.db_management_widget import DBManagementWidget

from ui.widgets.odd_even_widget import OddEvenWidget
from ui.widgets.high_low_widget import HighLowWidget
from ui.widgets.ac_widget import ACWidget
from ui.widgets.sum_widget import SumWidget

from ui.widgets.ratio_balance_widget import RatioBalanceWidget
from ui.widgets.statistical_metrics_widget import StatisticalMetricsWidget
from ui.widgets.decade_dist_widget import DecadeDistWidget
from ui.widgets.consecutive_widget import ConsecutiveWidget
from ui.widgets.ai_training_widget import AITrainingWidget
from ui.widgets.real_time_analytics_widget import RealTimeAnalyticsWidget


class LottoMainWindow(QMainWindow):
    """Main window for Lotto 6/45 Analysis Dashboard, refactored with modular controllers and isolated parameter tab."""
    def __init__(self):
        super().__init__()
        _log.info("[DEBUG] LottoMainWindow __init__ started.")
        
        self.engine = None
        try:
            global AlgorithmHub
            if AlgorithmHub is None:
                import importlib
                mod = importlib.import_module("core.algorithm_hub")
                AlgorithmHub = getattr(mod, "AlgorithmHub", None)
            if AlgorithmHub is not None:
                self.engine = AlgorithmHub()
        except Exception as ex:
            _log.critical(f"[CRITICAL DEBUG] AlgorithmHub instantiation failed: {ex}\n{traceback.format_exc()}")
        
        self.sim_controller = SimulationController(self)
        self.data_controller = DataSyncController(self)

        self.physics_timer = QTimer(self)
        self.physics_timer.timeout.connect(self.update_turbine_physics)
        self.physics_timer.start(13)

        try:
            self.init_ui()
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] init_ui failed: {e}\n{traceback.format_exc()}")
            raise e
        
        QTimer.singleShot(400, self.data_controller.init_auto_data_update)
        QTimer.singleShot(700, self.data_controller.update_metrics_from_generated_history)
        _log.info("[DEBUG] LottoMainWindow __init__ finished successfully.")

    def init_ui(self):
        _log.info("[DEBUG] init_ui started.")
        self.setWindowTitle('Lotto 6/45 Analysis Dashboard (Universal Responsive Edition)')
        
        screen_geometry = QDesktopWidget().availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        fixed_width = 1650
        fixed_height = 930

        self.setGeometry(
            (screen_width - fixed_width) // 2,
            (screen_height - fixed_height) // 2,
            fixed_width,
            fixed_height
        )
        
        self.setFixedSize(fixed_width, fixed_height)
        self.setStyleSheet("background-color: #f4f6f9;")

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #dcdde1; background: #f4f6f9; border-radius: 6px; }
            QTabBar::tab { background: #e4e7eb; color: #2c3e50; padding: 6px 16px; font-weight: bold; font-size: 11px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
            QTabBar::tab:selected { background: #ffffff; color: #2980b9; border-bottom: 3px solid #2980b9; }
        """)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        tab_generator = QWidget()
        tab_gen_main_layout = QVBoxLayout(tab_generator)
        tab_gen_main_layout.setContentsMargins(2, 2, 2, 2)
        tab_gen_main_layout.setSpacing(2)

        self.header_widget = HeaderWidget()
        tab_gen_main_layout.addWidget(self.header_widget)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("""
            QSplitter {
                background-color: #f4f6f9;
            }
            QSplitter::handle {
                background-color: #e4e7eb;
                margin: 0px;
            }
            QSplitter::handle:hover {
                background-color: #bdc3c7;
            }
        """)

        # --- Left Side: Venus Turbine & Controls ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(2, 2, 2, 2)
        left_layout.setSpacing(4)
        
        self.turbine_widget = VenusDrumWidget()
        self.drawing_control_widget = DrawingStartStopWidget()
        
        ratio_stat_layout = QHBoxLayout()
        ratio_stat_layout.setContentsMargins(0, 0, 0, 0)
        ratio_stat_layout.setSpacing(2)
        
        self.ratio_balance_widget = RatioBalanceWidget()
        self.statistical_metrics_widget = StatisticalMetricsWidget()
        
        ratio_stat_layout.addWidget(self.ratio_balance_widget, stretch=1)
        ratio_stat_layout.addWidget(self.statistical_metrics_widget, stretch=1)
        
        ratio_stat_container = QWidget()
        ratio_stat_container.setLayout(ratio_stat_layout)

        self.live_console_widget = LiveConsoleWidget()

        left_layout.addWidget(self.turbine_widget, stretch=45)
        left_layout.addWidget(self.drawing_control_widget, stretch=8)
        left_layout.addWidget(ratio_stat_container, stretch=15)
        left_layout.addWidget(self.live_console_widget, stretch=32)
        left_container.setLayout(left_layout)

        # --- Right Side: Analytics & Widgets (Bottom-aligned layout) ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(4)
        
        right_layout.insertStretch(0, 1)

        self.odd_even_widget = OddEvenWidget()
        self.high_low_widget = HighLowWidget()
        self.ac_widget = ACWidget()
        self.sum_widget = SumWidget()  # 새로 추가된 스핀박스/디폴트 버튼 포함 규격 반영
        
        for w in [self.odd_even_widget, self.high_low_widget, self.ac_widget]:
            w.setFixedHeight(115)
            w.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            
        # SumWidget은 높이가 145로 설정되어 있으므로 별도 규격 지정 또는 고정
        self.sum_widget.setFixedHeight(145)
        self.sum_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.decade_dist_widget = DecadeDistWidget()
        self.consecutive_widget = ConsecutiveWidget()
        self.heatmap_widget = LottoHeatmapWidget()

        metrics_layout = QHBoxLayout()
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setSpacing(3)
        metrics_layout.addWidget(self.odd_even_widget)
        metrics_layout.addWidget(self.high_low_widget)
        metrics_layout.addWidget(self.ac_widget)
        metrics_layout.addWidget(self.sum_widget)

        metrics_container = QWidget()
        metrics_container.setLayout(metrics_layout)

        top_freq_consecutive_layout = QHBoxLayout()
        top_freq_consecutive_layout.setContentsMargins(0, 0, 0, 0)
        top_freq_consecutive_layout.setSpacing(10)
        top_freq_consecutive_layout.addWidget(self.decade_dist_widget, alignment=Qt.AlignLeft)
        top_freq_consecutive_layout.addWidget(self.consecutive_widget, alignment=Qt.AlignRight)

        top_freq_consecutive_container = QWidget()
        top_freq_consecutive_container.setLayout(top_freq_consecutive_layout)

        heatmap_layout = QHBoxLayout()
        heatmap_layout.setContentsMargins(0, 0, 0, 0)
        heatmap_layout.addWidget(self.heatmap_widget, alignment=Qt.AlignCenter)

        heatmap_container = QWidget()
        heatmap_container.setLayout(heatmap_layout)

        right_layout.addWidget(metrics_container)
        right_layout.addWidget(top_freq_consecutive_container)
        right_layout.addWidget(heatmap_container)
        right_container.setLayout(right_layout)

        splitter.addWidget(left_container)
        splitter.addWidget(right_container)
        
        left_w = int(fixed_width * 0.50)
        right_w = fixed_width - left_w
        splitter.setSizes([left_w, right_w])

        tab_gen_main_layout.addWidget(splitter)
        tab_generator.setLayout(tab_gen_main_layout)
        
        self.tab_widget.addTab(tab_generator, "Live Venus Turbine Generator")
        
        self.generated_sets_widget = GeneratedSetsWidget()
        self.tab_widget.addTab(self.generated_sets_widget, "Generated Sets")

        self.real_time_analytics_widget = RealTimeAnalyticsWidget()
        self.tab_widget.addTab(self.real_time_analytics_widget, "Real-Time Analytics")

        self.backtest_widget = BacktestWidget()
        self.tab_widget.addTab(self.backtest_widget, "Algorithm Backtesting")

        self.ai_status_widget = AIStatusWidget()
        self.tab_widget.addTab(self.ai_status_widget, "Machine Learning Performance")
        
        self.official_history_widget = OfficialDrawHistoryWidget()
        self.tab_widget.addTab(self.official_history_widget, "Official Draw History (#1~Latest)")

        self.db_management_widget = DBManagementWidget()
        self.tab_widget.addTab(self.db_management_widget, "Database Management")

        self.system_parameters_widget = SystemParametersWidget()
        self.tab_widget.addTab(self.system_parameters_widget, "System Parameters")

        main_layout.addWidget(self.tab_widget)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        if hasattr(self, 'live_console_widget') and self.live_console_widget:
            self.live_console_widget.log_message("QUALITY GATE STATUS: Standby (Dynamic Ensemble Ready)")

        if hasattr(self.generated_sets_widget, 'load_generated_sets'):
            try:
                self.generated_sets_widget.load_generated_sets()
            except Exception as ex:
                _log.critical(f"[CRITICAL DEBUG] Initial load_generated_sets failed: {ex}\n{traceback.format_exc()}")

        if hasattr(self, 'sim_controller') and self.sim_controller:
            self.sim_controller.connect_ui_signals()

        _log.info("[DEBUG] init_ui finished successfully.")

    def on_tab_changed(self, index):
        try:
            current_widget = self.tab_widget.widget(index)
            if current_widget == getattr(self, 'generated_sets_widget', None):
                if hasattr(self.generated_sets_widget, 'load_generated_sets'):
                    self.generated_sets_widget.load_generated_sets()
            elif current_widget == getattr(self, 'db_management_widget', None):
                if hasattr(self.db_management_widget, 'refresh_db_status'):
                    self.db_management_widget.refresh_db_status()
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] on_tab_changed error: {e}\n{traceback.format_exc()}")

    def closeEvent(self, event):
        _log.info("[DEBUG] closeEvent triggered. Closing application safely...")
        try:
            if hasattr(self.sim_controller, 'turbine_timer') and self.sim_controller.turbine_timer.isActive():
                self.sim_controller.turbine_timer.stop()
            if hasattr(self, 'physics_timer') and self.physics_timer.isActive():
                self.physics_timer.stop()
            if hasattr(self.data_controller, 'ai_train_timer') and self.data_controller.ai_train_timer.isActive():
                self.data_controller.ai_train_timer.stop()
            
            if hasattr(self.sim_controller, 'worker') and self.sim_controller.worker is not None:
                try:
                    if self.sim_controller.worker.isRunning():
                        if not getattr(self, "_worker_close_pending", False):
                            self._worker_close_pending = True
                            self.sim_controller.worker.finished.connect(self._close_after_worker_finished)
                        if hasattr(self.sim_controller.worker, "stop"):
                            self.sim_controller.worker.stop()
                        self.sim_controller.worker.quit()
                        self.sim_controller.worker.wait(1000)
                        if self.sim_controller.worker.isRunning():
                            event.ignore()
                            return
                        self._worker_close_pending = False
                except Exception as re:
                    _log.warning(f"Exception while closing worker: {re}", exc_info=True)
                self.sim_controller.worker = None

            if hasattr(self.data_controller, 'ai_worker') and self.data_controller.ai_worker is not None:
                try:
                    if self.data_controller.ai_worker.isRunning():
                        self.data_controller.ai_worker.quit()
                        self.data_controller.ai_worker.wait(1000)
                except Exception as re:
                    _log.warning(f"Exception while closing ai_worker: {re}", exc_info=True)
                self.data_controller.ai_worker = None
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] Error during close event handling: {e}\n{traceback.format_exc()}")
        event.accept()

    def _close_after_worker_finished(self):
        if not getattr(self, "_worker_close_pending", False):
            return
        self._worker_close_pending = False
        self.close()

    def update_turbine_physics(self):
        try:
            if hasattr(self, 'turbine_widget') and self.turbine_widget:
                self.turbine_widget.update_physics()
        except Exception as e:
            _log.warning(f"update_turbine_physics warning: {e}", exc_info=True)

    def _update_live_set_metrics(self, current_6_numbers):
        try:
            if not current_6_numbers or len(current_6_numbers) < 6:
                return
            
            valid_6 = [n for n in current_6_numbers if 1 <= n <= 45][:6]
            odds = sum(1 for n in valid_6 if n % 2 != 0)
            evens = 6 - odds
            lows = sum(1 for n in valid_6 if n <= 22)
            highs = 6 - lows
            s = sum(valid_6)
            
            diffs = set()
            for i in range(len(valid_6)):
                for j in range(i + 1, len(valid_6)):
                    diffs.add(abs(valid_6[i] - valid_6[j]))
            ac = max(0, len(diffs) - 5)

            if hasattr(self, 'odd_even_widget') and self.odd_even_widget:
                self.odd_even_widget.update_ratio(odds, evens)
            if hasattr(self, 'high_low_widget') and self.high_low_widget:
                self.high_low_widget.update_ratio(lows, highs)
            if hasattr(self, 'ac_widget') and self.ac_widget:
                self.ac_widget.update_ac_value(float(ac))
            if hasattr(self, 'sum_widget') and self.sum_widget:
                self.sum_widget.update_sum_value(int(s))
            if hasattr(self, 'ratio_balance_widget') and self.ratio_balance_widget:
                self.ratio_balance_widget.update_from_numbers(valid_6)
            if hasattr(self, 'statistical_metrics_widget') and self.statistical_metrics_widget:
                self.statistical_metrics_widget.update_from_numbers(valid_6)
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] _update_live_set_metrics error: {e}\n{traceback.format_exc()}")


MainWindow = LottoMainWindow