# -*- coding: utf-8 -*-
# ui/widgets/venus_config_widget.py
import sys
import os
import logging

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("VenusConfigWidget")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QSpinBox, QComboBox, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

class VenusConfigWidget(QWidget):
    """Widget for configuring VENUS physical drawing machine simulations and algorithm hybrid weight policies."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. Turbine physical simulation configuration group
        group_turbine = QGroupBox("🌀 VENUS Turbine Physical Simulation Environment Settings")
        turbine_layout = QVBoxLayout(group_turbine)
        turbine_layout.setSpacing(8)

        # Ball mixing rotation speed setting
        row1 = QHBoxLayout()
        lbl_speed = QLabel("Ball Mixing Rotation Speed (RPM):")
        self.spin_speed = QSpinBox()
        self.spin_speed.setRange(50, 500)
        self.spin_speed.setValue(120)
        self.spin_speed.setSingleStep(10)
        row1.addWidget(lbl_speed)
        row1.addWidget(self.spin_speed)
        row1.addStretch(1)

        # Ball discharge air pressure intensity setting
        row2 = QHBoxLayout()
        lbl_pressure = QLabel("Drawing Blower Air Pressure (PSI):")
        self.spin_pressure = QSpinBox()
        self.spin_pressure.setRange(10, 100)
        self.spin_pressure.setValue(45)
        row2.addWidget(lbl_pressure)
        row2.addWidget(self.spin_pressure)
        row2.addStretch(1)

        turbine_layout.addLayout(row1)
        turbine_layout.addLayout(row2)

        # 2. Ensemble algorithm weight configuration group
        group_algo = QGroupBox("⚙️ AI Ensemble and Filtering Weight Policy Settings")
        algo_layout = QVBoxLayout(group_algo)
        algo_layout.setSpacing(8)

        row3 = QHBoxLayout()
        lbl_strategy = QLabel("Default Recommendation Algorithm Mode:")
        self.combo_strategy = QComboBox()
        self.combo_strategy.addItems([
            "Markov Chain & Monte Carlo Hybrid (Recommended)",
            "Deep Learning LSTM Trend Predictor",
            "Hot/Cold Statistical Balancing",
            "Pure Random Physics Simulation"
        ])
        row3.addWidget(lbl_strategy)
        row3.addWidget(self.combo_strategy)
        row3.addStretch(1)

        algo_layout.addLayout(row3)

        # Save button
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 Save and Apply Settings")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2471a3;
            }
        """)
        self.btn_save.clicked.connect(self.on_save_clicked)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_save)

        main_layout.addWidget(group_turbine)
        main_layout.addWidget(group_algo)
        main_layout.addLayout(btn_layout)
        main_layout.addStretch(1)

        self.setStyleSheet("background-color: #f8f9fa;")
        _log.info("VenusConfigWidget initialized successfully.")

    def get_turbine_rpm(self) -> int:
        """Get current turbine rotation speed."""
        try:
            return self.spin_speed.value() * 15  # Scale factor mapping to simulation RPM
        except Exception:
            return 9000

    def get_mix_duration(self) -> int:
        """Get mix duration based on air pressure setting (seconds)."""
        try:
            return int(self.spin_pressure.value() * 3)
        except Exception:
            return 300

    def get_selected_algorithm(self) -> str:
        """Get currently selected algorithm strategy."""
        try:
            return self.combo_strategy.currentText()
        except Exception:
            return "Markov Chain & Monte Carlo Hybrid"

    def on_save_clicked(self):
        speed = self.spin_speed.value()
        pressure = self.spin_pressure.value()
        strategy = self.combo_strategy.currentText()
        
        _log.info(f"VENUS configuration updated -> Speed: {speed}RPM, Pressure: {pressure}PSI, Strategy: {strategy}")
        QMessageBox.information(
            self, 
            "Settings Saved Successfully", 
            f"VENUS turbine and AI algorithm configurations have been applied successfully!\n\n• Rotation Speed: {speed} RPM\n• Air Pressure: {pressure} PSI\n• Algorithm: {strategy}"
        )