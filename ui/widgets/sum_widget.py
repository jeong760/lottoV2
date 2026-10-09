# ui/widgets/sum_widget.py
import sys
import os
import logging

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("SumWidget")

from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen
from data.lotto_db_helper import LottoDBHelper


class SumBarChartWidget(QWidget):
    """
    Custom fine-grained bell-curve histogram bar chart for Sum Distribution.
    """
    def __init__(self, current_sum=0, parent=None):
        super().__init__(parent)
        self.current_sum = current_sum
        self.setFixedHeight(45)  # 1행 4열 콤팩트 규격에 맞게 높이 축소
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_sum(self, current_sum: int):
        self.current_sum = current_sum
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Fine-grained bell-curve distribution bins mapping range 100 ~ 250 (31 bins)
        bars = [
            1, 2, 3, 5, 8, 12, 17, 24, 33, 45, 
            58, 72, 85, 95, 100, 95, 85, 72, 58, 45, 
            33, 24, 17, 12, 8, 5, 3, 2, 1, 1, 1
        ]
        num_bars = len(bars)
        if num_bars == 0:
            return

        if self.current_sum <= 0:
            total_spacing = (num_bars - 1) * 1.0
            bar_width = max(1.0, (width - 6 - total_spacing) / num_bars)
            for i in range(num_bars):
                x = 3 + (i * (bar_width + 1.0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("#dfe4ea"))
                painter.drawRoundedRect(QRectF(x, height - 10 - 2.0, bar_width, 2.0), 1.0, 1.0)
            return

        min_sum, max_sum = 100, 250
        normalized_pos = (self.current_sum - min_sum) / (max_sum - min_sum)
        highlight_idx = int(round(normalized_pos * (num_bars - 1)))
        highlight_idx = max(0, min(num_bars - 1, highlight_idx))

        total_spacing = (num_bars - 1) * 1.0
        bar_width = max(1.0, (width - 6 - total_spacing) / num_bars)
        max_h = max(bars) if max(bars) > 0 else 1

        for i, val in enumerate(bars):
            x = 3 + (i * (bar_width + 1.0))
            b_height = max(2.0, (val / max_h) * (height - 12))
            y = height - b_height - 10

            if i == highlight_idx:
                base_color = QColor("#f1c40f")  # Gold highlight for current value
            else:
                base_color = QColor("#2980b9")  # Blue for distribution

            painter.setPen(Qt.NoPen)
            painter.setBrush(base_color)
            painter.drawRoundedRect(QRectF(x, y, bar_width, b_height), 1.0, 1.0)


class SumWidget(QGroupBox):
    """
    Widget tracking the total sum range of generated sets,
    styled with a fine-grained bell-curve histogram and dynamic value/average display.
    """
    def __init__(self, title="Number Sum (SUM Tendency)", parent=None):
        super().__init__(title, parent)
        self.current_sum = 0
        self.avg_sum = 0
        self.init_ui()
        self.load_generated_average()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # 1. Header Title Layout
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel("SUM DISTRIBUTION")
        title_lbl.setStyleSheet("font-size: 9px; font-weight: bold; color: #7f8c8d; letter-spacing: 0.5px; border: none; background: transparent;")

        header_layout.addWidget(title_lbl, alignment=Qt.AlignLeft)
        layout.addLayout(header_layout)

        # 2. Flanked Metrics Layout
        metrics_layout = QHBoxLayout()
        metrics_layout.setContentsMargins(0, 0, 0, 0)

        self.current_lbl = QLabel(f"Sum: {self.current_sum}")
        self.current_lbl.setStyleSheet("font-size: 9px; font-weight: bold; color: #d35400; border: none; background: transparent;")

        self.avg_lbl = QLabel(f"Gen.Avg: {self.avg_sum}")
        self.avg_lbl.setStyleSheet("font-size: 9px; font-weight: bold; color: #2980b9; border: none; background: transparent;")

        metrics_layout.addWidget(self.current_lbl, alignment=Qt.AlignLeft)
        metrics_layout.addStretch()
        metrics_layout.addWidget(self.avg_lbl, alignment=Qt.AlignRight)
        
        layout.addLayout(metrics_layout)

        # 3. Bell Curve Histogram Bar Chart Widget
        self.chart = SumBarChartWidget(self.current_sum)
        layout.addWidget(self.chart)

        # 4. Bottom Scale Labels (100 ~ 250)
        scale_layout = QHBoxLayout()
        scale_layout.setContentsMargins(2, 0, 2, 0)
        for s in ["100", "130", "160", "190", "220", "250"]:
            lbl = QLabel(s)
            lbl.setStyleSheet("font-size: 7.5px; color: #7f8c8d; border: none; background: transparent;")
            scale_layout.addWidget(lbl)
            if s != "250":
                scale_layout.addStretch()
        layout.addLayout(scale_layout)

        # 1행 4열 배열에 딱 맞는 가로 195px, 세로 115px로 최적화 고정
        self.setFixedSize(195, 115)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Group box styling matching light theme
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

    def load_generated_average(self):
        """Calculates and updates the average sum based on generated number sets history."""
        try:
            records = LottoDBHelper.load_generation_history()
            if not records:
                return
            
            total_sum = 0
            count = 0
            for rec in records:
                for s_detail in rec.get("sets_detail", []):
                    nums = s_detail.get("numbers", [])
                    valid_6 = [int(n) for n in nums[:6] if 1 <= int(n) <= 45]
                    if len(valid_6) == 6:
                        total_sum += sum(valid_6)
                        count += 1
                        
            if count > 0:
                self.avg_sum = round(total_sum / count)
                self.avg_lbl.setText(f"Gen.Avg: {self.avg_sum}")
        except Exception as e:
            _log.error(f"Failed to load generated sets average sum: {e}")

    def update_historical_average(self, avg_val: int):
        """External call handler for average update."""
        self.avg_sum = avg_val
        self.avg_lbl.setText(f"Gen.Avg: {self.avg_sum}")

    def update_sum_value(self, total_sum: int, avg_sum: int = 0):
        self.current_sum = total_sum
        if avg_sum > 0:
            self.avg_sum = avg_sum
        self.chart.set_sum(total_sum)
        
        if total_sum <= 0:
            self.current_lbl.setText("Sum: No Data")
        else:
            self.current_lbl.setText(f"Sum: {total_sum}")
        self.avg_lbl.setText(f"Gen.Avg: {self.avg_sum}")

    def update_metric(self, val, avg_val=0):
        if isinstance(val, (int, float)):
            self.update_sum_value(int(val), int(avg_val))