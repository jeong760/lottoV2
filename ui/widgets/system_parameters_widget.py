# ui/widgets/system_parameters_widget.py
import logging
import os
import sys

# Ensure project root is in python path and initialize centralized logging
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("SystemParametersWidget")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit, QComboBox, QSizePolicy
from PyQt5.QtCore import Qt
from core.algorithm_catalog import get_mode_titles, get_mode_title, resolve_algorithm_mode_id

class ParameterRow(QWidget):
    """A clean key-value input row for system parameters."""
    def __init__(self, label_text: str, default_value: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)

        self.lbl_name = QLabel(label_text)
        self.lbl_name.setStyleSheet("font-size: 11px; color: #2c3e50; font-weight: bold; border: none; background: transparent;")
        
        self.input_field = QLineEdit(default_value)
        self.input_field.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.input_field.setFixedSize(110, 26)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #dcdde1;
                border-radius: 4px;
                padding: 0px 6px;
            }
            QLineEdit:focus {
                border: 1px solid #2980b9;
                background-color: #ffffff;
            }
        """)

        layout.addWidget(self.lbl_name)
        layout.addStretch()
        layout.addWidget(self.input_field)

    def get_value(self) -> str:
        return self.input_field.text()

    def set_value(self, val: str):
        self.input_field.setText(val)


class ParameterComboRow(QWidget):
    """A clean key-dropdown row for select parameters like Draw Type."""
    def __init__(self, label_text: str, options: list, default_option: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)

        self.lbl_name = QLabel(label_text)
        self.lbl_name.setStyleSheet("font-size: 11px; color: #2c3e50; font-weight: bold; border: none; background: transparent;")
        
        self.combo = QComboBox()
        self.combo.addItems(options)
        if default_option in options:
            self.combo.setCurrentText(default_option)
        self.combo.setFixedSize(130, 26)
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #dcdde1;
                border-radius: 4px;
                padding: 0px 6px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 0px;
            }
        """)

        layout.addWidget(self.lbl_name)
        layout.addStretch()
        layout.addWidget(self.combo)

    def get_current_text(self) -> str:
        return self.combo.currentText()


class SystemParametersWidget(QFrame):
    """
    System Parameters Dashboard Widget styled for the clean light dashboard theme.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # Clean Light Theme Card Styling
        self.setStyleSheet("""
            SystemParametersWidget {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 8px;
            }
        """)

        # Header Title & View All Action Row
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel("SYSTEM PARAMETERS")
        title_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #7f8c8d; letter-spacing: 1px; border: none; background: transparent;")

        self.lbl_view_all = QLabel("View All")
        self.lbl_view_all.setStyleSheet("font-size: 11px; font-weight: bold; color: #2980b9; border: none; background: transparent;")
        self.lbl_view_all.setCursor(Qt.PointingHandCursor)

        header_layout.addWidget(title_lbl, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_view_all, alignment=Qt.AlignRight)
        main_layout.addLayout(header_layout)

        # 2-Column Parameters Layout
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(20)

        # Left Column Parameters
        left_col_widget = QWidget()
        left_col_layout = QVBoxLayout(left_col_widget)
        left_col_layout.setContentsMargins(0, 0, 0, 0)
        left_col_layout.setSpacing(6)

        self.param_pool_size = ParameterRow("Ball Pool Size", "45")
        self.param_main_balls = ParameterRow("Main Balls", "6")
        self.param_bonus_balls = ParameterRow("Bonus Balls", "1")
        self.param_turbine_rpm = ParameterRow("Turbine Speed (RPM)", "9000")
        self.param_mix_duration = ParameterRow("Mix Duration (sec)", "300")

        left_col_layout.addWidget(self.param_pool_size)
        left_col_layout.addWidget(self.param_main_balls)
        left_col_layout.addWidget(self.param_bonus_balls)
        left_col_layout.addWidget(self.param_turbine_rpm)
        left_col_layout.addWidget(self.param_mix_duration)

        # Right Column Parameters
        right_col_widget = QWidget()
        right_col_layout = QVBoxLayout(right_col_widget)
        right_col_layout.setContentsMargins(0, 0, 0, 0)
        right_col_layout.setSpacing(6)

        self.param_draw_interval = ParameterRow("Draw Interval (sec)", "10.0")
        self.param_training_set = ParameterRow("Training Set", "100")
        self.param_repeat = ParameterRow("Repeat", "1")
        self.param_drawing_count = ParameterRow("Drawing Count", "10")
        self.param_draw_type = ParameterComboRow("Draw Type", ["Live Draw", "Instant Simulation", "Batch Ensemble"], "Live Draw")
        self.param_algorithm_mode = ParameterComboRow(
            "Algorithm Mode",
            get_mode_titles(include_random=False),
            get_mode_title("ensemble_auto")
        )

        right_col_layout.addWidget(self.param_draw_interval)
        right_col_layout.addWidget(self.param_training_set)
        right_col_layout.addWidget(self.param_repeat)
        right_col_layout.addWidget(self.param_drawing_count)
        right_col_layout.addWidget(self.param_draw_type)
        right_col_layout.addWidget(self.param_algorithm_mode)

        columns_layout.addWidget(left_col_widget, stretch=1)
        columns_layout.addWidget(right_col_widget, stretch=1)

        main_layout.addLayout(columns_layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        _log.info("SystemParametersWidget initialized successfully.")

    def get_turbine_rpm(self) -> int:
        """Returns the turbine RPM specified in the parameters widget."""
        try:
            val = int(self.param_turbine_rpm.get_value())
            _log.debug(f"Retrieved turbine RPM: {val}")
            return val
        except ValueError:
            _log.warning("Invalid turbine RPM value specified. Falling back to default: 9000")
            return 9000  # Default fallback RPM

    def get_mix_duration(self) -> int:
        """Returns the mix duration in seconds specified in the parameters widget."""
        try:
            val = int(self.param_mix_duration.get_value())
            _log.debug(f"Retrieved mix duration: {val}")
            return val
        except ValueError:
            _log.warning("Invalid mix duration value specified. Falling back to default: 300")
            return 300  # Default fallback duration

    def get_selected_algorithm_id(self) -> str:
        """Returns the stable algorithm mode ID selected by the user."""
        try:
            selected_title = self.param_algorithm_mode.get_current_text()
            return resolve_algorithm_mode_id(selected_title)
        except Exception:
            return "ensemble_auto"

    def get_selected_algorithm(self) -> str:
        """Returns the display title for the selected algorithm mode."""
        return get_mode_title(self.get_selected_algorithm_id())