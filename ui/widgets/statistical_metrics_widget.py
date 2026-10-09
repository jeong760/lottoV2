# -*- coding: utf-8 -*-
# ui/widgets/statistical_metrics_widget.py
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("StatisticalMetricsWidget")

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt


class StatisticalMetricsWidget(QGroupBox):
    """
    Dedicated widget for displaying statistical metrics (SUM Total and AC Complexity)
    derived exclusively from user-generated simulation sets, rendered with visual gauge bars.
    """
    def __init__(self, title="📊 Statistical Metrics", parent=None):
        super().__init__(title, parent)
        self.current_sum = 0
        self.current_ac = 0.0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # 1. SUM Total Gauge Layout (Lotto sum range: 21 ~ 255)
        sum_container_layout = QVBoxLayout()
        sum_container_layout.setSpacing(4)

        self.lbl_sum = QLabel("■ SUM Total : -")
        self.lbl_sum.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 11px;")

        self.sum_progress = QProgressBar()
        self.sum_progress.setRange(21, 255)
        self.sum_progress.setValue(0)
        self.sum_progress.setTextVisible(False)
        self.sum_progress.setFixedHeight(12)
        self.sum_progress.setStyleSheet("""
            QProgressBar {
                background-color: #dfe4ea;
                border-radius: 6px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #d35400;
                border-radius: 6px;
            }
        """)
        sum_container_layout.addWidget(self.lbl_sum)
        sum_container_layout.addWidget(self.sum_progress)
        layout.addLayout(sum_container_layout)

        # 2. AC Complexity Gauge Layout (Typical AC value range: 0 ~ 10)
        ac_container_layout = QVBoxLayout()
        ac_container_layout.setSpacing(4)

        self.lbl_ac = QLabel("■ AC Complexity : -")
        self.lbl_ac.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 11px;")

        self.ac_progress = QProgressBar()
        self.ac_progress.setRange(0, 10)
        self.ac_progress.setValue(0)
        self.ac_progress.setTextVisible(False)
        self.ac_progress.setFixedHeight(12)
        self.ac_progress.setStyleSheet("""
            QProgressBar {
                background-color: #dfe4ea;
                border-radius: 6px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #16a085;
                border-radius: 6px;
            }
        """)
        ac_container_layout.addWidget(self.lbl_ac)
        ac_container_layout.addWidget(self.ac_progress)
        layout.addLayout(ac_container_layout)

        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                margin-top: 8px;
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
            }
        """)
        _log.info("StatisticalMetricsWidget initialized successfully.")

    def reset_metrics(self):
        """Resets the widget to an empty state before simulation begins."""
        self.current_sum = 0
        self.current_ac = 0.0
        self.sum_progress.setValue(0)
        self.ac_progress.setValue(0)
        self.lbl_sum.setText("■ SUM Total : Waiting...")
        self.lbl_ac.setText("■ AC Complexity : Waiting...")

    def update_metric(self, sum_val: int, ac_val: float):
        """Updates the SUM and AC metrics dynamically in real-time when a set completes."""
        try:
            self.current_sum = sum_val
            self.current_ac = ac_val

            sum_status = "Optimal" if 100 <= sum_val <= 170 else "Out"
            ac_status = "Valid" if ac_val >= 7.0 else "Low"

            self.sum_progress.setValue(min(max(sum_val, 21), 255))
            self.lbl_sum.setText(f"■ SUM Total : {sum_val:,} ({sum_status})")

            self.ac_progress.setValue(min(max(int(round(ac_val)), 0), 10))
            self.lbl_ac.setText(f"■ AC Complexity : {ac_val:.1f} pts ({ac_status})")
        except Exception as e:
            _log.error(f"Failed to update statistical metrics: {e}")

    def update_sum_value(self, sum_val: int):
        """Compatibility method for individual sum updates from main window."""
        self.update_metric(sum_val, self.current_ac)

    def update_ac_value(self, ac_val: float):
        """Compatibility method for individual AC updates from main window."""
        self.update_metric(self.current_sum, ac_val)

    def update_from_numbers(self, numbers: list):
        """Calculates and updates SUM and AC complexity directly from a completed set's 6-number list."""
        try:
            if not numbers or len(numbers) < 6:
                return
            base_nums = sorted([int(n) for n in numbers[:6]])
            
            sum_val = sum(base_nums)

            differences = set()
            for i in range(len(base_nums)):
                for j in range(i + 1, len(base_nums)):
                    differences.add(abs(base_nums[i] - base_nums[j]))
            
            ac_val = float(len(differences) - 5)
            if ac_val < 0.0:
                ac_val = 0.0

            self.update_metric(sum_val, ac_val)
        except Exception as e:
            _log.error(f"Failed to update statistical metrics from numbers: {e}")

    def update_chi_square_metrics(self, chi2_data: dict):
        """Compatibility hook for controller-side chi-square pushes."""
        try:
            if not isinstance(chi2_data, dict):
                return
            p_val = float(chi2_data.get("p_value", 1.0))
            status = "Uniform" if bool(chi2_data.get("is_uniformly_distributed", True)) else "Biased"
            self.setToolTip(f"Chi-square p-value: {p_val:.4f} ({status})")
        except Exception as e:
            _log.error(f"Failed to update chi-square tooltip: {e}")