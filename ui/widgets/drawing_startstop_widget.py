# -*- coding: utf-8 -*-
# ui/widgets/drawing_startstop_widget.py
import sys
import os
import logging

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("DrawingStartStopWidget")

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSpinBox, QLabel, QFrame
from PyQt5.QtCore import pyqtSignal


class DrawingStartStopWidget(QFrame):
    """
    Dedicated control widget for the Venus Turbine simulator, 
    managing set counts, start drawing, stop drawing, and skip animation actions.
    """
    generate_clicked = pyqtSignal(int)
    stop_clicked = pyqtSignal()
    skip_clicked = pyqtSignal()  # Signal emitted to skip ongoing animation sequence

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
            }
        """)
        control_layout = QHBoxLayout(self)
        control_layout.setContentsMargins(10, 6, 10, 6)

        lbl_title = QLabel("VENUS Lottery Drawing Machine")
        lbl_title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 11px; border: none;")
        
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 100000)
        self.spin_count.setValue(5)
        self.spin_count.setStyleSheet("padding: 2px; font-weight: bold;")

        self.btn_start = QPushButton("Start Drawing")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                padding: 5px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_start.clicked.connect(self.on_start_clicked)

        self.btn_stop = QPushButton("Stop Drawing")
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                font-weight: bold;
                padding: 5px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_stop.setEnabled(False)  # Disabled by default until simulation starts
        self.btn_stop.clicked.connect(self.stop_clicked.emit)

        # Skip Animation button setup
        self.btn_skip = QPushButton("Skip Animation")
        self.btn_skip.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 5px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f1c40f;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_skip.setEnabled(False)  # Disabled by default until simulation starts
        self.btn_skip.clicked.connect(self.skip_clicked.emit)

        lbl_sets = QLabel("Sets per Draw:")
        lbl_sets.setStyleSheet("border: none; font-weight: bold; color: #2c3e50;")

        control_layout.addWidget(lbl_title)
        control_layout.addStretch(1)
        control_layout.addWidget(lbl_sets)
        control_layout.addWidget(self.spin_count)
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_skip)  # Append Skip button into layout
        control_layout.addWidget(self.btn_stop)
        self.setLayout(control_layout)

    def on_start_clicked(self):
        set_count = self.spin_count.value()
        self.generate_clicked.emit(set_count)

    def set_controls_enabled(self, enabled: bool):
        """
        Toggles button and spinbox states between running and idle phases.
        """
        self.btn_start.setEnabled(enabled)
        self.spin_count.setEnabled(enabled)
        self.btn_stop.setEnabled(not enabled)
        self.btn_skip.setEnabled(not enabled)  # Enable Skip button exclusively during active drawing/mixing phases