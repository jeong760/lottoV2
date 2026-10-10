# ui/widgets/official_history_widget.py
import sys
import os
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("OfficialHistoryWidget")

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt5.QtCore import Qt
from data.repositories.lotto_repository import LottoRepository


class OfficialHistoryWidget(QWidget):
    """Widget displaying official lotto draw history from draw #1 to latest stored in db/lottomater.db"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_official_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title_label = QLabel("Official Lotto Draw Records (Draw #1 to Latest)")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        layout.addWidget(title_label)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Round", "Date", "N1", "N2", "N3", "N4", "N5", "N6", "Bonus"
        ])
        
        header = self.table.horizontalHeader()
        for i in range(9):
            if 2 <= i <= 8:
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                self.table.setColumnWidth(i, 50)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                gridline-color: #f1f2f6;
                font-size: 11px;
                color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #dcdde1;
            }
        """)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_official_data(self):
        """Loads all draw records from LottoRepository and populates the table accurately with forced redraw."""
        try:
            self.table.setRowCount(0)
            draws = LottoRepository.get_all_draws()
            
            if not draws:
                _log.info("No official draw records found in DB.")
                return

            self.table.setRowCount(len(draws))
            for row, draw in enumerate(draws):
                if isinstance(draw, dict):
                    d_no = draw.get("draw_no") or draw.get("drwNo") or 0
                    d_date = draw.get("draw_date") or draw.get("drwNoDate") or ""
                    nums = [
                        draw.get("num1") or draw.get("drwtNo1") or 0,
                        draw.get("num2") or draw.get("drwtNo2") or 0,
                        draw.get("num3") or draw.get("drwtNo3") or 0,
                        draw.get("num4") or draw.get("drwtNo4") or 0,
                        draw.get("num5") or draw.get("drwtNo5") or 0,
                        draw.get("num6") or draw.get("drwtNo6") or 0
                    ]
                    bonus = draw.get("bonus") or draw.get("bnusNo") or 0
                else:
                    d_no, d_date = draw[0], draw[1]
                    nums = [draw[i] for i in range(2, 8)]
                    bonus = draw[8] if len(draw) > 8 else 0

                # Set Round
                item_round = QTableWidgetItem(str(d_no))
                item_round.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 0, item_round)

                # Set Date
                item_date = QTableWidgetItem(str(d_date))
                item_date.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, item_date)

                # Set Main 6 Numbers
                for i, num in enumerate(nums):
                    item = QTableWidgetItem(f"{int(num):02d}" if num else "-")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 2 + i, item)
                
                # Set Bonus Number
                b_item = QTableWidgetItem(f"{int(bonus):02d}" if bonus else "-")
                b_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 8, b_item)

            # Force viewport update/redraw to guarantee records are rendered immediately on screen
            self.table.viewport().update()
            _log.info(f"Loaded and displayed {len(draws)} official draw records into table.")
        except Exception as e:
            _log.error(f"Failed to load official draw records into table: {e}")

    def load_draw_data(self):
        """Alias method for compatibility with launcher/main window calls."""
        self.load_official_data()