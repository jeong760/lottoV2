# ui/widgets/ai_training_widget.py
import sys
import os
import logging

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("AITrainingWidget")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QSizePolicy, QProgressBar
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen


class AITrainingCircularGaugeWidget(QWidget):
    """
    Custom circular progress gauge widget displaying training percentage and current status.
    """
    def __init__(self, progress_pct=0, status_text="Standby", parent=None):
        super().__init__(parent)
        self.progress_pct = progress_pct
        self.status_text = status_text
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_progress(self, progress_pct: int, status_text: str = "Training..."):
        """Updates the gauge progress percentage and status description."""
        self.progress_pct = max(0, min(100, progress_pct))
        self.status_text = status_text
        self.update()

    def paintEvent(self, event):
        """Paints the circular progress track, active arc, and centered label text."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        
        cx = width / 2.0
        cy = height / 2.0
        radius = min(cx, cy) - 15

        # 1. Draw background track ring
        pen_track = QPen(QColor("#f1f2f6"), 8, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_track)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # 2. Draw active progress arc based on percentage
        span_angle = int((self.progress_pct / 100.0) * 360 * 16)
        pen_progress = QPen(QColor("#2980b9"), 8, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen_progress)
        painter.drawArc(QRectF(cx - radius, cy - radius, radius * 2, radius * 2), 90 * 16, -span_angle)

        # 3. Draw Inner Text (Percentage & Status)
        painter.setPen(QColor("#2c3e50"))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(QRectF(cx - radius, cy - 16, radius * 2, 20), Qt.AlignCenter, f"{self.progress_pct}%")

        painter.setPen(QColor("#7f8c8d"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(QRectF(cx - radius, cy + 4, radius * 2, 16), Qt.AlignCenter, self.status_text)


class AITrainingWidget(QGroupBox):
    """
    AI Training Progress widget reflecting real-time epoch, loss, accuracy, 
    learning rate, and elapsed time, styled harmoniously with the main dashboard theme.
    """
    def __init__(self, title="AI TRAINING PROGRESS", parent=None):
        super().__init__(title, parent)
        self.init_ui()

    def init_ui(self):
        """Initializes user interface layouts, gauges, metrics rows, and stylesheet rules."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(6)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Circular Gauge Widget
        self.gauge = AITrainingCircularGaugeWidget(0, "Standby")
        top_layout.addWidget(self.gauge, stretch=4)

        # 2. Detailed Metrics Layout (Right side)
        metrics_layout = QVBoxLayout()
        metrics_layout.setContentsMargins(0, 5, 0, 5)
        metrics_layout.setSpacing(4)

        epoch_layout, self.val_epoch = self._create_metric_row("Epoch", "0 / 50")
        loss_layout, self.val_loss = self._create_metric_row("Loss", "0.0000")
        accuracy_layout, self.val_accuracy = self._create_metric_row("Accuracy", "0.0%")
        lr_layout, self.val_lr = self._create_metric_row("Learning Rate", "0.00010")
        time_layout, self.val_time = self._create_metric_row("Time Elapsed", "00:00:00")

        metrics_layout.addLayout(epoch_layout)
        metrics_layout.addLayout(loss_layout)
        metrics_layout.addLayout(accuracy_layout)
        metrics_layout.addLayout(lr_layout)
        metrics_layout.addLayout(time_layout)

        top_layout.addLayout(metrics_layout, stretch=5)
        main_layout.addLayout(top_layout)

        # 3. Bottom Progress Bar
        self.bottom_progress = QProgressBar()
        self.bottom_progress.setRange(0, 100)
        self.bottom_progress.setValue(0)
        self.bottom_progress.setTextVisible(False)
        self.bottom_progress.setFixedHeight(6)
        self.bottom_progress.setStyleSheet("""
            QProgressBar { background-color: #f1f2f6; border-radius: 3px; border: none; }
            QProgressBar::chunk { background-color: #2980b9; border-radius: 3px; }
        """)
        main_layout.addWidget(self.bottom_progress)

        # Enforce fixed dimensions matching dashboard requirements
        self.setFixedSize(260, 220)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Group box styling matching main dashboard light theme
        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 8px;
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

    def _create_metric_row(self, label_text: str, value_text: str):
        """Helper method to construct structured horizontal metric rows and return layout & value label."""
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_title = QLabel(label_text)
        lbl_title.setStyleSheet("font-size: 9px; color: #7f8c8d; font-weight: bold; border: none; background: transparent;")
        
        lbl_val = QLabel(value_text)
        lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_val.setStyleSheet("font-size: 9px; color: #2c3e50; font-weight: bold; border: none; background: transparent;")

        row_layout.addWidget(lbl_title)
        row_layout.addWidget(lbl_val)
        return row_layout, lbl_val

    def update_training_metrics(self, epoch_current: int, epoch_total: int, loss: float, accuracy: float, lr: float = 0.0001, elapsed_str: str = "00:00:00"):
        """Dynamically updates training progress, circular gauge, and numerical performance metrics."""
        pct = int((epoch_current / max(1, epoch_total)) * 100)
        status = "Training..." if pct < 100 else "Completed"
        
        self.gauge.set_progress(pct, status)
        self.bottom_progress.setValue(pct)

        self.val_epoch.setText(f"{epoch_current} / {epoch_total}")
        self.val_loss.setText(f"{loss:.4f}")
        self.val_accuracy.setText(f"{accuracy:.1f}%")
        self.val_lr.setText(f"{lr:.5f}")
        self.val_time.setText(elapsed_str)

    def update_training_stats(self, epoch_current: int, epoch_total: int, loss: float, accuracy: float):
        """Compatibility alias for update_training_metrics."""
        self.update_training_metrics(epoch_current, epoch_total, loss, accuracy, lr=0.0001, elapsed_str="00:00:00")