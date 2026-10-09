# ui/widgets/real_time_analytics_widget.py
import sys
import os
import logging

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("RealTimeAnalyticsWidget")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, QSizePolicy
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QLinearGradient, QBrush
from core.reporting.dashboard_reporting import build_realtime_dashboard_payload


class LottoBallMiniLabel(QLabel):
    """Small official lotto ball badge for Hot Numbers list."""
    def __init__(self, number: int, parent=None):
        super().__init__(str(number).zfill(2), parent)
        self.setFixedSize(28, 28)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(self._get_ball_stylesheet(number))

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
                font-size: 11px;
                border-radius: 14px;
                border: 1px solid rgba(0, 0, 0, 0.2);
            }}
        """


class TrendLineChartWidget(QWidget):
    """Custom trend line chart widget for bottom section (Last 50 Draws)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(75)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.series_points = [50.0, 45.0, 55.0, 35.0, 40.0, 25.0, 45.0, 50.0, 30.0, 20.0, 40.0, 55.0]
        self.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dcdde1; border-radius: 6px;")

    def set_series_points(self, values):
        try:
            parsed = []
            for item in values or []:
                parsed.append(max(0.0, min(100.0, float(item))))
            if parsed:
                self.series_points = parsed
            self.update()
        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Draw grid lines
        painter.setPen(QPen(QColor("#ecf0f1"), 1, Qt.DashLine))
        painter.drawLine(0, height // 3, width, height // 3)
        painter.drawLine(0, (height // 3) * 2, width, (height // 3) * 2)

        values = self.series_points if self.series_points else [50.0, 45.0, 55.0, 35.0, 40.0]
        values = values[:max(2, len(values))]

        # Scale points to widget width
        scaled_points = []
        if width > 0 and len(values) > 1:
            step = width / float(max(1, len(values) - 1))
            for i, val in enumerate(values):
                y = height - 10 - ((float(val) / 100.0) * (height - 20))
                scaled_points.append((i * step, y))

        if len(scaled_points) > 1:
            path_pen = QPen(QColor("#2980b9"), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(path_pen)
            for i in range(len(scaled_points) - 1):
                x1, y1 = scaled_points[i]
                x2, y2 = scaled_points[i+1]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))


class RealTimeAnalyticsWidget(QFrame):
    """
    Real-Time Analytics Dashboard Widget styled for the clean light dashboard theme.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)
        self.hot_rows = []
        self.metric_labels = {}

        # Clean Light Theme Styling
        self.setStyleSheet("""
            RealTimeAnalyticsWidget {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 8px;
            }
        """)

        # 1. Header Title
        title_lbl = QLabel("REAL-TIME ANALYTICS")
        title_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #7f8c8d; letter-spacing: 1px; border: none; background: transparent;")
        main_layout.addWidget(title_lbl, alignment=Qt.AlignLeft)

        # 2. Middle Content Grid (Left: Hot Numbers / Right: 4 Metric Cards)
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(10)

        # Left Column: Hot Numbers (Top 5)
        left_container = QFrame()
        left_container.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dcdde1; border-radius: 6px;")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(6)

        hot_title = QLabel("Hot Numbers (Top 5)")
        hot_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #2c3e50; border: none; background: transparent;")
        left_layout.addWidget(hot_title)

        for _ in range(5):
            row_layout, ball, bar, lbl_pct = self._create_hot_number_row()
            left_layout.addLayout(row_layout)
            self.hot_rows.append({"ball": ball, "bar": bar, "label": lbl_pct})

        middle_layout.addWidget(left_container, stretch=5)

        # Right Column: 2x2 Metric Cards Grid
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Top row cards (Odd/Even, High/Low)
        top_metrics_layout = QHBoxLayout()
        top_metrics_layout.setSpacing(8)
        top_metrics_layout.addWidget(self._create_sub_card("odd_even", "Odd / Even", "3 : 3", "Balanced Ratio"))
        top_metrics_layout.addWidget(self._create_sub_card("high_low", "High / Low", "3 : 3", "Balanced Ratio"))
        right_layout.addLayout(top_metrics_layout)

        # Bottom row cards (Sum Distribution, AC Value)
        bottom_metrics_layout = QHBoxLayout()
        bottom_metrics_layout.setSpacing(8)
        bottom_metrics_layout.addWidget(self._create_sub_card("sum_distribution", "Sum Distribution", "188", "(Average : 182.7)"))
        bottom_metrics_layout.addWidget(self._create_sub_card("ac_value", "AC Value", "7.4", "(Average : 7.1)"))
        right_layout.addLayout(bottom_metrics_layout)

        middle_layout.addWidget(right_container, stretch=6)
        main_layout.addLayout(middle_layout)

        # 3. Bottom Trend Section
        bottom_container = QFrame()
        bottom_container.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dcdde1; border-radius: 6px;")
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(10, 8, 10, 8)
        bottom_layout.setSpacing(4)

        trend_header = QHBoxLayout()
        trend_title = QLabel("Trend (Last 50 Draws)")
        trend_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #2c3e50; border: none; background: transparent;")
        
        trend_labels = QLabel("High    Mid    Low")
        trend_labels.setStyleSheet("font-size: 9px; color: #7f8c8d; border: none; background: transparent;")
        
        trend_header.addWidget(trend_title)
        trend_header.addStretch()
        trend_header.addWidget(trend_labels)
        bottom_layout.addLayout(trend_header)

        self.trend_chart = TrendLineChartWidget()
        bottom_layout.addWidget(self.trend_chart)

        main_layout.addWidget(bottom_container)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.update_from_statistics({})
        _log.info("RealTimeAnalyticsWidget initialized successfully.")

    def _create_hot_number_row(self):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)

        ball = LottoBallMiniLabel(1)
        bar = QProgressBar()
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setStyleSheet("""
            QProgressBar { background-color: #ecf0f1; border: none; border-radius: 4px; }
            QProgressBar::chunk { background-color: #16a085; border-radius: 4px; }
        """)

        lbl_pct = QLabel("0.0%")
        lbl_pct.setStyleSheet("font-size: 10px; font-weight: bold; color: #2c3e50; border: none; background: transparent;")
        lbl_pct.setFixedWidth(40)

        row_layout.addWidget(ball)
        row_layout.addWidget(bar, stretch=1)
        row_layout.addWidget(lbl_pct)
        return row_layout, ball, bar, lbl_pct

    def _create_sub_card(self, metric_key: str, title: str, main_val: str, sub_val: str):
        """Helper to create small 2x2 analytical cards."""
        card = QFrame()
        card.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dcdde1; border-radius: 6px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 10px; color: #7f8c8d; font-weight: bold; border: none; background: transparent;")

        lbl_main = QLabel(main_val)
        lbl_main.setAlignment(Qt.AlignCenter)
        lbl_main.setStyleSheet("font-size: 14px; color: #2c3e50; font-weight: bold; border: none; background: transparent;")

        lbl_sub = QLabel(sub_val)
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 9px; color: #7f8c8d; border: none; background: transparent;")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_main)
        layout.addWidget(lbl_sub)
        self.metric_labels[metric_key] = (lbl_main, lbl_sub)
        return card

    def _get_heat_color(self, number: int) -> str:
        if 1 <= number <= 10:
            return "#f1c40f"
        if 11 <= number <= 20:
            return "#2980b9"
        if 21 <= number <= 30:
            return "#e74c3c"
        if 31 <= number <= 40:
            return "#7f8c8d"
        return "#27ae60"

    def update_from_statistics(self, stats_payload):
        try:
            payload = build_realtime_dashboard_payload(stats_payload, hot_limit=5)

            hot_numbers = payload.get("hot_numbers", [])
            for idx, row_ref in enumerate(self.hot_rows):
                if idx < len(hot_numbers):
                    row = hot_numbers[idx]
                    number = int(row.get("number", 1))
                    rate_pct = float(row.get("rate_pct", 0.0))
                    row_ref["ball"].setText(str(number).zfill(2))
                    row_ref["ball"].setStyleSheet(row_ref["ball"]._get_ball_stylesheet(number))
                    row_ref["bar"].setValue(int(max(0.0, min(100.0, rate_pct))))
                    chunk_color = self._get_heat_color(number)
                    row_ref["bar"].setStyleSheet(
                        f"""
                        QProgressBar {{ background-color: #ecf0f1; border: none; border-radius: 4px; }}
                        QProgressBar::chunk {{ background-color: {chunk_color}; border-radius: 4px; }}
                        """
                    )
                    row_ref["label"].setText(f"{rate_pct:.1f}%")
                else:
                    row_ref["ball"].setText("--")
                    row_ref["bar"].setValue(0)
                    row_ref["label"].setText("0.0%")

            for key in ("odd_even", "high_low", "sum_distribution", "ac_value"):
                labels = self.metric_labels.get(key)
                if not labels:
                    continue
                value_label, sub_label = labels
                metric_block = payload.get(key, {})
                if isinstance(metric_block, dict):
                    value_label.setText(str(metric_block.get("value", "-")))
                    sub_label.setText(str(metric_block.get("sub", "-")))

            trend_series = payload.get("trend_series", [])
            self.trend_chart.set_series_points(trend_series)
        except Exception as e:
            _log.warning(f"Failed to update RealTimeAnalyticsWidget payload: {e}", exc_info=True)