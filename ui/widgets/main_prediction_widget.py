# -*- coding: utf-8 -*-
# ui/widgets/main_prediction_widget.py
import sys
import os
import logging

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("MainPredictionWidget")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class LottoBallLabel(QLabel):
    """Custom styled official lotto ball widget with gradient background and bold number."""
    def __init__(self, number: int = 1, parent=None):
        super().__init__(str(number).zfill(2), parent)
        self.setFixedSize(42, 42)
        self.setAlignment(Qt.AlignCenter)
        self.update_number(number)

    def update_number(self, num: int):
        """Updates the ball number and applies the correct official color band style."""
        self.setText(str(num).zfill(2))
        self.setStyleSheet(self._get_ball_stylesheet(num))

    def _get_ball_stylesheet(self, num: int):
        if 1 <= num <= 10:
            bg, text_color = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f1c40f, stop:1 #d4ac0d)", "#2c3e50"
        elif 11 <= num <= 20:
            bg, text_color = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5499c7, stop:1 #2471a3)", "#ffffff"
        elif 21 <= num <= 30:
            bg, text_color = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ec7063, stop:1 #b03a2e)", "#ffffff"
        elif 31 <= num <= 40:
            bg, text_color = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #85929e, stop:1 #34495e)", "#ffffff"
        else:
            bg, text_color = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #58d68d, stop:1 #1e8449)", "#ffffff"

        return f"""
            QLabel {{
                background: {bg};
                color: {text_color};
                font-weight: bold;
                font-size: 15px;
                border-radius: 21px;
                border: 1px solid rgba(0, 0, 0, 0.2);
            }}
        """


class MetricCard(QFrame):
    """Individual metric card representing AI score, confidence, rank, etc."""
    def __init__(self, title: str, value: str, value_color: str = "#2c3e50", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(68)

        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dcdde1;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        self.lbl_title = QLabel(title)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("font-size: 10px; color: #7f8c8d; font-weight: bold; background: transparent; border: none;")

        self.lbl_value = QLabel(value)
        self.lbl_value.setAlignment(Qt.AlignCenter)
        self.lbl_value.setStyleSheet(f"font-size: 14px; color: {value_color}; font-weight: bold; background: transparent; border: none;")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

    def set_value(self, value: str, color: str = None):
        self.lbl_value.setText(str(value))
        if color:
            self.lbl_value.setStyleSheet(f"font-size: 14px; color: {color}; font-weight: bold; background: transparent; border: none;")


class MainPredictionWidget(QFrame):
    """
    Main Prediction Dashboard Widget featuring official lotto balls, set title badge,
    and 5 inline analytical metric cards matching the light dashboard design.
    Fully supports dynamic data binding via update_prediction_data().
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # Light Theme Card Styling matching Main Dashboard
        self.setStyleSheet("""
            MainPredictionWidget {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 8px;
            }
        """)

        # 1. Header Title: MAIN PREDICTION
        title_lbl = QLabel("MAIN PREDICTION")
        title_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #7f8c8d; letter-spacing: 1px; border: none; background: transparent;")
        main_layout.addWidget(title_lbl, alignment=Qt.AlignLeft)

        # 2. Lotto Balls Row (Centered)
        balls_layout = QHBoxLayout()
        balls_layout.setContentsMargins(0, 4, 0, 4)
        balls_layout.setSpacing(10)
        balls_layout.addStretch()

        # Initialize with default placeholder numbers (will be updated dynamically)
        initial_numbers = [3, 11, 17, 28, 35, 44]
        self.ball_labels = []
        for num in initial_numbers:
            ball = LottoBallLabel(num)
            balls_layout.addWidget(ball)
            self.ball_labels.append(ball)

        balls_layout.addStretch()
        main_layout.addLayout(balls_layout)

        # 3. Subheader & Rank Badge Row
        sub_header_layout = QHBoxLayout()
        sub_header_layout.setContentsMargins(0, 0, 0, 0)

        self.set_title_lbl = QLabel("Prediction Set A (Primary)")
        self.set_title_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #2980b9; border: none; background: transparent;")

        self.rank_badge_lbl = QLabel("Rank #1")
        self.rank_badge_lbl.setAlignment(Qt.AlignCenter)
        self.rank_badge_lbl.setStyleSheet("""
            background-color: #ebf5fb;
            color: #2980b9;
            font-size: 10px;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid #aed6f1;
        """)

        sub_header_layout.addWidget(self.set_title_lbl)
        sub_header_layout.addStretch()
        sub_header_layout.addWidget(self.rank_badge_lbl)
        main_layout.addLayout(sub_header_layout)

        # 4. 5 Metric Cards Grid / Row
        metrics_layout = QHBoxLayout()
        metrics_layout.setContentsMargins(0, 2, 0, 0)
        metrics_layout.setSpacing(8)

        self.card_ai_score = MetricCard("AI Score", "94.6%", "#27ae60")
        self.card_ensemble = MetricCard("Ensemble Strength", "92.1%", "#27ae60")
        self.card_confidence = MetricCard("Confidence", "94.7%", "#2c3e50")
        self.card_rank = MetricCard("Expected Rank", "Top 5%", "#8e44ad")
        self.card_odds = MetricCard("Winning Odds", "1 / 8.2", "#2c3e50")

        metrics_layout.addWidget(self.card_ai_score)
        metrics_layout.addWidget(self.card_ensemble)
        metrics_layout.addWidget(self.card_confidence)
        metrics_layout.addWidget(self.card_rank)
        metrics_layout.addWidget(self.card_odds)

        main_layout.addLayout(metrics_layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        _log.info("MainPredictionWidget initialized with full dynamic binding support.")

    def update_prediction_data(self, numbers: list, set_name: str = "Prediction Set A", metrics: dict = None):
        """
        Dynamically updates the widget with newly generated numbers, set title, 
        rank badge, and analytical metric values.
        """
        try:
            # 1. Update 6 Lotto Balls
            if numbers and isinstance(numbers, (list, tuple)):
                valid_nums = [int(n) for n in numbers if str(n).isdigit() and int(n) > 0]
                for i in range(min(len(self.ball_labels), len(valid_nums))):
                    self.ball_labels[i].update_number(valid_nums[i])

            # 2. Update Set Title Name
            if set_name:
                self.set_title_lbl.setText(str(set_name))

            # 3. Update Metrics and Rank Badge if dictionary is provided
            if metrics and isinstance(metrics, dict):
                if "ai_score" in metrics:
                    self.card_ai_score.set_value(metrics["ai_score"])
                if "ensemble" in metrics:
                    self.card_ensemble.set_value(metrics["ensemble"])
                if "confidence" in metrics:
                    self.card_confidence.set_value(metrics["confidence"])
                if "rank" in metrics:
                    rank_val = metrics["rank"]
                    self.card_rank.set_value(rank_val)
                    self.rank_badge_lbl.setText(f"Rank {rank_val}")
                if "odds" in metrics:
                    self.card_odds.set_value(metrics["odds"])

            _log.info(f"MainPredictionWidget successfully updated for set: {set_name}")
        except Exception as e:
            _log.error(f"Failed to update MainPredictionWidget data: {e}")