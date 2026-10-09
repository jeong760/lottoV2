# ui/widgets/official_draw_history_widget.py
import sys
import os
import logging

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("OfficialDrawHistoryWidget")

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush
from data.repositories.lotto_repository import LottoRepository


class NumericTableWidgetItem(QTableWidgetItem):
    """
    Custom QTableWidgetItem ensuring correct numerical sorting for monetary values, amounts, and round numbers.
    """
    def __init__(self, text, sort_value):
        super().__init__(text)
        self.sort_value = sort_value

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)


class OfficialDrawHistoryWidget(QWidget):
    """
    Widget displaying official historical draw records (1st round to latest) 
    with full 1st~5th prize details including total and individual prizes.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_draw_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Header Title and Refresh Button
        header_layout = QHBoxLayout()
        title_label = QLabel("📊 Official Historical Lotto 6/45 Draw & Prize Statistics")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        
        self.refresh_btn = QPushButton("Refresh Official Draws")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_draw_data)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)

        # Table Setup with Expanded Columns for 1st ~ 5th Full Details (Total 26 columns)
        self.table = QTableWidget()
        self.table.setColumnCount(26)
        self.table.setHorizontalHeaderLabels([
            "Draw Date", "Round", "N1", "N2", "N3", "N4", "N5", "N6", "Bonus",
            "Total Sales", 
            "1st Winners", "1st Total Prize", "1st Prize/Winner",
            "2nd Winners", "2nd Total Prize", "2nd Prize/Winner",
            "3rd Winners", "3rd Total Prize", "3rd Prize/Winner",
            "4th Winners", "4th Total Prize", "4th Prize/Winner",
            "5th Winners", "5th Total Prize", "5th Prize/Winner",
            "Status"
        ])
        
        # Disable cell editing on double-click to prevent user modifications
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.table.setSortingEnabled(True)

        # Generous vertical row height spacing
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        for i in range(26):
            if 2 <= i <= 7:  # Lotto balls N1~N6
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                self.table.setColumnWidth(i, 46)
            elif i == 8:  # Bonus column
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                self.table.setColumnWidth(i, 58)
            elif i in [9, 11, 12, 14, 15, 17, 18, 20, 21, 23, 24]:  # Sales and Prize columns
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
                self.table.setColumnWidth(i, max(110, self.table.columnWidth(i)))
            else:  # Winners count and other columns
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                gridline-color: #f1f2f6;
                font-size: 11px;
                selection-background-color: #3498db;
                selection-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-weight: bold;
                padding: 8px 6px;
                border: 1px solid #dcdde1;
                border-bottom: 2px solid #bdc3c7;
            }
            QTableWidget::item {
                padding: 6px 8px;
            }
        """)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def _get_val(self, draw: dict, keys: list, default=0):
        """Helper to safely extract value by checking multiple candidate keys."""
        if not isinstance(draw, dict):
            return default
        for key in keys:
            if key in draw and draw[key] is not None:
                val = draw[key]
                if isinstance(val, str) and val.strip() != "":
                    cleaned = val.replace(",", "").replace("KRW", "").strip()
                    if cleaned.replace(".", "", 1).isdigit():
                        try:
                            return float(cleaned) if "." in cleaned else int(cleaned)
                        except ValueError:
                            pass
                return val
        return default

    def _get_lotto_ball_color(self, num: int, is_bonus: bool = False):
        if is_bonus:
            return "#e74c3c"
        return "#2c3e50"

    def load_draw_data(self):
        """Fetches all official historical draws from DB and populates full 1st~5th statistics table."""
        try:
            self.table.setSortingEnabled(False)
            self.table.setRowCount(0)

            draws = LottoRepository.get_all_draws()
            if not draws:
                _log.warning("No official draw records found in local database.")
                self.table.setSortingEnabled(True)
                return

            draws = sorted(draws, key=lambda d: int(self._get_val(d, ["draw_no", "drwNo", "round", "회차"], 0)))

            self.table.setRowCount(len(draws))
            for row, draw in enumerate(draws):
                # 1. Draw Date
                date_val = self._get_val(draw, ["draw_date", "drwNoDate", "drwDate", "추첨일"], "-")
                item_date = QTableWidgetItem(str(date_val))
                item_date.setTextAlignment(Qt.AlignCenter)
                item_date.setFont(QFont("Segoe UI", 9))
                self.table.setItem(row, 0, item_date)

                # 2. Round
                round_val = int(self._get_val(draw, ["draw_no", "drwNo", "round", "회차"], 0))
                item_round = NumericTableWidgetItem(f"#{round_val}" if round_val > 0 else "-", round_val)
                item_round.setTextAlignment(Qt.AlignCenter)
                item_round.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item_round.setForeground(QColor("#2980b9"))
                self.table.setItem(row, 1, item_round)

                # 3. N1 ~ N6 Numbers
                for i in range(1, 7):
                    num_val = int(self._get_val(draw, [f"num{i}", f"drwtNo{i}", f"number{i}", f"번호{i}"], 0))
                    val_str = f"{num_val:02d}" if num_val > 0 else "-"
                    item_num = NumericTableWidgetItem(val_str, num_val)
                    item_num.setTextAlignment(Qt.AlignCenter)
                    item_num.setFont(QFont("Consolas", 9, QFont.Bold))
                    item_num.setForeground(QBrush(QColor(self._get_lotto_ball_color(num_val))))
                    self.table.setItem(row, 1 + i, item_num)

                # 4. Bonus Number
                b_val = int(self._get_val(draw, ["bonus", "bnusNo", "bonus_no", "보너스"], 0))
                b_str = f"{b_val:02d}" if b_val > 0 else "-"
                item_bonus = NumericTableWidgetItem(b_str, b_val)
                item_bonus.setTextAlignment(Qt.AlignCenter)
                item_bonus.setFont(QFont("Consolas", 9, QFont.Bold))
                item_bonus.setForeground(QBrush(QColor(self._get_lotto_ball_color(b_val, is_bonus=True))))
                self.table.setItem(row, 8, item_bonus)

                # 5. Total Sales
                sales_val = int(self._get_val(draw, ["tot_sellamnt", "totSellamnt", "total_sales", "sales", "총판매금액"], 0))
                sales_str = f"{sales_val:,} KRW" if sales_val > 0 else "-"
                item_sales = NumericTableWidgetItem(sales_str, sales_val)
                item_sales.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_sales.setFont(QFont("Segoe UI", 9))
                self.table.setItem(row, 9, item_sales)

                # --- Prize Tiers 1 ~ 3 Statistics ---
                tiers = [
                    (1, 10, 11, 12, "first_przwner_co", "first_accumamnt", "first_winamnt"),
                    (2, 13, 14, 15, "second_przwner_co", "second_accumamnt", "second_winamnt"),
                    (3, 16, 17, 18, "third_przwner_co", "third_accumamnt", "third_winamnt")
                ]
                for rank, col_w, col_tot, col_each, k_co, k_tot, k_each in tiers:
                    w_count = int(self._get_val(draw, [k_co, f"{rank}등_게임수"], 0))
                    p_each = int(self._get_val(draw, [k_each, f"{rank}등_1게임당"], 0))
                    p_total = int(self._get_val(draw, [k_tot, f"{rank}등_총당첨금"], 0))
                    if p_total == 0 and w_count > 0 and p_each > 0:
                        p_total = w_count * p_each

                    item_w = NumericTableWidgetItem(f"{w_count:,}" if w_count > 0 else "0", w_count)
                    item_w.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, col_w, item_w)

                    item_p_tot = NumericTableWidgetItem(f"{p_total:,} KRW" if p_total > 0 else "-", p_total)
                    item_p_tot.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, col_tot, item_p_tot)
                    
                    item_p_each = NumericTableWidgetItem(f"{p_each:,} KRW" if p_each > 0 else "-", p_each)
                    item_p_each.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item_p_each.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    if rank == 1:
                        item_p_each.setForeground(QColor("#27ae60"))
                    self.table.setItem(row, col_each, item_p_each)

                # --- Prize Tiers 4 & 5 Statistics (Fixed Prizes: 4th=50,000, 5th=5,000) ---
                fixed_tiers = [
                    (4, 19, 20, 21, "fourth_przwner_co", "fourth_accumamnt", "fourth_winamnt", 50000),
                    (5, 22, 23, 24, "fifth_przwner_co", "fifth_accumamnt", "fifth_winamnt", 5000)
                ]
                for rank, col_w, col_tot, col_each, k_co, k_tot, k_each, default_prize in fixed_tiers:
                    w_count = int(self._get_val(draw, [k_co, f"{rank}등_게임수"], 0))
                    p_each = int(self._get_val(draw, [k_each], default_prize))
                    if p_each <= 0:
                        p_each = default_prize
                    p_total = int(self._get_val(draw, [k_tot], w_count * p_each))
                    if p_total == 0 and w_count > 0:
                        p_total = w_count * p_each

                    item_w = NumericTableWidgetItem(f"{w_count:,}" if w_count > 0 else "0", w_count)
                    item_w.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, col_w, item_w)

                    item_p_tot = NumericTableWidgetItem(f"{p_total:,} KRW" if p_total > 0 else "-", p_total)
                    item_p_tot.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, col_tot, item_p_tot)

                    item_p_each = NumericTableWidgetItem(f"{p_each:,} KRW" if p_each > 0 else "-", p_each)
                    item_p_each.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, col_each, item_p_each)

                # Status Column
                item_status = QTableWidgetItem("Verified")
                item_status.setTextAlignment(Qt.AlignCenter)
                item_status.setForeground(QColor("#2980b9"))
                self.table.setItem(row, 25, item_status)

            self.table.setSortingEnabled(True)
            _log.info("Official draw history loaded successfully with full 1st~5th statistics columns.")

        except Exception as e:
            _log.error(f"Failed to load official draw history data: {e}")