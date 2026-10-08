# -*- coding: utf-8 -*-
# ui/widgets/ai_status_widget.py
import logging
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.logger import setup_logging
setup_logging(project_root)

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt

from .ai_system_widget import AISystemWidget
from .ai_training_widget import AITrainingWidget

_log = logging.getLogger("AIStatusWidget")


class AIStatusWidget(QWidget):
    """
    AI System Status Dashboard Container Widget combining:
    1. AISystemWidget (AI system metrics, score, ensemble, confidence, expected rank)
    2. AITrainingWidget (Live training progress, epochs, loss, accuracy)
    Optimized with balanced proportions and clean container styling.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Clean light theme stylesheet matching main dashboard (Outbox Container)
        self.setStyleSheet("""
            AIStatusWidget {
                background-color: #ffffff;
                color: #2c3e50;
                border-radius: 8px;
                border: 1px solid #dcdde1;
            }
        """)

        # 1. AI System Metrics Widget
        self.ai_system_widget = AISystemWidget()
        self.ai_system_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.ai_system_widget)

        # 2. AI Training Progress Widget
        self.ai_training_widget = AITrainingWidget()
        self.ai_training_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.ai_training_widget)

        # 컨테이너 전체 크기 정책 설정 (대시보드 그리드에 알맞게 조절)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        _log.info("AIStatusWidget initialized with balanced layout proportions.")

    def update_metrics(self, score: float, ensemble: float, confidence: float, rank_text: str = "Top 5%"):
        """Dynamically updates core AI metric values via AISystemWidget."""
        if hasattr(self, 'ai_system_widget') and self.ai_system_widget:
            if hasattr(self.ai_system_widget, 'update_ai_metrics'):
                self.ai_system_widget.update_ai_metrics(score, ensemble, confidence, rank_text)
            elif hasattr(self.ai_system_widget, 'update_metrics'):
                self.ai_system_widget.update_metrics(score, ensemble, confidence, rank_text)

    def update_training_live_data(self, epoch: int, max_epochs: int, loss: float, accuracy: float):
        """Updates live training telemetry data via AITrainingWidget."""
        if hasattr(self, 'ai_training_widget') and self.ai_training_widget:
            if hasattr(self.ai_training_widget, 'update_training_stats'):
                self.ai_training_widget.update_training_stats(epoch, max_epochs, loss, accuracy)