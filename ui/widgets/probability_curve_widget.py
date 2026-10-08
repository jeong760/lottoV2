# -*- coding: utf-8 -*-
# ui/widgets/probability_curve_widget.py
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("ProbabilityCurveWidget")

from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
import math


class ProbabilityCurveWidget(QWidget):
    """
    Probability Distribution Curve Widget.
    Visualizes the empirical frequency curve of lotto numbers against 
    the theoretical uniform distribution expectation curve.
    Optimized with balanced width/height proportions to prevent over-stretching.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # 가로로 너무 늘어지지 않도록 적절한 기본 높이 및 크기 정책 설정
        self.setMinimumSize(320, 200)
        self.setMaximumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setAutoFillBackground(True)
        
        self.observed_data = {}  # Number (1-45) -> frequency count
        self.expected_val = 0.0
        self.p_value = 1.0
        self.is_uniform = True
        _log.info("ProbabilityCurveWidget initialized with balanced aspect ratio.")

    def update_distribution_curve(self, chi2_data, number_counts):
        """
        Updates the widget with new Chi-Square test data and number counts.
        :param chi2_data: Dict containing p_value and evaluation metrics
        :param number_counts: Counter or dict tracking occurrences for numbers 1 to 45
        """
        self.p_value = chi2_data.get("p_value", 1.0)
        self.is_uniform = chi2_data.get("is_uniformly_distributed", True)
        self.observed_data = number_counts
        
        total_selections = sum(number_counts.values()) if number_counts else 0
        self.expected_val = (total_selections * (6.0 / 45.0)) if total_selections > 0 else 1.0
        self.update()
        _log.debug(f"Distribution curve updated: p_value={self.p_value:.4f}, is_uniform={self.is_uniform}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Widget background container & border
        painter.setPen(QPen(QColor("#b2bec3"), 1.5))
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRoundedRect(2, 2, width - 4, height - 4, 8, 8)

        # Draw title header & status badge
        painter.setPen(QColor("#2c3e50"))
        painter.setFont(QFont("Segoe UI", 9.5, QFont.Bold))
        painter.drawText(12, 20, "Probability Distribution & Fit Curve")

        status_text = f"{'Normal (p>0.05)' if self.is_uniform else 'Biased (p<=0.05)'} [p={self.p_value:.3f}]"
        painter.setFont(QFont("Segoe UI", 8.5))
        painter.setPen(QColor("#27ae60" if self.is_uniform else "#c0392b"))
        # 우측 여백에 딱 맞도록 위치 조정
        painter.drawText(width - 165, 20, status_text)

        # Plot boundary margins (컴팩트한 비율에 맞춰 여백 최적화)
        margin_left, margin_right, margin_top, margin_bottom = 35, 25, 38, 30
        graph_width = width - (margin_left + margin_right)
        graph_height = height - (margin_top + margin_bottom)

        # Draw grid lines
        painter.setPen(QPen(QColor("#dcdde1"), 1, Qt.DashLine))
        for i in range(4):
            y = margin_top + (graph_height / 3) * i
            painter.drawLine(margin_left, int(y), width - margin_right, int(y))

        if not self.observed_data:
            painter.setPen(QColor("#7f8c8d"))
            painter.setFont(QFont("Segoe UI", 95 if False else 9))
            painter.drawText(width // 2 - 75, height // 2, "Awaiting Statistical Data...")
            return

        # Calculate coordinates mapping for numbers 1 to 45
        max_obs = max(self.observed_data.values()) if self.observed_data else 10
        max_y_val = max(max_obs * 1.15, self.expected_val * 1.2, 1.0)

        points_observed = []
        points_expected = []

        for i in range(1, 46):
            val = self.observed_data.get(i, 0)
            x_pos = margin_left + (i - 1) * (graph_width / 44.0)
            y_obs = margin_top + graph_height - (val / max_y_val) * graph_height
            y_exp = margin_top + graph_height - (self.expected_val / max_y_val) * graph_height

            points_observed.append(QPointF(x_pos, y_obs))
            points_expected.append(QPointF(x_pos, y_exp))

        # Fill gradient under the observed curve
        if len(points_observed) > 1:
            grad = QLinearGradient(0, margin_top, 0, height - margin_bottom)
            grad.setColorAt(0.0, QColor(41, 128, 185, 110))
            grad.setColorAt(1.0, QColor(41, 128, 185, 10))
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawPolygon(points_observed + [QPointF(width - margin_right, margin_top + graph_height), QPointF(margin_left, margin_top + graph_height)])

        # Draw expected uniform distribution baseline
        pen_color = QColor("#d4ac0d")
        pen_color.setAlpha(220)
        painter.setPen(QPen(pen_color, 1.8, Qt.DashLine))
        for i in range(len(points_expected) - 1):
            painter.drawLine(points_expected[i], points_expected[i+1])

        # Draw observed empirical curve
        painter.setPen(QPen(QColor("#2980b9"), 1.8, Qt.SolidLine))
        for i in range(len(points_observed) - 1):
            painter.drawLine(points_observed[i], points_observed[i+1])

        # Draw axis labels
        painter.setPen(QColor("#7f8c8d"))
        painter.setFont(QFont("Segoe UI", 7.5))
        painter.drawText(margin_left, height - 10, "1")
        painter.drawText(width // 2 - 35, height - 10, "Number (1 ~ 45)")
        painter.drawText(width - margin_right - 12, height - 10, "45")