# -*- coding: utf-8 -*-
# ui/widgets/consecutive_widget.py
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("ConsecutiveWidget")

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QSizePolicy
from PyQt5.QtCore import Qt
from data.repositories.lotto_repository import LottoRepository


class ConsecutiveWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Co-occurrence Rate", parent)
        self.init_ui()
        self.load_consecutive_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(12)
        
        self.bars = {}
        categories = ["2 Numbers", "3 Numbers", "4 Numbers"]
        
        colors = {
            "2 Numbers": "#16a085",
            "3 Numbers": "#2980b9",
            "4 Numbers": "#8e44ad"
        }
        
        for cat in categories:
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            lbl = QLabel(cat)
            lbl.setFixedWidth(80)
            lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: #2c3e50;")
            
            pbar = QProgressBar()
            pbar.setRange(0, 100)
            pbar.setValue(0)
            pbar.setTextVisible(True)
            pbar.setFormat("%v%")
            pbar.setFixedHeight(18)
            
            chunk_color = colors.get(cat, "#16a085")
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #ecf0f1;
                    border: none;
                    border-radius: 4px;
                    text-align: right;
                    font-size: 8.5px;
                    color: #7f8c8d;
                    padding-right: 6px;
                }}
                QProgressBar::chunk {{
                    background-color: {chunk_color};
                    border-radius: 4px;
                }}
            """)
            
            row_layout.addWidget(lbl)
            row_layout.addWidget(pbar)
            layout.addLayout(row_layout)
            self.bars[cat] = pbar

        self.setFixedWidth(400)
        self.setFixedHeight(175)
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

    def load_consecutive_data(self):
        try:
            draws = LottoRepository.get_all_draws()
            if not draws:
                return

            counts = {"2 Numbers": 0, "3 Numbers": 0, "4 Numbers": 0}
            
            for draw in draws:
                nums = []
                for i in range(1, 7):
                    val = draw.get(f"num{i}") or draw.get(f"drwtNo{i}") or 0
                    if val:
                        nums.append(int(val))
                
                nums = sorted([n for n in nums if n > 0])
                if len(nums) < 6:
                    continue

                i = 0
                max_group_size = 1
                while i < len(nums):
                    group_size = 1
                    j = i
                    while j + 1 < len(nums) and nums[j+1] == nums[j] + 1:
                        group_size += 1
                        j += 1
                    if group_size > max_group_size:
                        max_group_size = group_size
                    i = max(i + 1, j + 1)

                if max_group_size == 2:
                    counts["2 Numbers"] += 1
                elif max_group_size == 3:
                    counts["3 Numbers"] += 1
                elif max_group_size >= 4:
                    counts["4 Numbers"] += 1

            self.update_metric(counts)
        except Exception as e:
            _log.error(f"Failed to load consecutive data: {e}")

    def update_metric(self, data):
        try:
            if isinstance(data, dict):
                total = sum(data.values()) if sum(data.values()) > 0 else 1
                for cat, val in data.items():
                    if cat in self.bars:
                        pct = int((val / total) * 100) if isinstance(val, (int, float)) else int(val)
                        self.bars[cat].setValue(min(100, max(0, pct)))
        except Exception as e:
            _log.error(f"Error updating ConsecutiveWidget: {e}")
            
    def update_data(self, data):
        self.update_metric(data)

    def load_data(self):
        self.load_consecutive_data()