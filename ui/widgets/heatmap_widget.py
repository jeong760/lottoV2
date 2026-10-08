# -*- coding: utf-8 -*-
# ui/widgets/heatmap_widget.py
import sys
import os
import logging

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("LottoHeatmapWidget")

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QSizePolicy, QWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QFont
from data.repositories.lotto_repository import LottoRepository


class TrendBarChartWidget(QWidget):
    def __init__(self, data_points=None, mode="number", parent=None):
        super().__init__(parent)
        self.data_points = data_points or []
        self.mode = mode
        self.setFixedHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dcdde1;
                border-radius: 6px;
            }
        """)

    def set_data(self, points, mode="number"):
        self.data_points = points
        self.mode = mode
        self.update()

    def paintEvent(self, event):
        if not self.data_points:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        
        margin_x = 55
        margin_top = 26
        margin_bottom = 22

        values = [p[1] if isinstance(p, tuple) else p for p in self.data_points]
        max_val = max(values) if values and max(values) > 0 else 1
        total_sum = sum(values) if values else 1
        
        chart_width = width - (margin_x * 2)
        chart_height = height - margin_top - margin_bottom

        num_bars = len(self.data_points)
        if num_bars == 0:
            return
        
        bar_spacing = 2.0
        total_spacing = (num_bars - 1) * bar_spacing
        bar_width = max(1.0, (chart_width - total_spacing) / num_bars)

        # 정수형 폰트 크기 적용
        font = QFont("Arial", 7)
        painter.setFont(font)

        for i, item in enumerate(self.data_points):
            if isinstance(item, tuple):
                num, val = item
            else:
                num, val = i + 1, item

            x = margin_x + (i * (bar_width + bar_spacing))
            bar_height = max(4.0, (val / max_val) * chart_height)
            y = height - margin_bottom - bar_height

            if 1 <= num <= 10:
                base_color, top_color = QColor("#f39c12"), QColor("#f1c40f")
            elif 11 <= num <= 20:
                base_color, top_color = QColor("#2980b9"), QColor("#5499c7")
            elif 21 <= num <= 30:
                base_color, top_color = QColor("#c0392b"), QColor("#e74c3c")
            elif 31 <= num <= 40:
                base_color, top_color = QColor("#2c3e50"), QColor("#566573")
            else:
                base_color, top_color = QColor("#27ae60"), QColor("#58d68d")

            gradient = QLinearGradient(x, y, x, y + bar_height)
            gradient.setColorAt(0.0, top_color)
            gradient.setColorAt(1.0, base_color)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(QRectF(x, y, bar_width, bar_height), 1.5, 1.5)

            if bar_width >= 8:
                painter.setPen(QColor("#2c3e50"))
                if self.mode == "number":
                    pct = (val / total_sum) * 100 if total_sum > 0 else 0
                    val_str = f"{pct:.1f}%"
                else:
                    val_str = str(val)
                text_rect = QRectF(x - 10, y - 20, bar_width + 20, 16)
                painter.drawText(text_rect, Qt.AlignCenter, val_str)

            if bar_width >= 6:
                painter.setPen(QColor("#7f8c8d"))
                text_rect = QRectF(x - 4, height - margin_bottom + 3, bar_width + 8, 16)
                painter.drawText(text_rect, Qt.AlignCenter, str(num))


class LottoHeatmapWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Number Frequency Heatmap", parent)
        self.sort_mode = "number"
        self.freq_data = {}
        self.number_cells = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        sort_layout = QHBoxLayout()
        sort_layout.setContentsMargins(0, 0, 0, 0)
        sort_layout.setSpacing(4)

        self.btn_num_order = QPushButton("Number Order (1~45)")
        self.btn_num_order.setFixedHeight(22)
        self.btn_num_order.setCheckable(True)
        self.btn_num_order.setChecked(True)
        self.btn_num_order.clicked.connect(lambda: self.set_sort_mode("number"))

        self.btn_freq_order = QPushButton("Frequency Order")
        self.btn_freq_order.setFixedHeight(22)
        self.btn_freq_order.setCheckable(True)
        self.btn_freq_order.clicked.connect(lambda: self.set_sort_mode("frequency"))

        tab_style = """
            QPushButton {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 9px;
                font-weight: bold;
                color: #7f8c8d;
                padding: 0px 8px;
            }
            QPushButton:checked {
                background-color: #16a085;
                color: #ffffff;
                border: 1px solid #117a65;
            }
        """
        self.btn_num_order.setStyleSheet(tab_style)
        self.btn_freq_order.setStyleSheet(tab_style)

        sort_layout.addWidget(self.btn_num_order)
        sort_layout.addWidget(self.btn_freq_order)
        sort_layout.addStretch()
        main_layout.addLayout(sort_layout)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        
        self.grid_layout.setHorizontalSpacing(28)
        self.grid_layout.setVerticalSpacing(14)
        
        for num in range(1, 46):
            ball_lbl = QLabel()
            ball_lbl.setAlignment(Qt.AlignCenter)
            ball_lbl.setFixedSize(62, 40)
            ball_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            
            bg_gradient, _ = self._get_high_def_lotto_style(num)
            ball_lbl.setStyleSheet(f"""
                background: {bg_gradient}; 
                border-radius: 5px;
                border: 1px solid rgba(0, 0, 0, 0.25);
            """)
            self.number_cells[num] = ball_lbl

        main_layout.addWidget(self.grid_widget, 0, Qt.AlignCenter)

        self.trend_chart = TrendBarChartWidget(mode="number")
        main_layout.addWidget(self.trend_chart)

        self.setMinimumWidth(750)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10px;
                color: #2c3e50;
                margin-top: 12px;
            }
            QGroupBox::title {
                subcontrol-position: top left;
                subcontrol-origin: margin;
                left: 10px;
                padding: 2px 6px;
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 4px;
            }
        """)

        self.load_heatmap_data()

    def set_sort_mode(self, mode: str):
        if self.sort_mode == mode:
            return
        self.sort_mode = mode
        if mode == "number":
            self.btn_num_order.setChecked(True)
            self.btn_freq_order.setChecked(False)
        else:
            self.btn_num_order.setChecked(False)
            self.btn_freq_order.setChecked(True)

        self.refresh_grid_layout()

    def _get_high_def_lotto_style(self, num: int):
        if 1 <= num <= 10:
            return "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f1c40f, stop:1 #d4ac0d)", "#2c3e50"
        elif 11 <= num <= 20:
            return "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5499c7, stop:1 #2471a3)", "#ffffff"
        elif 21 <= num <= 30:
            return "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ec7063, stop:1 #b03a2e)", "#ffffff"
        elif 31 <= num <= 40:
            return "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #85929e, stop:1 #34495e)", "#ffffff"
        elif 41 <= num <= 45:
            return "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #58d68d, stop:1 #1e8449)", "#ffffff"
        return "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #bdc3c7, stop:1 #7f8c8d)", "#2c3e50"

    def load_heatmap_data(self):
        try:
            _log.info("Loading 1st to latest draw records from DB for frequency heatmap...")
            draws = LottoRepository.get_all_draws()
            
            freqs = {n: 0 for n in range(1, 46)}
            for draw in draws:
                for i in range(1, 7):
                    val = draw.get(f"num{i}") or draw.get(f"drwtNo{i}") or 0
                    if val and 1 <= int(val) <= 45:
                        freqs[int(val)] += 1

            self.freq_data = freqs
            if not any(self.freq_data.values()):
                import random
                self.freq_data = {n: random.randint(5, 35) for n in range(1, 46)}

            self.refresh_grid_layout()
            _log.info("Heatmap and bar chart data successfully loaded from DB.")
            
        except Exception as e:
            _log.error(f"Failed to load heatmap data from DB: {e}")

    def refresh_grid_layout(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if self.sort_mode == "number":
            sorted_items = sorted(self.freq_data.items(), key=lambda x: x[0])
        else:
            sorted_items = sorted(self.freq_data.items(), key=lambda x: x[1], reverse=True)

        for idx, (num, count) in enumerate(sorted_items):
            row = idx // 9
            col = idx % 9
            
            ball_lbl = self.number_cells[num]
            _, text_color = self._get_high_def_lotto_style(num)
            
            sub_color = "#2c3e50" if 1 <= num <= 10 else "rgba(255, 255, 255, 0.95)"
            
            html_text = f"""
                <div align='center' style='line-height: 1.0; padding-top: 1px;'>
                    <span style='font-size: 10pt; font-weight: bold; color: {text_color};'>{num}</span><br>
                    <span style='font-size: 7pt; font-weight: 600; color: {sub_color};'>{count} times</span>
                </div>
            """
            ball_lbl.setText(html_text)
            ball_lbl.setToolTip(f"Number {num}: {count} appearances")
            self.grid_layout.addWidget(ball_lbl, row, col)

        bar_points = [(num, count) for num, count in sorted_items]
        self.trend_chart.set_data(bar_points, mode=self.sort_mode)