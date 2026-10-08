# -*- coding: utf-8 -*-
# ui/widgets/live_console_widget.py
import sys
import os
import logging
import re

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("LiveConsoleWidget")

from PyQt5.QtWidgets import QGroupBox, QGridLayout, QVBoxLayout, QLabel, QSizePolicy, QFrame
from PyQt5.QtCore import Qt

class LiveConsoleWidget(QGroupBox):
    """
    In-place update widget that refreshes only the current turbine status, numerical values, 
    Quality Gate status, Extraction Algorithm, Discarded Numbers in place within a fixed panel,
    styled for the clean light dashboard theme.
    """
    def __init__(self, title="📡 VENUS Turbine Drawing Machine Live Monitoring Panel (Live Status)", parent=None):
        super().__init__(title, parent)
        self.init_ui()

    def init_ui(self):
        grid_layout = QGridLayout(self)
        grid_layout.setContentsMargins(12, 12, 12, 12)
        grid_layout.setHorizontalSpacing(12)
        grid_layout.setVerticalSpacing(8)

        # Define fixed status items including Quality Gate Status, Algorithm, Discarded Numbers (System Resources removed)
        self.status_items = {
            "model": ("Machine Model:", "AKANIS TECHNOLOGIES - VENUS"),
            "status": ("System Status:", "System Ready"),
            "quality_gate": ("QUALITY GATE STATUS:", "Standby"),
            "algorithm": ("Extraction Algorithm:", "Standby"),
            "discarded_numbers": ("Discarded Combinations:", "None (0 filtered)"),
            "est_time": ("Estimated Time:", "Standby"),
            "rpm": ("Turbine Speed (RPM):", "0 RPM"),
            "aerodynamics": ("Aerodynamic Spec:", "Air Velocity 73~80 m/s (Cd: 0.47)"),
            "extraction": ("Current Extraction Step:", "Standby (0 / 7 balls)")
        }

        self.value_labels = {}
        
        positions = [
            (0, 0), (0, 1),
            (1, 0), (1, 1),
            (2, 0), (2, 1),
            (3, 0), (3, 1),
            (4, 0)
        ]

        keys = list(self.status_items.keys())
        for idx, key in enumerate(keys):
            if idx >= len(positions):
                break
            label_text, default_val = self.status_items[key]
            pos = positions[idx]

            item_layout = QVBoxLayout()
            item_layout.setContentsMargins(4, 4, 4, 4)
            item_layout.setSpacing(2)

            lbl_key = QLabel(label_text)
            lbl_key.setStyleSheet("font-weight: bold; color: #7f8c8d; font-size: 10px; border: none; background: transparent;")
            
            lbl_val = QLabel(default_val)
            lbl_val.setWordWrap(True)
            
            if key == "quality_gate":
                lbl_val.setStyleSheet("color: #d35400; font-weight: bold; font-family: 'Consolas', monospace; font-size: 11px; border: none; background: transparent;")
            elif key == "algorithm":
                lbl_val.setStyleSheet("color: #2980b9; font-weight: bold; font-family: 'Consolas', monospace; font-size: 11px; border: none; background: transparent;")
            elif key == "discarded_numbers":
                lbl_val.setStyleSheet("color: #c0392b; font-weight: bold; font-family: 'Consolas', monospace; font-size: 11px; border: none; background: transparent;")
            elif key == "est_time":
                lbl_val.setStyleSheet("color: #8e44ad; font-weight: bold; font-family: 'Consolas', monospace; font-size: 11px; border: none; background: transparent;")
            else:
                lbl_val.setStyleSheet("color: #16a085; font-weight: bold; font-family: 'Consolas', monospace; font-size: 11px; border: none; background: transparent;")

            item_layout.addWidget(lbl_key)
            item_layout.addWidget(lbl_val)

            frame = QFrame()
            frame.setLayout(item_layout)
            frame.setStyleSheet("""
                QFrame {
                    background-color: #fcfcfc;
                    border: 1px solid #e1e4e8;
                    border-radius: 6px;
                }
            """)

            grid_layout.addWidget(frame, pos[0], pos[1])
            self.value_labels[key] = lbl_val

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                font-size: 11px;
                color: #2c3e50;
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

    def update_status(self, discards, algo_title):
        """Updates Quality Gate status, extraction algorithm name, and discarded combinations in-place."""
        self.value_labels["quality_gate"].setText("Passed (Verified)")
        self.value_labels["quality_gate"].setStyleSheet("color: #27ae60; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
        
        if algo_title:
            self.value_labels["algorithm"].setText(str(algo_title))
        if discards is not None:
            self.value_labels["discarded_numbers"].setText(str(discards))
        _log.debug(f"LiveConsole status updated: algo={algo_title}")

    def update_live_telemetry(self, system_status: str, quality_gate: str, rpm: int, step_text: str):
        """Directly and reliably updates console telemetry fields."""
        try:
            if system_status:
                self.value_labels["status"].setText(str(system_status))
                if "Mixing" in system_status or "300s" in system_status:
                    self.value_labels["status"].setStyleSheet("color: #e67e22; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
                    # During the 300s mixing phase: Quality gate is Filtered & Verifying
                    self.value_labels["quality_gate"].setText("Filtered & Verifying")
                    self.value_labels["quality_gate"].setStyleSheet("color: #e67e22; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
                elif "Complete" in system_status:
                    self.value_labels["status"].setStyleSheet("color: #27ae60; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
                    self.value_labels["quality_gate"].setText("Passed (Verified)")
                    self.value_labels["quality_gate"].setStyleSheet("color: #27ae60; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
                elif "Drawing" in system_status or "Extraction" in system_status:
                    self.value_labels["status"].setStyleSheet("color: #2980b9; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
                    # Once drawing starts: Quality gate is Passed (Verified), Discarding stops
                    self.value_labels["quality_gate"].setText("Passed (Verified)")
                    self.value_labels["quality_gate"].setStyleSheet("color: #27ae60; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
                else:
                    self.value_labels["status"].setStyleSheet("color: #16a085; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")

            if quality_gate:
                self.value_labels["quality_gate"].setText(str(quality_gate))

            if rpm is not None:
                self.value_labels["rpm"].setText(f"{rpm:,} RPM")

            if step_text:
                self.value_labels["extraction"].setText(str(step_text))
        except Exception as e:
            _log.error(f"Error updating live telemetry: {e}")

    def log_message(self, msg: str):
        """Analyzes external log messages and updates UI fields accordingly based on session phases."""
        # 1. Discarded combinations: Active during mixing (300s), paused/frozen once drawing starts
        if "Discard" in msg or "discard" in msg or "Filtered" in msg or "filtered" in msg:
            # Check if drawing has already started to halt filtering updates
            current_status = self.value_labels["status"].text()
            if "Drawing" not in current_status and "Extraction" not in current_status and "Complete" not in current_status:
                match = re.search(r'(?:Discarded|filtered)[:\s]*([\d,]+)', msg, re.IGNORECASE)
                if match:
                    extracted_val = f"{match.group(1)} filtered"
                    self.value_labels["discarded_numbers"].setText(extracted_val)
                else:
                    self.value_labels["discarded_numbers"].setText(msg)
            return

        if "Est. Time" in msg or "remaining" in msg:
            self.value_labels["est_time"].setText(msg)
            return

        if "RPM" in msg:
            if "➔" in msg:
                rpm_val = msg.split("➔")[-1].strip()
                self.value_labels["rpm"].setText(rpm_val)
            else:
                self.value_labels["rpm"].setText(msg)
            
            # Transition to mixing phase (300s mixing active)
            self.value_labels["status"].setText("Turbine Mixing (Filtering 300s)")
            self.value_labels["status"].setStyleSheet("color: #e67e22; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
            self.value_labels["quality_gate"].setText("Filtered & Verifying")
            self.value_labels["quality_gate"].setStyleSheet("color: #e67e22; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
            self.value_labels["est_time"].setText("05:00 remaining (Mixing)")

        elif "Extraction" in msg or "Main Ball" in msg or "Bonus Ball" in msg or "extraction" in msg or "main" in msg or "bonus" in msg:
            self.value_labels["extraction"].setText(msg)
            # Drawing has started: Halt discarding updates, set Quality Gate to Passed (Verified), show drawing estimate
            self.value_labels["status"].setText("Ball Extraction in Progress (Drawing)")
            self.value_labels["status"].setStyleSheet("color: #2980b9; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
            self.value_labels["quality_gate"].setText("Passed (Verified)")
            self.value_labels["quality_gate"].setStyleSheet("color: #27ae60; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
            self.value_labels["est_time"].setText("Drawing in Progress")
            
            if "complete" in msg or "Complete" in msg or "landing" in msg or "Landing" in msg:
                self.value_labels["status"].setText("1 Set Drawing Complete")
                self.value_labels["status"].setStyleSheet("color: #27ae60; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")

        elif "preparation complete" in msg or "Preparation" in msg or "Ready" in msg or "prepare" in msg:
            # Standby phase before mixing/drawing starts
            self.value_labels["extraction"].setText("Standby (0 / 7 balls)")
            self.value_labels["status"].setText("System Ready")
            self.value_labels["status"].setStyleSheet("color: #16a085; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
            self.value_labels["quality_gate"].setText("Standby")
            self.value_labels["quality_gate"].setStyleSheet("color: #d35400; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
            self.value_labels["algorithm"].setText("Standby")
            self.value_labels["discarded_numbers"].setText("None (0 filtered)")
            self.value_labels["est_time"].setText("Standby")

        elif "initialization complete" in msg or "Initialization" in msg or "saved successfully" in msg or "Saved" in msg:
            self.value_labels["status"].setText("System Ready")
            self.value_labels["status"].setStyleSheet("color: #16a085; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
            self.value_labels["rpm"].setText("0 RPM")
            self.value_labels["quality_gate"].setText("Standby")
            self.value_labels["quality_gate"].setStyleSheet("color: #d35400; font-weight: bold; font-family: Consolas; font-size: 11px; border: none; background: transparent;")
            self.value_labels["algorithm"].setText("Standby")
            self.value_labels["est_time"].setText("Standby")