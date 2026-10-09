# -*- coding: utf-8 -*-
# ui/controllers/data_sync_controller.py
import logging
import psutil
import traceback
from PyQt5.QtCore import QTimer
from data.lotto_db_helper import LottoDBHelper
from data.repositories.lotto_repository import LottoRepository
from workers.ai_train_worker import AITrainWorker
from core.engines.statistics_engine import StatisticsEngine

_log = logging.getLogger("DataSyncController")


class StatisticsWidgetConnector:
    """Connector class to bridge unified StatisticsEngine data to UI analytical widgets safely."""
    def __init__(self, main_window):
        self.main_window = main_window

    def update_all_widgets(self, history_data):
        try:
            if not history_data:
                history_data = [{"draw": 1, "numbers": [1, 10, 20, 30, 40, 45]}]

            gaps_data = StatisticsEngine.analyze_periodicity_and_gaps(history_data)
            decade_data = StatisticsEngine.analyze_decade_and_digit_distribution(history_data)
            chi2_data = StatisticsEngine.chi_square_goodness_of_fit(history_data)
            phase_c_data = StatisticsEngine.build_phase_c_analytics(history_data, lookback_draws=80)
            comprehensive_stats = StatisticsEngine.get_comprehensive_statistics()
            if not isinstance(comprehensive_stats, dict):
                comprehensive_stats = {}
            if not comprehensive_stats:
                comprehensive_stats = {"phase_c_analytics": phase_c_data}

            if hasattr(self.main_window, 'decade_dist_widget') and self.main_window.decade_dist_widget:
                if hasattr(self.main_window.decade_dist_widget, 'update_data'):
                    self.main_window.decade_dist_widget.update_data(decade_data)
                elif hasattr(self.main_window.decade_dist_widget, 'load_data'):
                    self.main_window.decade_dist_widget.load_data()

            if hasattr(self.main_window, 'heatmap_widget') and self.main_window.heatmap_widget:
                if hasattr(self.main_window.heatmap_widget, 'update_heat_with_gaps'):
                    self.main_window.heatmap_widget.update_heat_with_gaps(gaps_data)
                elif hasattr(self.main_window.heatmap_widget, 'load_heatmap_data'):
                    self.main_window.heatmap_widget.load_heatmap_data()

            if hasattr(self.main_window, 'statistical_metrics_widget') and self.main_window.statistical_metrics_widget:
                if hasattr(self.main_window.statistical_metrics_widget, 'update_chi_square_metrics'):
                    self.main_window.statistical_metrics_widget.update_chi_square_metrics(chi2_data)

            if hasattr(self.main_window, 'real_time_analytics_widget') and self.main_window.real_time_analytics_widget:
                if hasattr(self.main_window.real_time_analytics_widget, 'update_from_statistics'):
                    self.main_window.real_time_analytics_widget.update_from_statistics(comprehensive_stats)

            if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                p_val_str = f"{chi2_data.get('p_value', 1.0):.4f}"
                uniform_status = "Normal (Uniform)" if chi2_data.get('is_uniformly_distributed', True) else "Biased (Skewed)"
                self.main_window.live_console_widget.log_message(f"Advanced Stats: Chi2 p-value={p_val_str} [{uniform_status}]")
                hot = phase_c_data.get("hot_numbers", [])[:3]
                cold = phase_c_data.get("cold_numbers", [])[:3]
                if hot:
                    self.main_window.live_console_widget.log_message(
                        "Hot Numbers: " + ", ".join(str(item.get("number")) for item in hot)
                    )
                if cold:
                    self.main_window.live_console_widget.log_message(
                        "Cold Numbers: " + ", ".join(str(item.get("number")) for item in cold)
                    )

            _log.info("All analytical statistics successfully pushed to connected UI widgets via StatisticsEngine.")
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] StatisticsWidgetConnector error: {e}\n{traceback.format_exc()}")


