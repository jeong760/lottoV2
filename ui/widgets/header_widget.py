# -*- coding: utf-8 -*-
# ui/widgets/header_widget.py
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

_log = logging.getLogger("HeaderWidget")

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class HeaderWidget(QWidget):
    """
    Header widget cleaned up to remove redundant status/guidance labels,
    delegating monitoring status to the Live Console panel.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        _log.info("HeaderWidget initialized successfully.")

    def update_status(self, discards, algo_title):
        """
        Maintained for compatibility with existing signal callers.
        Status tracking is now handled inside LiveConsoleWidget.
        """
        _log.debug(f"HeaderWidget status update called: algo={algo_title}, discards={len(discards) if isinstance(discards, list) else discards}")
        pass