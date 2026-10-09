# ui/widgets/ac_widget.py
import sys
import os
import logging

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("ACWidget")

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen

class DonutChartPainter(QWidget):
    def __init__(self, ac_val=0.0, parent=None):
        super().__init__(parent)
        self.ac_val = ac_val
        self.setFixedSize(72, 72)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_data(self, ac_val):
        self.ac_val = max(0.0, ac_val)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width, height = self.width(), self.height()
        side = min(width, height)
        pen_width = 9
        rect = QRectF(pen_width / 2, pen_width / 2, side - pen_width, side - pen_width)

        if self.ac_val <= 0.0:
            painter.setPen(QPen(QColor("#dcdde1"), pen_width, Qt.SolidLine, Qt.FlatCap))
            painter.drawArc(rect, 0, 360 * 16)
            return

        pct = min(100.0, (self.ac_val / 15.0) * 100.0)
        span_angle = int(- (pct / 100.0) * 360 * 16)

        painter.setPen(QPen(QColor("#dfe4ea"), pen_width, Qt.SolidLine, Qt.FlatCap))
        painter.drawEllipse(rect)

        painter.setPen(QPen(QColor("#16a085"), pen_width, Qt.SolidLine, Qt.FlatCap))
        painter.drawArc(rect, 90 * 16, span_angle)


class ACWidget(QGroupBox):
    def __init__(self, title="AC Value (Complexity)", parent=None):
        super().__init__(title, parent)
        self.current_ac = 0.0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(6)
        content_layout.setAlignment(Qt.AlignVCenter)

        self.donut_widget = DonutChartPainter(self.current_ac)
        
        center_container = QWidget(self.donut_widget)
        center_container.setGeometry(6, 6, 60, 60)
        center_container.setStyleSheet("background: transparent; border: none;")
        
        c_layout = QVBoxLayout(center_container)
        c_layout.setAlignment(Qt.AlignCenter)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        self.lbl_value = QLabel("0.0")
        self.lbl_value.setStyleSheet("font-size: 11.5px; font-weight: bold; color: #2c3e50; background: transparent; border: none;")
        self.lbl_status = QLabel("No Data")
        self.lbl_status.setStyleSheet("font-size: 7.5px; color: #7f8c8d; font-weight: bold; background: transparent; border: none;")

        c_layout.addWidget(self.lbl_value, alignment=Qt.AlignCenter)
        c_layout.addWidget(self.lbl_status, alignment=Qt.AlignCenter)

        content_layout.addWidget(self.donut_widget, alignment=Qt.AlignCenter)

        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(2)
        desc_layout.setAlignment(Qt.AlignVCenter)

        self.lbl_desc_title = QLabel("■ AC Index")
        self.lbl_desc_title.setStyleSheet("font-size: 9px; color: #16a085; font-weight: bold; border: none; background: transparent;")

        self.lbl_desc_sub = QLabel("Complexity\nmeasure.")
        self.lbl_desc_sub.setStyleSheet("font-size: 8px; color: #7f8c8d; border: none; background: transparent;")

        desc_layout.addWidget(self.lbl_desc_title)
        desc_layout.addWidget(self.lbl_desc_sub)

        content_layout.addLayout(desc_layout)
        layout.addLayout(content_layout)

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

    def set_custom_size(self, width: int, height: int):
        self.setFixedSize(width, height)

    def update_ac_value(self, ac_val: float):
        self.current_ac = ac_val
        self.donut_widget.set_data(ac_val)
        self.lbl_value.setText(f"{ac_val:.1f}")

        if ac_val <= 0.0:
            self.lbl_status.setText("No Data")
        else:
            self.lbl_status.setText("Complexity")

    def update_metric(self, val, *args):
        if isinstance(val, (int, float)):
            self.update_ac_value(float(val))