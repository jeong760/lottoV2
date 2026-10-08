# -*- coding: utf-8 -*-
# ui/widgets/decade_dist_widget.py
import sys
import os
import logging

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("DecadeDistWidget")

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath, QLinearGradient
from data.repositories.lotto_repository import LottoRepository


class SparklineWidget(QWidget):
    def __init__(self, recent_trend_values=None, parent=None):
        super().__init__(parent)
        self.trend_values = recent_trend_values or [0] * 50
        self.setFixedHeight(36)  # 스파크라인 높이 살짝 확대
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_trend(self, values):
        self.trend_values = values
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        if not self.trend_values or len(self.trend_values) < 2:
            return

        min_val = min(self.trend_values)
        max_val = max(self.trend_values)
        val_range = max_val - min_val if max_val != min_val else 1

        path = QPainterPath()
        fill_path = QPainterPath()

        step_x = width / (len(self.trend_values) - 1) if len(self.trend_values) > 1 else width

        points = []
        for idx, val in enumerate(self.trend_values):
            x = idx * step_x
            y = height - 4 - ((val - min_val) / val_range) * (height - 8)
            points.append((x, y))

        if not points:
            return

        path.moveTo(points[0][0], points[0][1])
        fill_path.moveTo(points[0][0], height - 2)
        fill_path.lineTo(points[0][0], points[0][1])

        for x, y in points[1:]:
            path.lineTo(x, y)
            fill_path.lineTo(x, y)

        fill_path.lineTo(points[-1][0], height - 2)
        fill_path.closeSubpath()

        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0.0, QColor(41, 128, 185, 80))
        gradient.setColorAt(1.0, QColor(41, 128, 185, 5))
        painter.fillPath(fill_path, gradient)

        pen = QPen(QColor("#2980b9"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)


class LottoBallLabel(QLabel):
    def __init__(self, number: int = 0, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setAlignment(Qt.AlignCenter)
        self.set_number(number)

    def set_number(self, num: int):
        self.number = num
        if num <= 0:
            self.setText("-")
            self.setStyleSheet("""
                QLabel {
                    background-color: #e0e0e0;
                    color: #7f8c8d;
                    font-size: 8.5px;
                    font-weight: bold;
                    border-radius: 10px;
                }
            """)
            return

        self.setText(f"{num:02d}")
        bg_color, fg_color = self._get_ball_colors(num)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {fg_color};
                font-size: 9px;
                font-weight: bold;
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 0.15);
            }}
        """)

    def _get_ball_colors(self, num: int):
        if 1 <= num <= 10:
            return "#fbc531", "#2c3e50"
        elif 11 <= num <= 20:
            return "#00a8ff", "#ffffff"
        elif 21 <= num <= 30:
            return "#e84118", "#ffffff"
        elif 31 <= num <= 40:
            return "#7f8c8d", "#ffffff"
        else:
            return "#4cd137", "#ffffff"


class DecadeDistWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Top Frequencies & Recent Trend", parent)
        self.init_ui()
        self.load_top_frequencies_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 14, 10, 12)
        layout.setSpacing(6)  # 내부 항목 간격 살짝 조정
        
        self.rows = []
        self.top_container = QWidget()
        self.top_layout = QVBoxLayout(self.top_container)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(4)  # 행 간격 조정

        for i in range(5):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)

            rank_lbl = QLabel(f"#{i+1}")
            rank_lbl.setFixedWidth(20)
            rank_lbl.setStyleSheet("font-size: 8.5px; font-weight: bold; color: #7f8c8d;")

            ball_label = LottoBallLabel(0)

            pbar = QProgressBar()
            pbar.setRange(0, 100)
            pbar.setValue(0)
            pbar.setTextVisible(True)
            pbar.setFormat("%v% (%1 hits)")
            pbar.setFixedHeight(16)  # 프로그레스 바 높이 살짝 확대
            pbar.setStyleSheet("""
                QProgressBar {
                    background-color: #ecf0f1;
                    border: none;
                    border-radius: 4px;
                    text-align: right;
                    font-size: 8.5px;
                    color: #7f8c8d;
                    padding-right: 6px;
                }
                QProgressBar::chunk {
                    background-color: #2980b9;
                    border-radius: 4px;
                }
            """)

            row_layout.addWidget(rank_lbl)
            row_layout.addWidget(ball_label)
            row_layout.addWidget(pbar, stretch=1)

            self.top_layout.addWidget(row_widget)
            self.rows.append((ball_label, pbar))

        layout.addWidget(self.top_container)

        trend_lbl = QLabel("Recent 50-Draw Trend Flow")
        trend_lbl.setStyleSheet("font-size: 8.5px; font-weight: bold; color: #95a5a6; margin-top: 4px;")
        layout.addWidget(trend_lbl)

        self.sparkline = SparklineWidget()
        layout.addWidget(self.sparkline)

        # 세로 높이를 190px로 확장하여 시각적 여유 확보
        self.setFixedWidth(400)
        self.setFixedHeight(190)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                font-weight: bold;
                font-size: 9.5px;
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

    def load_top_frequencies_data(self):
        try:
            draws = LottoRepository.get_all_draws()
            if not draws:
                return

            freq = {i: 0 for i in range(1, 46)}
            sorted_draws = sorted(draws, key=lambda d: int(d.get("drawNo") or d.get("drwNo") or 0))

            for draw in sorted_draws:
                for i in range(1, 7):
                    val = draw.get(f"num{i}") or draw.get(f"drwtNo{i}") or 0
                    if val:
                        num = int(val)
                        if 1 <= num <= 45:
                            freq[num] += 1

            top_5 = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
            total_draws = len(sorted_draws) if len(sorted_draws) > 0 else 1

            for idx, (num, hits) in enumerate(top_5):
                if idx < len(self.rows):
                    ball_label, pbar = self.rows[idx]
                    ball_label.set_number(num)

                    pct = int((hits / (total_draws * 6)) * 100) if total_draws > 0 else 0
                    pbar.setFormat(f"{pct}% ({hits} hits)")
                    pbar.setValue(min(100, max(0, pct)))

            recent_50 = sorted_draws[-50:] if len(sorted_draws) >= 50 else sorted_draws
            trend_values = []
            for draw in recent_50:
                d_sum = sum(int(draw.get(f"num{i}") or draw.get(f"drwtNo{i}") or 0) for i in range(1, 7))
                trend_values.append(d_sum)

            if trend_values:
                self.sparkline.set_trend(trend_values)
        except Exception as e:
            _log.error(f"Failed to load top frequencies data: {e}")

    def update_metric(self, data):
        self.load_top_frequencies_data()
            
    def update_data(self, data):
        self.update_metric(data)

    def load_data(self):
        self.load_top_frequencies_data()