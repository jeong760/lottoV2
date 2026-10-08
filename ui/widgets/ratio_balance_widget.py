# -*- coding: utf-8 -*-
# ui/widgets/ratio_balance_widget.py
import sys
import os
import logging

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("RatioBalanceWidget")

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class RatioBalanceWidget(QGroupBox):
    """
    Dedicated widget for displaying ratio balance metrics (Odd/Even and High/Low distribution)
    derived exclusively from user-generated simulation sets, rendered with multi-color visual progress bars.
    """
    def __init__(self, title="📊 Ratio Balance Metrics", parent=None):
        super().__init__(title, parent)
        self.current_oe = "-"
        self.current_hl = "-"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # 1. Odd / Even Progress Bar Layout (Multi-color dual gradient look via stylesheet & custom rendering)
        oe_container_layout = QVBoxLayout()
        oe_container_layout.setSpacing(4)
        
        self.lbl_odd_even = QLabel("■ Odd / Even Ratio : -")
        self.lbl_odd_even.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 11px;")
        
        self.oe_progress = QProgressBar()
        self.oe_progress.setRange(0, 6)
        self.oe_progress.setValue(0)
        self.oe_progress.setTextVisible(False)
        self.oe_progress.setFixedHeight(12)
        # Multi-color tone: Blue accent gradient for Odd/Even
        self.oe_progress.setStyleSheet("""
            QProgressBar {
                background-color: #dfe4ea;
                border-radius: 6px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop: 0 #1b1464, stop: 0.5 #2980b9, stop: 1 #00cec9);
                border-radius: 6px;
            }
        """)
        oe_container_layout.addWidget(self.lbl_odd_even)
        oe_container_layout.addWidget(self.oe_progress)
        layout.addLayout(oe_container_layout)

        # 2. High / Low Progress Bar Layout
        hl_container_layout = QVBoxLayout()
        hl_container_layout.setSpacing(4)

        self.lbl_high_low = QLabel("■ High / Low Ratio : -")
        self.lbl_high_low.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 11px;")

        self.hl_progress = QProgressBar()
        self.hl_progress.setRange(0, 6)
        self.hl_progress.setValue(0)
        self.hl_progress.setTextVisible(False)
        self.hl_progress.setFixedHeight(12)
        # Multi-color tone: Warm Orange & Coral Red accent gradient for High/Low
        self.hl_progress.setStyleSheet("""
            QProgressBar {
                background-color: #dfe4ea;
                border-radius: 6px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                            stop: 0 #e67e22, stop: 0.6 #e74c3c, stop: 1 #f1c40f);
                border-radius: 6px;
            }
        """)
        hl_container_layout.addWidget(self.lbl_high_low)
        hl_container_layout.addWidget(self.hl_progress)
        layout.addLayout(hl_container_layout)

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
        _log.info("RatioBalanceWidget initialized successfully.")

    def reset_metrics(self):
        """Resets the widget to an empty state before simulation begins."""
        self.current_oe = "-"
        self.current_hl = "-"
        self.oe_progress.setValue(0)
        self.hl_progress.setValue(0)
        self.lbl_odd_even.setText("■ Odd / Even Ratio : Waiting...")
        self.lbl_high_low.setText("■ High / Low Ratio : Waiting...")

    def update_data(self, ratio_stats: dict, total: int = 1):
        """Updates the ratio balance metrics dynamically from generated simulation history."""
        try:
            if not isinstance(ratio_stats, dict):
                return

            oe_dist = ratio_stats.get("odd_even_distribution", {})
            hl_dist = ratio_stats.get("high_low_distribution", {})

            oe_text = list(oe_dist.keys())[0] if oe_dist else self.current_oe
            hl_text = list(hl_dist.keys())[0] if hl_dist else self.current_hl

            self.current_oe = oe_text
            self.current_hl = hl_text

            if ":" in oe_text:
                parts = oe_text.split(":")
                odds = int(parts[0])
                self.oe_progress.setValue(odds)

            self.lbl_odd_even.setText(f"■ Odd / Even Ratio : {oe_text}")

            if ":" in hl_text:
                parts = hl_text.split(":")
                highs = int(parts[0])
                self.hl_progress.setValue(highs)

            self.lbl_high_low.setText(f"■ High / Low Ratio : {hl_text}")
        except Exception as e:
            _log.error(f"Failed to update ratio balance data: {e}")

    def update_ratio(self, odds: int, evens: int):
        """Compatibility method for direct ratio updates from main window."""
        oe_str = f"{odds}:{evens}"
        self.current_oe = oe_str
        self.oe_progress.setValue(odds)
        self.lbl_odd_even.setText(f"■ Odd / Even Ratio : {oe_str}")

    def update_from_numbers(self, numbers: list):
        """Calculates and updates ratios directly from a completed set's 6-number list."""
        try:
            if not numbers or len(numbers) < 6:
                return
            base_nums = numbers[:6]
            odds = sum(1 for n in base_nums if n % 2 != 0)
            evens = 6 - odds
            oe_str = f"{odds}:{evens}"

            lows = sum(1 for n in base_nums if 1 <= n <= 22)
            highs = 6 - lows
            hl_str = f"{lows}:{highs}"

            self.current_oe = oe_str
            self.current_hl = hl_str

            self.oe_progress.setValue(odds)
            self.lbl_odd_even.setText(f"■ Odd / Even Ratio : {oe_str}")

            self.hl_progress.setValue(highs)
            self.lbl_high_low.setText(f"■ High / Low Ratio : {hl_str}")
        except Exception as e:
            _log.error(f"Failed to update ratio balance from numbers: {e}")

    def update_metric(self, *args, **kwargs):
        """Flexible metric receiver hook matching main window updates."""
        if args and isinstance(args[0], (list, tuple)):
            self.update_from_numbers(args[0])
        elif 'numbers' in kwargs:
            self.update_from_numbers(kwargs['numbers'])
        else:
            pass