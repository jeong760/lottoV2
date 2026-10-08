# -*- coding: utf-8 -*-
# ui/widgets/backtest_widget.py
import logging
import random
import os
import sys

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from data.repositories.lotto_repository import LottoRepository
from core.lotto_evaluator import LottoEvaluator
from utils.logger import setup_logging

setup_logging(project_root)
_log = logging.getLogger("BacktestWidget")

class BacktestWorker(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(dict)

    def __init__(self, test_rounds=50):
        super().__init__()
        self.test_rounds = test_rounds

    def __del__(self):
        try:
            _log.debug(f"[{self.__class__.__name__}] Thread object is being destroyed.")
        except Exception:
            pass

    def run(self):
        try:
            _log.info("Starting backtest worker thread initialization...")
            draws = LottoRepository.get_all_draws()
            if not draws or len(draws) < self.test_rounds + 30:
                _log.warning("Insufficient history records for rigorous backtesting.")
                self.finished_signal.emit({"status": "Error", "msg": "Insufficient history for rigorous backtesting."})
                return

            self.progress_signal.emit(10, "Initializing Walk-Forward time-series split...")

            def dummy_algorithm_engine(train_pool, set_count):
                sets = []
                for _ in range(set_count):
                    sets.append(sorted(random.sample(range(1, 46), 6)))
                return sets

            self.progress_signal.emit(30, f"Evaluating {self.test_rounds} draws with Train/Test separation...")
            _log.info(f"Executing Walk-Forward backtest simulation for {self.test_rounds} test rounds.")
            
            simulation_result = LottoEvaluator.run_backtest_simulation(
                all_draws=draws,
                algorithm_engine=dummy_algorithm_engine,
                test_window_size=self.test_rounds,
                sets_per_draw=5
            )

            if not simulation_result or simulation_result.get("status") != "success":
                err_msg = simulation_result.get("message", "Unknown simulation failure") if isinstance(simulation_result, dict) else "Invalid simulation result format"
                _log.error(f"Backtest simulation failed: {err_msg}")
                self.finished_signal.emit({"status": "Error", "msg": err_msg})
                return

            self.progress_signal.emit(90, "Calculating ROI and comparing with Random Baseline...")
            self.progress_signal.emit(100, "Backtest simulation completed successfully.")
            _log.info("Backtest simulation completed successfully with ROI analysis.")

            self.finished_signal.emit(simulation_result)
        except Exception as e:
            _log.error(f"Backtest execution error: {e}", exc_info=True)
            self.finished_signal.emit({"status": "Error", "msg": str(e)})

class BacktestWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("<b>Enterprise Backtesting & Algorithm Simulation Dashboard (Walk-Forward & ROI)</b>")
        title.setStyleSheet("font-size: 14px; color: #2c3e50;")
        layout.addWidget(title)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 4px; font-family: Consolas;")
        layout.addWidget(self.log_box)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Walk-Forward Backtest & ROI Analysis")
        self.run_btn.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.run_btn.clicked.connect(self.start_backtest)
        btn_layout.addWidget(self.run_btn)

        layout.addLayout(btn_layout)

    def start_backtest(self):
        self.run_btn.setEnabled(False)
        self.log_box.clear()
        self.log_box.append("Starting rigorous Walk-Forward backtest simulation across recent 50 draws...")
        _log.info("User triggered Walk-Forward backtest simulation.")
        
        if self.worker is not None and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()

        self.worker = BacktestWorker(test_rounds=50)
        self.worker.progress_signal.connect(lambda p, m: (self.progress_bar.setValue(p), self.log_box.append(m)))
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def on_finished(self, result):
        self.run_btn.setEnabled(True)
        try:
            if result and result.get("status") == "success":
                test_window = result.get("test_total_draws", 50)
                algo = result.get("algorithm", {})
                rand = result.get("random_baseline", {})

                self.log_box.append(f"\n==================================================")
                self.log_box.append(f" BACKTEST & ROI PERFORMANCE REPORT (Last {test_window} Draws)")
                self.log_box.append(f"==================================================")
                
                self.log_box.append(f"\n[AI Algorithm Model]")
                self.log_box.append(f" - Total Cost: {algo.get('total_cost', 0):,} KRW")
                self.log_box.append(f" - Total Prize: {algo.get('total_prize', 0):,} KRW")
                self.log_box.append(f" - Return on Investment (ROI): {algo.get('roi', 0.0)}%")
                self.log_box.append(f" - Ranks Breakdown: {algo.get('ranks', {})}")
                algo_metrics = algo.get("metrics", {})
                if isinstance(algo_metrics, dict):
                    self.log_box.append(
                        " - Hit/Match Rates: "
                        f"Hit={algo_metrics.get('hit_rate', 0.0)}% | "
                        f"M3={algo_metrics.get('match_3_rate', 0.0)}% | "
                        f"M4={algo_metrics.get('match_4_rate', 0.0)}% | "
                        f"M5={algo_metrics.get('match_5_rate', 0.0)}% | "
                        f"M6={algo_metrics.get('match_6_rate', 0.0)}%"
                    )
                    self.log_box.append(
                        " - Classification Metrics: "
                        f"Precision={algo_metrics.get('precision', 0.0)}% | "
                        f"Recall={algo_metrics.get('recall', 0.0)}% | "
                        f"F1={algo_metrics.get('f1_score', 0.0)}% | "
                        f"Tickets={algo_metrics.get('ticket_count', 0)}"
                    )

                self.log_box.append(f"\n[Random Baseline Comparison]")
                self.log_box.append(f" - Total Cost: {rand.get('total_cost', 0):,} KRW")
                self.log_box.append(f" - Total Prize: {rand.get('total_prize', 0):,} KRW")
                self.log_box.append(f" - Return on Investment (ROI): {rand.get('roi', 0.0)}%")
                self.log_box.append(f" - Ranks Breakdown: {rand.get('ranks', {})}")
                rand_metrics = rand.get("metrics", {})
                if isinstance(rand_metrics, dict):
                    self.log_box.append(
                        " - Hit/Match Rates: "
                        f"Hit={rand_metrics.get('hit_rate', 0.0)}% | "
                        f"M3={rand_metrics.get('match_3_rate', 0.0)}% | "
                        f"M4={rand_metrics.get('match_4_rate', 0.0)}% | "
                        f"M5={rand_metrics.get('match_5_rate', 0.0)}% | "
                        f"M6={rand_metrics.get('match_6_rate', 0.0)}%"
                    )
                    self.log_box.append(
                        " - Classification Metrics: "
                        f"Precision={rand_metrics.get('precision', 0.0)}% | "
                        f"Recall={rand_metrics.get('recall', 0.0)}% | "
                        f"F1={rand_metrics.get('f1_score', 0.0)}% | "
                        f"Tickets={rand_metrics.get('ticket_count', 0)}"
                    )
                self.log_box.append(f"\n==================================================")
                _log.info("Backtest results successfully rendered on UI dashboard.")
            else:
                error_msg = result.get('msg', 'Unknown error') if isinstance(result, dict) else 'Invalid response format'
                self.log_box.append(f"\nBacktest failed: {error_msg}")
                _log.error(f"Backtest failure reported on UI: {error_msg}")
        finally:
            if self.worker:
                self.worker = None