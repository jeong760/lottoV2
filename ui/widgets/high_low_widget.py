# -*- coding: utf-8 -*-
# ui/widgets/high_low_widget.py
import sys
import os
import logging

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("HighLowWidget")

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen


class DonutChartPainter(QWidget):
    def __init__(self, low_count=0, high_count=0, parent=None):
        super().__init__(parent)
        self.low_count = low_count
        self.high_count = high_count
        self.setFixedSize(72, 72)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_data(self, low_count, high_count):
        self.low_count = max(0, low_count)
        self.high_count = max(0, high_count)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width, height = self.width(), self.height()
        side = min(width, height)
        pen_width = 9
        rect = QRectF(pen_width / 2, pen_width / 2, side - pen_width, side - pen_width)

        total = self.low_count + self.high_count
        if total <= 0:
            # Draw empty/standby circular track
            painter.setPen(QPen(QColor("#dcdde1"), pen_width, Qt.SolidLine, Qt.FlatCap))
            painter.drawArc(rect, 0, 360 * 16)
            return

        span_low = int(- (self.low_count / total) * 360 * 16)
        span_high = int(- (self.high_count / total) * 360 * 16)

        painter.setPen(QPen(QColor("#27ae60"), pen_width, Qt.SolidLine, Qt.FlatCap))
        painter.drawArc(rect, 90 * 16, span_low)

        painter.setPen(QPen(QColor("#8e44ad"), pen_width, Qt.SolidLine, Qt.FlatCap))
        painter.drawArc(rect, (90 * 16) + span_low, span_high)


class HighLowWidget(QGroupBox):
    def __init__(self, title="High / Low Distribution", parent=None):
        super().__init__(title, parent)
        self.low_total = 0
        self.high_total = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(6)
        content_layout.setAlignment(Qt.AlignVCenter)

        self.donut_widget = DonutChartPainter(self.low_total, self.high_total)
        
        center_container = QWidget(self.donut_widget)
        center_container.setGeometry(6, 6, 60, 60)
        center_container.setStyleSheet("background: transparent; border: none;")
        
        c_layout = QVBoxLayout(center_container)
        c_layout.setAlignment(Qt.AlignCenter)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        self.lbl_ratio = QLabel("0 : 0")
        self.lbl_ratio.setStyleSheet("font-size: 10.5px; font-weight: bold; color: #2c3e50; background: transparent; border: none;")
        self.lbl_status = QLabel("No Data")
        self.lbl_status.setStyleSheet("font-size: 7.5px; color: #7f8c8d; font-weight: bold; background: transparent; border: none;")

        c_layout.addWidget(self.lbl_ratio, alignment=Qt.AlignCenter)
        c_layout.addWidget(self.lbl_status, alignment=Qt.AlignCenter)

        content_layout.addWidget(self.donut_widget, alignment=Qt.AlignCenter)

        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(2)
        legend_layout.setAlignment(Qt.AlignVCenter)

        self.lbl_low_legend = QLabel("■ Low: 0 (0.0%)")
        self.lbl_low_legend.setStyleSheet("font-size: 9px; color: #27ae60; font-weight: bold; border: none; background: transparent;")

        self.lbl_high_legend = QLabel("■ High: 0 (0.0%)")
        self.lbl_high_legend.setStyleSheet("font-size: 9px; color: #8e44ad; font-weight: bold; border: none; background: transparent;")

        legend_layout.addWidget(self.lbl_low_legend)
        legend_layout.addWidget(self.lbl_high_legend)

        content_layout.addLayout(legend_layout)
        layout.addLayout(content_layout)

        # 1행 4열 배열에 딱 맞는 가로 195px, 세로 115px로 최적화 고정
        self.setFixedSize(195, 115)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                font-weight: bold;
                font-size: 9px;
                color: #2c3e50;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-position: top left;
                subcontrol-origin: margin;
                left: 8px;
                padding: 1px 4px;
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 3px;
            }
        """)

    def update_ratio(self, low_count: int, high_count: int):
        self.low_total = low_count
        self.high_total = high_count
        self.donut_widget.set_data(low_count, high_count)

        total = max(1, low_count + high_count)
        p_low = (low_count / total) * 100
        p_high = (high_count / total) * 100

        self.lbl_ratio.setText(f"{low_count} : {high_count}")
        self.lbl_low_legend.setText(f"■ Low: {low_count:,} ({p_low:.1f}%)")
        self.lbl_high_legend.setText(f"■ High: {high_count:,} ({p_high:.1f}%)")

        if low_count == 0 and high_count == 0:
            self.lbl_status.setText("No Data")
            return

        diff = abs(low_count - high_count)
        if diff <= total * 0.1:
            self.lbl_status.setText("Balanced")
        elif low_count > high_count:
            self.lbl_status.setText("Low Heavy")
        else:
            self.lbl_status.setText("High Heavy")

    def update_metric(self, val1, val2=0):
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            self.update_ratio(int(val1), int(val2))