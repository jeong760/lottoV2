# -*- coding: utf-8 -*-
# ui/widgets/backtest_widget.py
import logging
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
from core.engines.lotto_engine import LottoEngine
from core.reporting.dashboard_reporting import build_backtest_report_lines, build_backtest_report_text
from utils.logger import setup_logging
from PyQt5.QtWidgets import QFileDialog, QMessageBox

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
            raw_draws = LottoRepository.get_all_draws()
            normalized_draws = []
            for draw in raw_draws or []:
                if not isinstance(draw, dict):
                    continue

                nums = []
                for i in range(1, 7):
                    raw_num = draw.get(f"num{i}")
                    if raw_num is None:
                        raw_num = draw.get(f"drwtNo{i}")
                    try:
                        iv = int(raw_num)
                        if 1 <= iv <= 45:
                            nums.append(iv)
                    except (TypeError, ValueError):
                        continue

                if len(nums) != 6:
                    continue

                normalized = dict(draw)
                normalized["numbers"] = sorted(nums)
                draw_no = draw.get("draw_no", draw.get("drwNo", 0))
                normalized["draw_no"] = draw_no
                normalized["drwNo"] = draw_no
                try:
                    bonus = int(draw.get("bonus", draw.get("bnusNo", 0)) or 0)
                except (TypeError, ValueError):
                    bonus = 0
                normalized["bonus"] = bonus
                normalized["bnusNo"] = bonus
                normalized_draws.append(normalized)

            if not normalized_draws or len(normalized_draws) < self.test_rounds + 30:
                _log.warning("Insufficient history records for rigorous backtesting.")
                self.finished_signal.emit({"status": "Error", "msg": "Insufficient history for rigorous backtesting."})
                return

            normalized_draws.sort(key=lambda draw: int(draw["draw_no"]))
            test_count = min(max(1, int(self.test_rounds)), len(normalized_draws) - 30)
            start_test_draw = int(normalized_draws[-test_count]["draw_no"])
            self.progress_signal.emit(10, "Initializing Walk-Forward time-series split...")

            engine = LottoEngine(historical_draws=[])

            def _to_history_sets(history_pool):
                converted = []
                for rec in history_pool or []:
                    if not isinstance(rec, dict):
                        continue
                    nums = rec.get("numbers", [])
                    if not nums:
                        nums = [rec.get(f"num{i}") or rec.get(f"drwtNo{i}") for i in range(1, 7)]
                    parsed = []
                    for n in nums:
                        try:
                            iv = int(n)
                            if 1 <= iv <= 45:
                                parsed.append(iv)
                        except (TypeError, ValueError):
                            continue
                    parsed = sorted(parsed[:6])
                    if len(parsed) == 6:
                        converted.append(parsed)
                return converted

            def real_algorithm_engine(train_pool, set_count):
                generated_sets = []
                try:
                    history_sets = _to_history_sets(train_pool)
                    if history_sets:
                        engine.historical_draws = history_sets
                        engine._recalculate_analytics()

                    prediction_sets = engine.generate_prediction_sets(
                        set_count=max(1, int(set_count)),
                        selected_algorithm_id="ensemble_auto",
                    ) or []
                    for pred in prediction_sets:
                        nums = pred.get("numbers", []) if isinstance(pred, dict) else pred
                        if not isinstance(nums, (list, tuple)):
                            continue
                        parsed = []
                        for n in nums[:6]:
                            try:
                                iv = int(n)
                                if 1 <= iv <= 45:
                                    parsed.append(iv)
                            except (TypeError, ValueError):
                                continue
                        parsed = sorted(parsed)
                        if len(parsed) == 6 and parsed not in generated_sets:
                            generated_sets.append(parsed)

                except Exception as exc:
                    raise RuntimeError(f"Algorithm generation failed: {exc}") from exc
                if len(generated_sets) < int(set_count):
                    raise RuntimeError(
                        f"Algorithm generated {len(generated_sets)} valid sets; expected {int(set_count)}."
                    )
                return generated_sets[:int(set_count)]

            self.progress_signal.emit(30, f"Evaluating {self.test_rounds} draws with Train/Test separation...")
            _log.info(f"Executing Walk-Forward backtest simulation for {self.test_rounds} test rounds.")
            
            simulation_result = LottoEvaluator.run_backtest_simulation(
                all_draws=normalized_draws,
                algorithm_engine=real_algorithm_engine,
                start_test_draw=start_test_draw,
                test_window_size=test_count,
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
        self.last_result = None
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

        self.export_btn = QPushButton("Export Backtest Report")
        self.export_btn.setStyleSheet("background-color: #16a085; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_backtest_report)
        btn_layout.addWidget(self.export_btn)

        layout.addLayout(btn_layout)

    def start_backtest(self):
        self.run_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.last_result = None
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
                self.last_result = result
                self.export_btn.setEnabled(True)
                for line in build_backtest_report_lines(result):
                    self.log_box.append(line)
                _log.info("Backtest results successfully rendered on UI dashboard.")
            else:
                error_msg = result.get('msg', 'Unknown error') if isinstance(result, dict) else 'Invalid response format'
                self.log_box.append(f"\nBacktest failed: {error_msg}")
                _log.error(f"Backtest failure reported on UI: {error_msg}")
        finally:
            if self.worker:
                self.worker = None

    def export_backtest_report(self):
        try:
            if not isinstance(self.last_result, dict) or self.last_result.get("status") != "success":
                QMessageBox.warning(self, "Export Warning", "No successful backtest result is available to export.")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Backtest Report",
                "lotto_backtest_report.txt",
                "Text Files (*.txt);;All Files (*)",
            )
            if not file_path:
                return

            report_text = build_backtest_report_text(self.last_result)
            with open(file_path, mode="w", encoding="utf-8") as f:
                f.write(report_text)

            QMessageBox.information(self, "Success", f"Backtest report exported successfully:\n{file_path}")
            _log.info("Backtest report exported: %s", file_path)
        except Exception as e:
            _log.error(f"Failed to export backtest report: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to export backtest report: {e}")