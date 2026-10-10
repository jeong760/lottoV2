# ui/widgets/odd_even_widget.py
import logging
import os
import sys

# Ensure project root is in python path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("OddEvenWidget")

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen

class DonutChartPainter(QWidget):
    def __init__(self, odd_count=0, even_count=0, parent=None):
        super().__init__(parent)
        self.odd_count = odd_count
        self.even_count = even_count
        self.setFixedSize(72, 72)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_data(self, odd_count, even_count):
        self.odd_count = max(0, odd_count)
        self.even_count = max(0, even_count)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width, height = self.width(), self.height()
        side = min(width, height)
        pen_width = 9
        rect = QRectF(pen_width / 2, pen_width / 2, side - pen_width, side - pen_width)

        total = self.odd_count + self.even_count
        if total <= 0:
            painter.setPen(QPen(QColor("#dcdde1"), pen_width, Qt.SolidLine, Qt.FlatCap))
            painter.drawArc(rect, 0, 360 * 16)
            return

        span_odd = int(- (self.odd_count / total) * 360 * 16)
        span_even = int(- (self.even_count / total) * 360 * 16)

        painter.setPen(QPen(QColor("#2980b9"), pen_width, Qt.SolidLine, Qt.FlatCap))
        painter.drawArc(rect, 90 * 16, span_odd)

        painter.setPen(QPen(QColor("#e74c3c"), pen_width, Qt.SolidLine, Qt.FlatCap))
        painter.drawArc(rect, (90 * 16) + span_odd, span_even)


class OddEvenWidget(QGroupBox):
    def __init__(self, title="Odd / Even Distribution", parent=None):
        super().__init__(title, parent)
        self.odd_total = 0
        self.even_total = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(6)
        content_layout.setAlignment(Qt.AlignVCenter)

        self.donut_widget = DonutChartPainter(self.odd_total, self.even_total)
        
        # 중앙 컨테이너 크기를 도넛 차트 내부 공간에 딱 맞게 타이트하게 설정 (삐져나옴 방지)
        center_container = QWidget(self.donut_widget)
        center_container.setGeometry(10, 10, 52, 52)
        center_container.setStyleSheet("background: transparent; border: none;")
        
        c_layout = QVBoxLayout(center_container)
        c_layout.setAlignment(Qt.AlignCenter)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # 폰트 크기를 컴팩트하게 조정하여 원 밖으로 글자가 나가지 않도록 함
        self.lbl_ratio = QLabel("0 : 0")
        self.lbl_ratio.setAlignment(Qt.AlignCenter)
        self.lbl_ratio.setStyleSheet("font-size: 9px; font-weight: bold; color: #2c3e50; background: transparent; border: none;")
        
        self.lbl_status = QLabel("No Data")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 7px; color: #7f8c8d; font-weight: bold; background: transparent; border: none;")

        c_layout.addWidget(self.lbl_ratio)
        c_layout.addWidget(self.lbl_status)

        content_layout.addWidget(self.donut_widget, alignment=Qt.AlignCenter)

        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(2)
        legend_layout.setAlignment(Qt.AlignVCenter)

        self.lbl_odd_legend = QLabel("■ Odd: 0 (0.0%)")
        self.lbl_odd_legend.setStyleSheet("font-size: 9px; color: #2980b9; font-weight: bold; border: none; background: transparent;")

        self.lbl_even_legend = QLabel("■ Even: 0 (0.0%)")
        self.lbl_even_legend.setStyleSheet("font-size: 9px; color: #e74c3c; font-weight: bold; border: none; background: transparent;")

        legend_layout.addWidget(self.lbl_odd_legend)
        legend_layout.addWidget(self.lbl_even_legend)

        content_layout.addLayout(legend_layout)
        layout.addLayout(content_layout)

        # 1행 4열 배열에 딱 들어맞는 가로 195px, 세로 115px로 최적화 고정
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

    def update_ratio(self, odd_count: int, even_count: int):
        self.odd_total = odd_count
        self.even_total = even_count
        self.donut_widget.set_data(odd_count, even_count)

        total = max(1, odd_count + even_count)
        p_odd = (odd_count / total) * 100
        p_even = (even_count / total) * 100

        self.lbl_ratio.setText(f"{odd_count} : {even_count}")
        self.lbl_odd_legend.setText(f"■ Odd: {odd_count:,} ({p_odd:.1f}%)")
        self.lbl_even_legend.setText(f"■ Even: {even_count:,} ({p_even:.1f}%)")

        if odd_count == 0 and even_count == 0:
            self.lbl_status.setText("No Data")
            return

        diff = abs(odd_count - even_count)
        if diff <= total * 0.1:
            self.lbl_status.setText("Balanced")
        elif odd_count > even_count:
            self.lbl_status.setText("Odd Heavy")
        else:
            self.lbl_status.setText("Even Heavy")

    def update_metric(self, val1, val2=0):
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            self.update_ratio(int(val1), int(val2))