class DataSyncController:
    """Controller responsible for data synchronization, statistics updating, and AI background training workers."""

    def __init__(self, main_window):
        self.main_window = main_window
        self.ai_worker = None

        # AI training background task timer (every 30 minutes)
        self.ai_train_timer = QTimer(main_window)
        self.ai_train_timer.timeout.connect(self.init_auto_ai_training)
        self.ai_train_timer.start(30 * 60 * 1000)

    def init_auto_data_update(self):
        """Load local lotto records and synchronize all analytical widgets."""
        try:
            _log.info("Loading local lotto records and synchronizing widgets...")
            
            if hasattr(self.main_window, 'official_history_widget') and self.main_window.official_history_widget:
                if hasattr(self.main_window.official_history_widget, 'load_draw_data'):
                    self.main_window.official_history_widget.load_draw_data()
            
            formatted_history = []
            try:
                draws = LottoRepository.get_all_draws()
                if draws:
                    for i, d in enumerate(draws):
                        draw_no_raw = d.get("draw_no", d.get("drwNo", i + 1))
                        try:
                            draw_no = int(draw_no_raw)
                        except (TypeError, ValueError):
                            draw_no = i + 1

                        nums = []
                        for j in range(1, 7):
                            raw_val = d.get(f"num{j}")
                            if raw_val is None:
                                raw_val = d.get(f"drwtNo{j}")
                            try:
                                n = int(raw_val)
                                if 1 <= n <= 45:
                                    nums.append(n)
                            except (TypeError, ValueError):
                                continue

                        if len(nums) == 6:
                            formatted_history.append({"draw": draw_no, "numbers": nums})
            except Exception as stat_ex:
                _log.warning(f"Failed to fetch draws for statistics: {stat_ex}", exc_info=True)

            connector = StatisticsWidgetConnector(self.main_window)
            connector.update_all_widgets(formatted_history)

            if hasattr(self.main_window, 'sum_widget') and self.main_window.sum_widget:
                try:
                    draws = LottoRepository.get_all_draws()
                    if draws:
                        total_sum = 0
                        count = 0
                        for draw in draws:
                            nums = [draw.get(f"num{i}") or draw.get(f"drwtNo{i}") or 0 for i in range(1, 7)]
                            valid_6 = [int(n) for n in nums if int(n) > 0]
                            if len(valid_6) == 6:
                                total_sum += sum(valid_6)
                                count += 1
                        if count > 0:
                            hist_avg = round(total_sum / count)
                            if hasattr(self.main_window.sum_widget, 'update_historical_average'):
                                self.main_window.sum_widget.update_historical_average(hist_avg)
                            elif hasattr(self.main_window.sum_widget, 'set_hist_avg'):
                                self.main_window.sum_widget.set_hist_avg(hist_avg)
                            elif hasattr(self.main_window.sum_widget, 'hist_avg_label'):
                                self.main_window.sum_widget.hist_avg_label.setText(f"Hist.Avg: {hist_avg}")
                except Exception as ex:
                    _log.warning(f"Failed to calculate historical average for sum widget: {ex}", exc_info=True)

            for widget_name, method_candidates in [
                ('decade_dist_widget', ['load_data', 'refresh', 'update_data', 'load_decade_data']),
                ('consecutive_widget', ['load_data', 'refresh', 'update_data', 'load_consecutive_data']),
                ('heatmap_widget', ['load_heatmap_data', 'load_data', 'refresh'])
            ]:
                widget = getattr(self.main_window, widget_name, None)
                if widget:
                    for m in method_candidates:
                        if hasattr(widget, m):
                            try:
                                getattr(widget, m)()
                                break
                            except Exception as ex:
                                _log.warning(f"Failed to call {m} on {widget_name}: {ex}", exc_info=True)

            if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                self.main_window.live_console_widget.log_message("Lotto Data: Local cache loaded & Widgets synchronized successfully.")
            _log.info("Local lotto data synchronization & widget refresh finished successfully.")
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] init_auto_data_update failed: {e}\n{traceback.format_exc()}")
            if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                self.main_window.live_console_widget.log_message("Lotto Data: Running on offline local cache.")

    def init_auto_ai_training(self):
        """Initialize and start background AI training worker."""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            mem_info = psutil.virtual_memory()
            system_telemetry = f"System Resource Status -> CPU: {cpu_percent}% | RAM: {mem_info.percent}% ({mem_info.used / (1024**3):.1f} GB used)"
            _log.info(system_telemetry)

            if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                self.main_window.live_console_widget.log_message("AI Model: Running continuous background 50-epoch auto-training with Dynamic Ensemble update...")
                self.main_window.live_console_widget.log_message(system_telemetry)
            
            if self.ai_worker is not None and self.ai_worker.isRunning():
                return

            self.ai_worker = AITrainWorker(total_epochs=50)
            self.ai_worker.progress_signal.connect(self.on_ai_training_progress)
            self.ai_worker.finished_signal.connect(self.on_ai_training_finished)
            self.ai_worker.start()
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] init_auto_ai_training failed: {e}\n{traceback.format_exc()}")

    def on_ai_training_progress(self, epoch, total, loss, acc, lr, time_str):
        """Handle background AI training progress updates."""
        try:
            ai_status_widget = getattr(self.main_window, 'ai_status_widget', None)
            if (
                ai_status_widget
                and hasattr(ai_status_widget, 'ai_training_widget')
                and ai_status_widget.ai_training_widget
                and hasattr(ai_status_widget.ai_training_widget, 'update_training_metrics')
            ):
                ai_status_widget.ai_training_widget.update_training_metrics(epoch, total, loss, acc, lr, time_str)
                return

            if hasattr(self.main_window, 'ai_training_widget') and self.main_window.ai_training_widget:
                self.main_window.ai_training_widget.update_training_metrics(epoch, total, loss, acc, lr, time_str)
        except Exception as e:
            _log.warning(f"on_ai_training_progress warning: {e}", exc_info=True)

    def on_ai_training_finished(self, result):
        """Safely handle AI background training completion signal and clean up thread resources."""
        try:
            if result and isinstance(result, dict) and result.get("status") == "Success":
                checkpoint_msg = "AI Model: Continuous background auto-training (50 epochs) & Dynamic Ensemble re-weighting finished successfully."
                if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                    self.main_window.live_console_widget.log_message(checkpoint_msg)
                _log.info(checkpoint_msg)
            else:
                if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                    self.main_window.live_console_widget.log_message("AI Model: Auto-training skipped/failed, using fallback.")
        except Exception as e:
            _log.error(f"Error handling AI training finish signal: {e}", exc_info=True)
        finally:
            if self.ai_worker:
                try:
                    if self.ai_worker.isRunning():
                        self.ai_worker.quit()
                        self.ai_worker.wait(1000)
                    self.ai_worker.deleteLater()
                except Exception as ex:
                    _log.warning(f"Failed to safely clean up ai_worker: {ex}", exc_info=True)
                self.ai_worker = None

    def update_metrics_from_generated_history(self):
        """Calculate and update analytical metrics based on generated history records."""
        try:
            history = LottoDBHelper.get_generation_history() if hasattr(LottoDBHelper, 'get_generation_history') else []
            if not history:
                return
            
            total_odds = total_evens = total_lows = total_highs = total_sum = count = 0
            total_ac = 0.0

            for record in history:
                numbers = record.get("numbers", record.get("set_numbers", []))
                valid_6 = [n for n in numbers if 1 <= n <= 45][:6]
                if len(valid_6) == 6:
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

                    total_odds += odds
                    total_evens += evens
                    total_lows += lows
                    total_highs += highs
                    total_sum += s
                    total_ac += ac
                    count += 1

            if count > 0:
                avg_odds = round(total_odds / count)
                avg_evens = 6 - avg_odds
                avg_lows = round(total_lows / count)
                avg_highs = 6 - avg_lows
                mean_sum = round(total_sum / count)
                mean_ac = round(total_ac / count, 1)

                if hasattr(self.main_window, 'odd_even_widget'):
                    self.main_window.odd_even_widget.update_ratio(avg_odds, avg_evens)
                if hasattr(self.main_window, 'high_low_widget'):
                    self.main_window.high_low_widget.update_ratio(avg_lows, avg_highs)
                if hasattr(self.main_window, 'ac_widget'):
                    self.main_window.ac_widget.update_ac_value(float(mean_ac))
                if hasattr(self.main_window, 'sum_widget'):
                    self.main_window.sum_widget.update_sum_value(int(mean_sum))
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] update_metrics_from_generated_history error: {e}\n{traceback.format_exc()}")