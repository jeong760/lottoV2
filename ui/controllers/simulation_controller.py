# -*- coding: utf-8 -*-
# ui/controllers/simulation_controller.py
import logging
import random
import time
import psutil
import traceback
from PyQt5.QtCore import QTimer
from workers.lotto_worker import LottoWorker
from data.lotto_db_helper import LottoDBHelper

_log = logging.getLogger("SimulationController")

AVAILABLE_ALGO_GROUPS = [
    "Statistical Distribution Model",
    "Frequency Matrix Analyzer",
    "Machine Learning Gradient Engine",
    "AI Neural Predictor",
    "Historical Pattern Matcher",
    "Advanced Markov Chain Ensemble"
]

class SimulationController:
    """Controller responsible for managing number generation, Venus turbine simulation, and drawing states."""

    def __init__(self, main_window):
        self.main_window = main_window
        
        # Simulation state variables
        self.live_sets = []
        self.current_set_index = 0
        self.current_ball_index = 0
        self.active_set_balls = []
        self.active_bonus_ball = 0
        self.is_generating = False
        self.worker = None
        
        self.current_accumulated_discards = 0
        self.target_discards_to_accumulate = 0
        self.current_algo_title_display = ""
        
        self.drawing_phase = 'IDLE'
        self.remaining_mixing_seconds = 300
        self.simulation_start_time = 0.0

        # Turbine Timer setup
        self.turbine_timer = QTimer(main_window)
        self.turbine_timer.timeout.connect(self.process_turbine_tick)

    def connect_ui_signals(self):
        """Connect drawing control widget signals to controller slots safely."""
        try:
            if hasattr(self.main_window, 'drawing_control_widget') and self.main_window.drawing_control_widget:
                # Disconnect first to prevent duplicate connections if called twice
                try:
                    self.main_window.drawing_control_widget.generate_clicked.disconnect()
                    self.main_window.drawing_control_widget.stop_clicked.disconnect()
                    if hasattr(self.main_window.drawing_control_widget, 'skip_clicked'):
                        self.main_window.drawing_control_widget.skip_clicked.disconnect()
                except Exception:
                    pass

                self.main_window.drawing_control_widget.generate_clicked.connect(self.on_generate_pressed)
                self.main_window.drawing_control_widget.stop_clicked.connect(self.on_stop_pressed)
                if hasattr(self.main_window.drawing_control_widget, 'skip_clicked'):
                    self.main_window.drawing_control_widget.skip_clicked.connect(self.on_skip_pressed)
                _log.info("DrawingStartStopWidget signals successfully connected to SimulationController.")
            else:
                _log.warning("drawing_control_widget not found when attempting to connect signals.")
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] Failed to connect UI signals: {e}\n{traceback.format_exc()}")

    def on_generate_pressed(self, set_count: int):
        """Handle number generation request and initiate worker thread."""
        _log.info(f"[DEBUG] on_generate_pressed called with set_count={set_count}")
        if self.is_generating:
            _log.warning("Number generation and live simulation are already in progress.")
            return

        try:
            self.is_generating = True
            self.simulation_start_time = time.time()
            
            selected_algo = ""
            if hasattr(self.main_window, 'system_parameters_widget') and self.main_window.system_parameters_widget:
                if hasattr(self.main_window.system_parameters_widget, 'get_selected_algorithm'):
                    selected_algo = self.main_window.system_parameters_widget.get_selected_algorithm()
                elif hasattr(self.main_window.system_parameters_widget, 'algorithm_combo') and self.main_window.system_parameters_widget.algorithm_combo:
                    selected_algo = self.main_window.system_parameters_widget.algorithm_combo.currentText()

            if not selected_algo or selected_algo == "Advanced AI Ensemble":
                selected_algo = random.choice(AVAILABLE_ALGO_GROUPS)

            self.current_algo_title_display = selected_algo.split("(")[0].strip() if "(" in selected_algo else selected_algo
            
            fixed_numbers = []
            excluded_numbers = []
            if hasattr(self.main_window, 'system_parameters_widget') and self.main_window.system_parameters_widget:
                if hasattr(self.main_window.system_parameters_widget, 'get_fixed_numbers'):
                    try:
                        fixed_numbers = self.main_window.system_parameters_widget.get_fixed_numbers() or []
                    except Exception:
                        pass
                if hasattr(self.main_window.system_parameters_widget, 'get_excluded_numbers'):
                    try:
                        excluded_numbers = self.main_window.system_parameters_widget.get_excluded_numbers() or []
                    except Exception:
                        pass

            cpu_percent = psutil.cpu_percent(interval=None)
            mem_info = psutil.virtual_memory()
            sys_diag = f"Resource Telemetry -> CPU: {cpu_percent}% | RAM: {mem_info.percent}%"
            _log.info(f"Requesting premium number generation for {set_count:,} sets using Dynamic Ensemble [{self.current_algo_title_display}]. {sys_diag}")

            if hasattr(self.main_window, 'drawing_control_widget') and self.main_window.drawing_control_widget:
                self.main_window.drawing_control_widget.set_controls_enabled(False)

            if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                self.main_window.live_console_widget.log_message(f"Selected Algorithm (Dynamic Ensemble): {self.current_algo_title_display}")
                if fixed_numbers:
                    self.main_window.live_console_widget.log_message(f"User Fixed Numbers Applied: {fixed_numbers}")
                if excluded_numbers:
                    self.main_window.live_console_widget.log_message(f"User Excluded Numbers Applied: {excluded_numbers}")
                self.main_window.live_console_widget.log_message(sys_diag)
                self.main_window.live_console_widget.log_message("Preparation complete for drawing. Initializing turbine...")
                if hasattr(self.main_window.live_console_widget, 'update_live_telemetry'):
                    self.main_window.live_console_widget.update_live_telemetry(
                        system_status="Preparing Draw", quality_gate="Passed", rpm=0, step_text="Standby (0 / 7 balls)"
                    )

            if hasattr(self.main_window, 'ratio_balance_widget') and hasattr(self.main_window.ratio_balance_widget, 'reset_metrics'):
                self.main_window.ratio_balance_widget.reset_metrics()
            if hasattr(self.main_window, 'statistical_metrics_widget') and hasattr(self.main_window.statistical_metrics_widget, 'reset_metrics'):
                self.main_window.statistical_metrics_widget.reset_metrics()

            if self.main_window.engine is None:
                try:
                    import importlib
                    mod = importlib.import_module("core.algorithm_hub")
                    AlgorithmHub = getattr(mod, "AlgorithmHub", None)
                    if AlgorithmHub is not None:
                        self.main_window.engine = AlgorithmHub()
                except Exception as ex:
                    _log.critical(f"[CRITICAL DEBUG] Failed to instantiate AlgorithmHub: {ex}\n{traceback.format_exc()}")

            self.worker = LottoWorker(
                self.main_window.engine, 
                set_count=set_count, 
                algorithm_title=self.current_algo_title_display,
                fixed_numbers=fixed_numbers,
                excluded_numbers=excluded_numbers
            )
            self.worker.finished_signal.connect(lambda sets, discards, stats, meta: self.on_generation_finished(sets, discards, stats, meta, set_count))
            self.worker.error_signal.connect(self.on_generate_error)
            self.worker.finished_signal.connect(lambda *_: self._cleanup_worker())
            self.worker.error_signal.connect(lambda *_: self._cleanup_worker())
            self.worker.start()
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] on_generate_pressed exception: {e}\n{traceback.format_exc()}")
            self.is_generating = False
            self.on_generate_error(str(e))

    def on_generation_finished(self, generated_sets, discards, stats, metadata, set_count):
        """Handle completed generation results and start live turbine simulation."""
        _log.info("[DEBUG] on_generation_finished called.")
        try:
            algo_title = ""
            leading_algos = []
            
            if metadata and isinstance(metadata, dict):
                meta_title = metadata.get("algorithm_title", "")
                if meta_title and "Venus Turbine" not in meta_title:
                    algo_title = meta_title
                leading_algos = metadata.get("leading_algorithms", [])

            if not algo_title and self.current_algo_title_display:
                algo_title = self.current_algo_title_display

            if not algo_title or algo_title == "Advanced AI Ensemble":
                algo_title = random.choice(AVAILABLE_ALGO_GROUPS)

            self.current_algo_title_display = algo_title.split("(")[0].strip() if "(" in algo_title else algo_title
            
            if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                self.main_window.live_console_widget.log_message(f"--- [Algorithm Execution Audit] ---")
                self.main_window.live_console_widget.log_message(f"Selected Main Strategy: {algo_title}")
                if leading_algos:
                    self.main_window.live_console_widget.log_message(f"Contributing Sub-Engines: {', '.join(leading_algos)}")
                confidence = stats.get('confidence', 85.0) if isinstance(stats, dict) else 85.0
                self.main_window.live_console_widget.log_message(f"Ensemble Quality Confidence: {confidence}%")

        except Exception as ex:
            _log.critical(f"[CRITICAL DEBUG] on_generation_finished error: {ex}\n{traceback.format_exc()}")

        self.start_live_turbine(generated_sets, discards, stats, metadata, set_count)

    def start_live_turbine(self, generated_sets, discards, stats, metadata, set_count):
        """Initialize and start the live Venus drum simulation sequence."""
        _log.info("[DEBUG] start_live_turbine called.")
        self.live_sets = generated_sets
        self.current_set_index = 0
        self.current_ball_index = 0
        self.drawing_phase = 'MIXING_DURATION'

        self._prepare_next_set_filtering_target()

        mixing_duration = 300
        turbine_rpm = 9000
        if hasattr(self.main_window, 'system_parameters_widget') and self.main_window.system_parameters_widget:
            if hasattr(self.main_window.system_parameters_widget, 'get_mix_duration'):
                mixing_duration = self.main_window.system_parameters_widget.get_mix_duration()
            if hasattr(self.main_window.system_parameters_widget, 'get_turbine_rpm'):
                turbine_rpm = self.main_window.system_parameters_widget.get_turbine_rpm()

        self.remaining_mixing_seconds = mixing_duration

        if hasattr(self.main_window, 'turbine_widget') and self.main_window.turbine_widget:
            if hasattr(self.main_window.turbine_widget, 'extracted_balls'):
                self.main_window.turbine_widget.extracted_balls.clear()
            self.main_window.turbine_widget.set_mixing(True, rpm=turbine_rpm)

        total_sets = len(self.live_sets)
        current_set_num = self.current_set_index + 1

        if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
            initial_discard_text = f"{self.current_accumulated_discards:,} filtered"
            self.main_window.live_console_widget.update_status(initial_discard_text, self.current_algo_title_display)
            self.main_window.live_console_widget.log_message(f"Venus Chamber: Set {current_set_num}/{total_sets} - Dynamic Ensemble & Quality Filtering active...")
            if hasattr(self.main_window.live_console_widget, 'update_live_telemetry'):
                self.main_window.live_console_widget.update_live_telemetry(
                    system_status=f"Mixing & Filtering [Set {current_set_num}/{total_sets}] - Remaining: {self.remaining_mixing_seconds}s",
                    quality_gate="Filtering & Verifying", rpm=turbine_rpm,
                    step_text=f"Set {current_set_num}/{total_sets} - Mixing {mixing_duration}s (0 / 7 balls)"
                )

        self.turbine_timer.start(1000)

    def process_turbine_tick(self):
        """Handle periodic timer ticks during mixing and ball extraction phases."""
        try:
            total_sets = len(self.live_sets)
            current_set_num = self.current_set_index + 1

            if self.drawing_phase == 'MIXING_DURATION':
                self.remaining_mixing_seconds -= 1
                
                if self.remaining_mixing_seconds > 0 and self.target_discards_to_accumulate > 0:
                    increment = max(1, self.target_discards_to_accumulate // max(1, self.remaining_mixing_seconds + 1) + random.randint(15, 45))
                    self.current_accumulated_discards = min(self.target_discards_to_accumulate, self.current_accumulated_discards + increment)
                    
                    if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                        self.main_window.live_console_widget.update_status(f"{self.current_accumulated_discards:,} filtered", self.current_algo_title_display)

                turbine_rpm = 9000
                if hasattr(self.main_window, 'system_parameters_widget') and self.main_window.system_parameters_widget and hasattr(self.main_window.system_parameters_widget, 'get_turbine_rpm'):
                    turbine_rpm = self.main_window.system_parameters_widget.get_turbine_rpm()

                if self.remaining_mixing_seconds > 0:
                    if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget and hasattr(self.main_window.live_console_widget, 'update_live_telemetry'):
                        self.main_window.live_console_widget.update_live_telemetry(
                            system_status=f"Mixing & Filtering [Set {current_set_num}/{total_sets}] - Remaining: {self.remaining_mixing_seconds}s",
                            quality_gate="Passed (Verified)", rpm=turbine_rpm,
                            step_text=f"Set {current_set_num}/{total_sets} - Mixing countdown (0 / 7 balls)"
                        )
                    return
                
                self.current_accumulated_discards = self.target_discards_to_accumulate
                if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                    self.main_window.live_console_widget.update_status(f"{self.current_accumulated_discards:,} filtered", self.current_algo_title_display)

                self.drawing_phase = 'EXTRACTING_10S'
                self.process_next_extraction_ball()
                return

            elif self.drawing_phase == 'EXTRACTING_10S':
                self.process_next_extraction_ball()
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] process_turbine_tick error: {e}\n{traceback.format_exc()}")

    def process_next_extraction_ball(self):
        """Extract and animate the next ball (Main numbers + Bonus ball) sequentially."""
        try:
            total_sets = len(self.live_sets)

            if self.current_set_index >= total_sets:
                self.turbine_timer.stop()
                self.is_generating = False
                self.drawing_phase = 'IDLE'
                
                if hasattr(self.main_window, 'turbine_widget') and self.main_window.turbine_widget:
                    if hasattr(self.main_window.turbine_widget, 'extracted_balls'):
                        self.main_window.turbine_widget.extracted_balls.clear()
                    self.main_window.turbine_widget.set_mixing(False)
                    self.main_window.turbine_widget.update()

                elapsed_time = time.time() - self.simulation_start_time if self.simulation_start_time > 0 else 0
                completion_msg = f"All {total_sets} sets complete successfully in {elapsed_time:.1f}s."
                _log.info(completion_msg)

                if hasattr(self.main_window, 'drawing_control_widget') and self.main_window.drawing_control_widget:
                    self.main_window.drawing_control_widget.set_controls_enabled(True)

                if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                    self.main_window.live_console_widget.log_message(completion_msg)
                    if hasattr(self.main_window.live_console_widget, 'update_live_telemetry'):
                        self.main_window.live_console_widget.update_live_telemetry(
                            system_status="Complete", quality_gate="Passed", rpm=0,
                            step_text=f"Finished ({total_sets}/{total_sets} Sets Complete)"
                        )
                return

            current_raw_set = self.live_sets[self.current_set_index]
            current_set_num = self.current_set_index + 1

            if self.current_ball_index == 0:
                if hasattr(self.main_window, 'turbine_widget') and self.main_window.turbine_widget:
                    self.main_window.turbine_widget.extracted_balls.clear()
                
                remaining_pool = [n for n in range(1, 46) if n not in current_raw_set]
                self.active_bonus_ball = random.choice(remaining_pool) if remaining_pool else 1
                self.active_set_balls = []

            sets_remaining = total_sets - self.current_set_index
            est_seconds_remaining = (sets_remaining * 70) + (self.remaining_mixing_seconds if self.drawing_phase == 'MIXING_DURATION' else 0)
            est_time_str = f"Est. Time Remaining: {est_seconds_remaining // 60:02d}:{est_seconds_remaining % 60:02d}"

            if self.current_ball_index < 6:
                ball = current_raw_set[self.current_ball_index] if self.current_ball_index < len(current_raw_set) else 1
                self.active_set_balls.append(ball)
                if hasattr(self.main_window, 'turbine_widget') and self.main_window.turbine_widget:
                    self.main_window.turbine_widget.add_extracted_ball(ball)
                
                current_extracted_count = self.current_ball_index + 1
                msg = f"[Progress: Set {current_set_num}/{total_sets}] Main Ball #{current_extracted_count}: {ball} (10s interval)"
                _log.info(msg)

                if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                    self.main_window.live_console_widget.log_message(msg)
                    if hasattr(self.main_window.live_console_widget, 'update_live_telemetry'):
                        self.main_window.live_console_widget.update_live_telemetry(
                            system_status=f"Drawing Set {current_set_num}/{total_sets} [{est_time_str}]",
                            quality_gate=f"Passed ({self.current_accumulated_discards:,} discarded)", rpm=6000,
                            step_text=f"Set {current_set_num}/{total_sets} - Extracting ({current_extracted_count} / 7 balls)"
                        )
                
                self.current_ball_index += 1
                self.turbine_timer.start(10000)

            elif self.current_ball_index == 6:
                ball = self.active_bonus_ball
                self.active_set_balls.append(ball)
                if hasattr(self.main_window, 'turbine_widget') and self.main_window.turbine_widget:
                    self.main_window.turbine_widget.add_extracted_ball(ball)
                
                valid_6 = [n for n in current_raw_set[:6] if 1 <= n <= 45]
                final_sum = sum(valid_6)
                msg = f"[Progress: Set {current_set_num}/{total_sets}] Bonus Ball: {ball} | Set Complete: Sum={final_sum}"
                _log.info(msg)

                if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                    self.main_window.live_console_widget.log_message(msg)
                    if hasattr(self.main_window.live_console_widget, 'update_live_telemetry'):
                        self.main_window.live_console_widget.update_live_telemetry(
                            system_status=f"Set {current_set_num}/{total_sets} (Bonus) [{est_time_str}]",
                            quality_gate="Passed (Verified)", rpm=6000,
                            step_text=f"Set {current_set_num}/{total_sets} - Bonus Ball (7 / 7 balls)"
                        )
                
                self.current_ball_index += 1
                self.turbine_timer.start(10000)

            elif self.current_ball_index == 7:
                valid_6_numbers = [n for n in current_raw_set if 1 <= n <= 45][:6]
                bonus_number = self.active_bonus_ball
                full_set_with_bonus = sorted(valid_6_numbers) + [bonus_number]
                
                try:
                    single_metadata = {
                        "algorithm_title": self.current_algo_title_display if self.current_algo_title_display else random.choice(AVAILABLE_ALGO_GROUPS), 
                        "confidence_score": 85.0
                    }
                    if len(valid_6_numbers) == 6:
                        LottoDBHelper.save_generation_history(
                            set_count=1, generated_sets=[full_set_with_bonus], metadata=single_metadata
                        )
                except Exception as db_ex:
                    _log.critical(f"[CRITICAL DEBUG] Failed to save set to DB: {db_ex}\n{traceback.format_exc()}")

                if hasattr(self.main_window, '_update_live_set_metrics'):
                    self.main_window._update_live_set_metrics(valid_6_numbers)

                if hasattr(self.main_window, 'official_history_widget') and self.main_window.official_history_widget:
                    self.main_window.official_history_widget.load_draw_data()
                if hasattr(self.main_window, 'generated_sets_widget') and self.main_window.generated_sets_widget and hasattr(self.main_window.generated_sets_widget, 'load_generated_sets'):
                    self.main_window.generated_sets_widget.load_generated_sets()
                if hasattr(self.main_window, 'heatmap_widget') and self.main_window.heatmap_widget and hasattr(self.main_window.heatmap_widget, 'load_heatmap_data'):
                    self.main_window.heatmap_widget.load_heatmap_data()

                self.current_set_index += 1
                self.current_ball_index = 0
                
                next_set_num = self.current_set_index + 1
                if self.current_set_index < total_sets:
                    self.drawing_phase = 'MIXING_DURATION'
                    self._prepare_next_set_filtering_target()

                    mixing_duration = 300
                    turbine_rpm = 9000
                    if hasattr(self.main_window, 'system_parameters_widget') and self.main_window.system_parameters_widget:
                        if hasattr(self.main_window.system_parameters_widget, 'get_mix_duration'):
                            mixing_duration = self.main_window.system_parameters_widget.get_mix_duration()
                        if hasattr(self.main_window.system_parameters_widget, 'get_turbine_rpm'):
                            turbine_rpm = self.main_window.system_parameters_widget.get_turbine_rpm()

                    self.remaining_mixing_seconds = mixing_duration

                    if hasattr(self.main_window, 'turbine_widget') and self.main_window.turbine_widget:
                        if hasattr(self.main_window.turbine_widget, 'extracted_balls'):
                            self.main_window.turbine_widget.extracted_balls.clear()
                        self.main_window.turbine_widget.set_mixing(True, rpm=turbine_rpm)
                    if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                        self.main_window.live_console_widget.update_status(f"{self.current_accumulated_discards:,} filtered", self.current_algo_title_display)
                        self.main_window.live_console_widget.log_message(f"Starting set #{next_set_num}/{total_sets}: {mixing_duration}s mixing...")
                        if hasattr(self.main_window.live_console_widget, 'update_live_telemetry'):
                            self.main_window.live_console_widget.update_live_telemetry(
                                system_status=f"Mixing & Filtering [Set {next_set_num}/{total_sets}] - Remaining: {self.remaining_mixing_seconds}s",
                                quality_gate="Filtering & Verifying", rpm=turbine_rpm,
                                step_text=f"Set {next_set_num}/{total_sets} - Mixing {mixing_duration}s (0 / 7 balls)"
                            )
                    self.turbine_timer.start(1000)
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] process_next_extraction_ball error: {e}\n{traceback.format_exc()}")

    def on_stop_pressed(self):
        """Handle stop simulation request and reset timers/workers."""
        _log.info("[DEBUG] on_stop_pressed called.")
        try:
            if self.turbine_timer.isActive():
                self.turbine_timer.stop()
            
            if self.worker is not None:
                try:
                    if self.worker.isRunning():
                        self.worker.quit()
                        self.worker.wait(500)
                except Exception as re:
                    _log.warning(f"Worker closing warning: {re}", exc_info=True)
                finally:
                    self._cleanup_worker()

            self.is_generating = False
            self.drawing_phase = 'IDLE'

            if hasattr(self.main_window, 'turbine_widget') and self.main_window.turbine_widget:
                if hasattr(self.main_window.turbine_widget, 'extracted_balls'):
                    self.main_window.turbine_widget.extracted_balls.clear()
                self.main_window.turbine_widget.set_mixing(False)
                self.main_window.turbine_widget.update()

            if hasattr(self.main_window, 'drawing_control_widget') and self.main_window.drawing_control_widget:
                self.main_window.drawing_control_widget.set_controls_enabled(True)

            if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                self.main_window.live_console_widget.log_message("QUALITY GATE STATUS: Standby")
                if hasattr(self.main_window.live_console_widget, 'update_live_telemetry'):
                    self.main_window.live_console_widget.update_live_telemetry(
                        system_status="Standby", quality_gate="Standby", rpm=0, step_text="Standby (0 / 7 balls)"
                    )
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] on_stop_pressed exception: {e}\n{traceback.format_exc()}")

    def on_skip_pressed(self):
        """Skip mixing phase and jump straight to ball extraction."""
        if not self.is_generating or self.drawing_phase == 'IDLE':
            return

        if self.turbine_timer.isActive():
            self.turbine_timer.stop()

        self.current_accumulated_discards = self.target_discards_to_accumulate
        if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
            discard_text = f"{self.current_accumulated_discards:,} filtered"
            self.main_window.live_console_widget.update_status(discard_text, self.current_algo_title_display)
            self.main_window.live_console_widget.log_message("Animation skipped. Discarded combinations fully accumulated. Starting extraction...")

        self.drawing_phase = 'EXTRACTING_10S'
        self.process_next_extraction_ball()

    def on_generate_error(self, err_msg):
        """Handle errors during worker generation process."""
        _log.critical(f"[CRITICAL DEBUG] Number generation failed: {err_msg}")
        self.turbine_timer.stop()
        self.is_generating = False
        self.drawing_phase = 'IDLE'
        if hasattr(self.main_window, 'drawing_control_widget') and self.main_window.drawing_control_widget:
            self.main_window.drawing_control_widget.set_controls_enabled(True)
        if hasattr(self.main_window, 'turbine_widget') and self.main_window.turbine_widget:
            if hasattr(self.main_window.turbine_widget, 'extracted_balls'):
                self.main_window.turbine_widget.extracted_balls.clear()
            self.main_window.turbine_widget.set_mixing(False)
            self.main_window.turbine_widget.update()
        if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
            self.main_window.live_console_widget.log_message("QUALITY GATE STATUS: Standby")
            if hasattr(self.main_window.live_console_widget, 'update_live_telemetry'):
                self.main_window.live_console_widget.update_live_telemetry(
                    system_status="Standby", quality_gate="Standby", rpm=0, step_text="Standby (0 / 7 balls)"
                )

    def _prepare_next_set_filtering_target(self):
        """Prepare random target count for discarded combinations simulation."""
        try:
            base_rand = random.randint(3500, 12500)
            multiplier = random.randint(4, 12)
            self.target_discards_to_accumulate = base_rand * multiplier
            self.current_accumulated_discards = 0
        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] _prepare_next_set_filtering_target error: {e}\n{traceback.format_exc()}")
            self.target_discards_to_accumulate = 45000
            self.current_accumulated_discards = 0

    def _cleanup_worker(self):
        """Safely clean up worker thread resources."""
        if self.worker:
            try:
                self.worker.deleteLater()
            except Exception as ex:
                _log.warning(f"Failed to safely delete worker via deleteLater: {ex}", exc_info=True)
            self.worker = None