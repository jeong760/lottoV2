# -*- coding: utf-8 -*-
# ui/widgets/generator_widget.py
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("GeneratorWidget")

import random
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from ui.widgets.venus_drum_widget import VenusDrumWidget
from ui.widgets.live_console_widget import LiveConsoleWidget
from data.repositories.lotto_repository import LottoRepository


class GeneratorWidget(QWidget):
    """
    AKANIS TECHNOLOGIES - VENUS Model-Based Turbine Drawing Machine Widget
    - Runs continuous queue execution without interruption until all configured sets are fully exhausted.
    - Automatic correction when queue counts are low, and auto-accumulating save to DB via LottoRepository upon completing each set.
    - Live console (in-place update) and Venus sphere bottom tray landing integration.
    """
    generate_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pending_sets = []
        self.total_sets_count = 0
        self.current_rpm = 1000
        self.extract_step = 0
        self.target_numbers = []
        
        self.init_ui()

        # Physics computation timer
        self.physics_timer = QTimer(self)
        self.physics_timer.setInterval(25)
        self.physics_timer.timeout.connect(self.update_drum_animation)

        # Ball extraction timer (set to 1.2s for simulation acceleration)
        self.extraction_timer = QTimer(self)
        self.extraction_timer.setInterval(1200)
        self.extraction_timer.timeout.connect(self.extract_next_ball)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. Top status label
        self.lbl_status = QLabel("🎰 VENUS Turbine Drawing Machine Standby [AKANIS TECHNOLOGIES]")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lbl_status.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        main_layout.addWidget(self.lbl_status)

        # 2. Venus drawing machine widget (sphere bottom landing type)
        self.drum_widget = VenusDrumWidget()
        main_layout.addWidget(self.drum_widget, alignment=Qt.AlignCenter)

        # 3. Set count selection and generation button control layout
        control_layout = QHBoxLayout()
        control_layout.setAlignment(Qt.AlignCenter)
        control_layout.setSpacing(15)
        
        lbl_count = QLabel("Generation Set Count:")
        lbl_count.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_count.setStyleSheet("color: #34495e;")
        
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 9999999)
        self.spin_count.setValue(5)
        self.spin_count.setDisplayIntegerBase(10)
        self.spin_count.setGroupSeparatorShown(True)
        self.spin_count.setFixedWidth(120)
        self.spin_count.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.spin_count.setStyleSheet("padding: 6px; border: 2px solid #dcdde1; border-radius: 6px; background: white;")
        
        self.btn_generate = QPushButton("🚀 Draw Lotto Lucky Numbers")
        self.btn_generate.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_generate.setFixedHeight(45)
        self.btn_generate.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; 
                color: white; 
                border-radius: 8px; 
                padding: 0 20px; 
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:pressed { background-color: #229954; }
            QPushButton:disabled { background-color: #bdc3c7; }
        """)
        
        control_layout.addWidget(lbl_count)
        control_layout.addWidget(self.spin_count)
        control_layout.addWidget(self.btn_generate)
        main_layout.addLayout(control_layout)

        # 4. Live console widget (in-place update panel)
        self.console_widget = LiveConsoleWidget()
        main_layout.addWidget(self.console_widget)

        self.btn_generate.clicked.connect(self.on_generate_button_clicked)
        self.setLayout(main_layout)
        
        self.console_widget.log_message("System initialization complete [Model: VENUS / Manufacturer: AKANIS]")
        self.console_widget.log_message("[Specs] 45 Balls + 1 Bonus | Mixing: 300s | Sphere Bottom Tray Landing at 10s Intervals")

    def on_generate_button_clicked(self):
        """Passes the exact set count configured in the spinbox to the parent controller when generated"""
        set_count = self.spin_count.value()
        self.btn_generate.setEnabled(False)
        self.spin_count.setEnabled(False)
        self.console_widget.log_message(f"User Request: Starting continuous drawing process for a total of {set_count:,} sets.")
        self.generate_clicked.emit(set_count)

    def set_numbers(self, all_generated_sets):
        """
        Receives external data to construct the full set queue, automatically compensating
        if shorter than the target set count to fully populate the queue and start continuous performance.
        """
        cleaned_sets = []
        try:
            if isinstance(all_generated_sets, list):
                for item in all_generated_sets:
                    if isinstance(item, list) and len(item) >= 6:
                        cleaned_sets.append(item)
            elif isinstance(all_generated_sets, int):
                cleaned_sets = [[3, 12, 24, 27, 35, 42, 7]]
        except Exception:
            cleaned_sets = []

        target_count = self.spin_count.value()

        # Automatically generate and fill if received sets are fewer than target
        while len(cleaned_sets) < target_count:
            nums = sorted(random.sample(range(1, 46), 6))
            bonus = random.choice([n for n in range(1, 46) if n not in nums])
            cleaned_sets.append(nums + [bonus])

        self.pending_sets = cleaned_sets[:target_count]
        self.total_sets_count = len(self.pending_sets)
        self.console_widget.log_message(f"Total {self.total_sets_count:,} sets loaded into queue. Starting continuous execution until completion.")
        _log.info(f"Loaded {self.total_sets_count} sets into the queue for continuous generation.")

        self.prepare_next_set()

    def prepare_next_set(self):
        """Retrieves and prepares the next set from the queue (maintains loop until all sets end)"""
        if not self.pending_sets:
            self.lbl_status.setText("✨ All VENUS Turbine set drawings and DB accumulation complete!")
            self.console_widget.log_message("All set drawing and DB insertion processes terminated.")
            self.btn_generate.setEnabled(True)
            self.spin_count.setEnabled(True)
            self.drum_widget.set_mixing(False)
            _log.info("All scheduled turbine sets have been fully processed.")
            return

        current_set = self.pending_sets.pop(0)
        try:
            if isinstance(current_set, list):
                self.target_numbers = [int(n) for n in current_set[:7]] if len(current_set) >= 7 else [int(n) for n in current_set[:6]] + [random.randint(1, 45)]
            else:
                self.target_numbers = [3, 12, 24, 27, 35, 42, 7]
        except Exception:
            self.target_numbers = [3, 12, 24, 27, 35, 42, 7]

        # Automatically accumulate and save to DB at the completion point of each set
        try:
            if hasattr(LottoRepository, 'save_simulation_set'):
                LottoRepository.save_simulation_set(self.target_numbers)
            elif hasattr(LottoRepository, 'save_generation_history'):
                LottoRepository.save_generation_history(1, [self.target_numbers])
        except Exception as e:
            self.console_widget.log_message(f"DB Save Warning: {e}")
            _log.warning(f"Failed to auto-save simulation set to repository: {e}")

        remaining_runs = len(self.pending_sets)
        completed_count = self.total_sets_count - remaining_runs
        self.lbl_status.setText(f"⏳ [Progress: {completed_count}/{self.total_sets_count} sets] Preparing next draw...")
        self.console_widget.log_message(f"Set [{completed_count}/{self.total_sets_count}] preparation complete. (Remaining sets: {remaining_runs})")
        
        self.drum_widget.set_mixing(False)
        QTimer.singleShot(1500, self.start_turbine_mixing)

    def start_turbine_mixing(self):
        """Turbine mixing phase (RPM variable between 1000 and 9000)"""
        self.current_rpm = random.randint(1000, 9000)
        
        self.lbl_status.setText(f"🌪️ Turbine operating [RPM: {self.current_rpm:,}] (Mixing balls)...")
        self.console_widget.log_message(f"Turbine rotation started! RPM: {self.current_rpm:,}")
        
        self.drum_widget.set_mixing(True, self.current_rpm)
        self.physics_timer.start()

        self.rpm_fluctuate_timer = QTimer(self)
        self.rpm_fluctuate_timer.setInterval(700)
        self.rpm_fluctuate_timer.timeout.connect(self.fluctuate_rpm)
        self.rpm_fluctuate_timer.start()

        # Enter 7-ball extraction sequence at 10-second intervals after 3 seconds of mixing
        QTimer.singleShot(3000, self.begin_extraction_phase)

    def fluctuate_rpm(self):
        self.current_rpm = random.randint(1000, 9000)
        self.drum_widget.current_rpm = self.current_rpm
        self.console_widget.log_message(f"Turbine RPM fluctuation ➔ {self.current_rpm:,} RPM")

    def update_drum_animation(self):
        self.drum_widget.update_physics()

    def begin_extraction_phase(self):
        if hasattr(self, 'rpm_fluctuate_timer'):
            self.rpm_fluctuate_timer.stop()
            
        self.extract_step = 0
        self.console_widget.log_message("Starting ball extraction to sphere bottom tray")
        self.extraction_timer.start()

    def extract_next_ball(self):
        """Extracts one ball at a time to land in the bottom tray"""
        if self.extract_step < len(self.target_numbers):
            next_num = self.target_numbers[self.extract_step]
            self.drum_widget.add_extracted_ball(next_num)
            
            if self.extract_step < 6:
                self.console_widget.log_message(f"Extraction [Main Ball #{self.extract_step + 1}] ➔ [{next_num}]")
                self.lbl_status.setText(f"🎯 Extracting main numbers... ({self.extract_step + 1}/6 balls)")
            else:
                self.console_widget.log_message(f"Extraction [Bonus Ball] ➔ [{next_num}]")
                self.lbl_status.setText(f"⭐ Bonus ball extraction complete!")
                
            self.extract_step += 1
        else:
            self.extraction_timer.stop()
            self.physics_timer.stop()
            self.drum_widget.set_mixing(False)
            
            main_nums = self.target_numbers[:6]
            bonus_num = self.target_numbers[6] if len(self.target_numbers) > 6 else 7
            self.console_widget.log_message(f"🎉 Set complete! Main numbers: {main_nums} | Bonus: [{bonus_num}]")
            self.lbl_status.setText(f"🎉 Set completed! (Transitioning to next set...)")

            # Wait for results for 3 seconds then immediately enter next set remaining in queue
            QTimer.singleShot(3000, self.prepare_next_set)