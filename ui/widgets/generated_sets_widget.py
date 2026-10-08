# -*- coding: utf-8 -*-
# ui/widgets/generated_sets_widget.py
import sys
import os
import logging
import csv

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("GeneratedSetsWidget")

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QHBoxLayout, QHeaderView, QCheckBox, QFileDialog, QMessageBox, QWidget as QW,
    QAbstractItemView, QDialog, QLabel, QTextBrowser
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QBrush
from data.lotto_db_helper import LottoDBHelper
from core.lotto_evaluator import LottoEvaluator

try:
    import pandas as pd
except ImportError:
    pd = None


class BonusSwapDialog(QDialog):
    """Dialog window displaying bonus swap optimization simulation results."""
    def __init__(self, optimization_result: dict, parent=None):
        super().__init__(parent)
        self.result = optimization_result
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Bonus Swap Optimizer Analysis")
        self.resize(550, 450)
        self.setStyleSheet("background-color: #f8f9fa;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title_lbl = QLabel("[Bonus Number Swap & Rank Optimizer]")
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_lbl.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_lbl)

        orig_set = self.result.get("original_set", [])
        orig_matches = self.result.get("original_matches", 0)
        bonus = self.result.get("bonus_number", 0)

        info_text = (
            f"<b>Original Generated Set:</b> {orig_set} (Current Matches: {orig_matches})<br>"
            f"<b>Available Bonus Number:</b> <font color='#e74c3c'><b>{bonus:02d}</b></font><br>"
            f"<i>Replacing 1 number with the bonus number yields the following simulations:</i><br><br>"
        )

        info_lbl = QLabel(info_text)
        info_lbl.setFont(QFont("Segoe UI", 10))
        layout.addWidget(info_lbl)

        self.browser = QTextBrowser()
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        
        simulations = self.result.get("all_simulations", [])
        html_content = "<b>--- All Swap Combinations (Rank & Match Analysis) ---</b><br><br>"
        
        for idx, sim in enumerate(simulations, 1):
            rank_color = "#27ae60" if sim['rank'] != "Miss" else "#e74c3c"
            html_content += (
                f"<b>#{idx} Swap:</b> Remove <font color='#c0392b'><b>{sim['removed']:02d}</b></font> "
                f"-> Add Bonus <font color='#2980b9'><b>{sim['added']:02d}</b></font><br>"
                f"&nbsp;&nbsp;* New Set: <b>{sim['new_set']}</b><br>"
                f"&nbsp;&nbsp;* Matches: {sim['matches']} | Rank: <font color='{rank_color}'><b>{sim['rank']}</b></font><br><br>"
            )

        self.browser.setHtml(html_content)
        layout.addWidget(self.browser)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9; color: white; font-weight: bold;
                padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #3498db; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)


class GeneratedSetsWidget(QWidget):
    """
    Widget to display and track a history of lotto number sets.
    Features selection checkboxes with select/deselect all, sequential IDs, Rank column, 
    dynamic color-coded matches/probabilities with Gold for 1st place, Excel export options,
    and Bonus Swap Optimizer integration.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_generated_sets()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        top_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9; color: white; font-weight: bold;
                padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #3498db; }
        """)
        refresh_btn.clicked.connect(self.load_generated_sets)

        select_all_btn = QPushButton("Select All")
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d; color: white; font-weight: bold;
                padding: 6px 12px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #95a5a6; }
        """)
        select_all_btn.clicked.connect(lambda: self.set_all_checkboxes(True))

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d; color: white; font-weight: bold;
                padding: 6px 12px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #95a5a6; }
        """)
        deselect_all_btn.clicked.connect(lambda: self.set_all_checkboxes(False))

        optimize_btn = QPushButton("Bonus Swap Optimizer")
        optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #d35400; color: white; font-weight: bold;
                padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #e67e22; }
        """)
        optimize_btn.clicked.connect(self.run_bonus_swap_optimizer)

        export_all_btn = QPushButton("Export All to Excel")
        export_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white; font-weight: bold;
                padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        export_all_btn.clicked.connect(lambda: self.export_to_excel(selected_only=False))

        export_selected_btn = QPushButton("Export Selected to Excel")
        export_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; color: white; font-weight: bold;
                padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #9b59b6; }
        """)
        export_selected_btn.clicked.connect(lambda: self.export_to_excel(selected_only=True))

        top_layout.addWidget(refresh_btn)
        top_layout.addWidget(select_all_btn)
        top_layout.addWidget(deselect_all_btn)
        top_layout.addWidget(optimize_btn)
        top_layout.addWidget(export_all_btn)
        top_layout.addWidget(export_selected_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        headers = [
            "Select", "ID", "Date", "Round", "Algorithm", 
            "N1", "N2", "N3", "N4", "N5", "N6", "Bonus", 
            "Rounds", "Matches", "Rank", "Probability"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #dcdde1;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                selection-background-color: #3498db;
            }
            QHeaderView::section {
                background-color: #f1f2f6;
                color: #2c3e50;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #dcdde1;
            }
        """)
        
        header = self.table.horizontalHeader()
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

    def _get_alpha_label(self, index: int) -> str:
        """
        Generates a continuous sequence label based on row index without resets:
        - 0 ~ 25 (Index 0~25): SET A ~ SET Z
        - 26 ~ 51 (Index 26~51): SET A0 ~ SET Z25
        - 52 and above (Index 52+): SET A26, SET B27, ...
        """
        if index < 26:
            return f"SET {chr(ord('A') + index)}"
        elif index < 52:
            sub_idx = index - 26
            return f"SET {chr(ord('A') + sub_idx)}{sub_idx}"
        else:
            sub_idx = index - 26
            return f"SET A{sub_idx}"

    def set_all_checkboxes(self, check_state: bool):
        try:
            for row in range(self.table.rowCount()):
                cell_widget = self.table.cellWidget(row, 0)
                if cell_widget:
                    chk = cell_widget.findChild(QCheckBox)
                    if chk:
                        chk.setChecked(check_state)
        except Exception as e:
            _log.error(f"Failed to batch update checkboxes: {e}")

    def load_generated_sets(self):
        try:
            self.table.setSortingEnabled(False)
            self.table.setRowCount(0)

            history_records = LottoDBHelper.get_generation_history() if hasattr(LottoDBHelper, 'get_generation_history') else []
            if not history_records:
                _log.warning("No generated number sets found in local database.")
                self.table.setSortingEnabled(True)
                return

            self.table.setRowCount(len(history_records))
            for row, record in enumerate(history_records):
                seq_id = row + 1
                rec_date = record.get("created_at", record.get("date", record.get("timestamp", "-")))
                rec_round = self._get_alpha_label(row)
                rec_title = record.get("algorithm_title", record.get("title", record.get("algorithm", "AI Ensemble")))
                
                numbers = record.get("numbers", record.get("set_numbers", record.get("nums", [])))
                if not numbers and isinstance(record, dict):
                    flat_nums = []
                    for k in ["n1", "n2", "n3", "n4", "n5", "n6", "bonus", "num1", "num2", "num3", "num4", "num5", "num6", "drwtNo6"]:
                        if k in record:
                            flat_nums.append(record[k])
                    if flat_nums:
                        numbers = flat_nums

                if not isinstance(numbers, (list, tuple)):
                    numbers = [0] * 7
                elif len(numbers) < 7:
                    numbers = list(numbers) + [0] * (7 - len(numbers))

                match_count = record.get("match_count", record.get("matches", record.get("matched", 0)))
                rounds_info = record.get("rounds_info", "-")
                prob_str = record.get("probability_str", "0.00%")

                has_bonus = "2nd" in rounds_info or "5+B" in rounds_info or "Bonus" in rounds_info
                rank_label = LottoEvaluator.get_rank_label(match_count, has_bonus)
                
                if rank_label == "-" and "1st" in prob_str:
                    rank_label = "1st"
                elif rank_label == "-" and "2nd" in prob_str:
                    rank_label = "2nd (5+B)"
                elif rank_label == "-" and "3rd" in prob_str:
                    rank_label = "3rd (5 Matches)"

                # 0. Select Checkbox Column
                chk_container = QW()
                chk_layout = QHBoxLayout(chk_container)
                chk_box = QCheckBox()
                chk_box.setChecked(False)
                chk_layout.addWidget(chk_box)
                chk_layout.setAlignment(Qt.AlignCenter)
                chk_layout.setContentsMargins(0, 0, 0, 0)
                self.table.setCellWidget(row, 0, chk_container)

                # 1. Sequential ID Item
                item_id = QTableWidgetItem(str(seq_id))
                item_id.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, item_id)

                # 2. Date Item
                item_date = QTableWidgetItem(str(rec_date))
                item_date.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, item_date)

                # 3. Round Info Item
                item_round = QTableWidgetItem(str(rec_round))
                item_round.setTextAlignment(Qt.AlignCenter)
                item_round.setForeground(QColor("#2980b9"))
                item_round.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.table.setItem(row, 3, item_round)

                # 4. Title Item
                item_title = QTableWidgetItem(str(rec_title))
                item_title.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item_title.setForeground(QColor("#2c3e50"))
                self.table.setItem(row, 4, item_title)

                # 5. Numbers (N1 ~ N6 & Bonus)
                for i in range(7):
                    val = int(numbers[i]) if i < len(numbers) and numbers[i] is not None else 0
                    val_str = f"{val:02d}" if val > 0 else "-"
                    item_num = QTableWidgetItem(val_str)
                    item_num.setTextAlignment(Qt.AlignCenter)
                    item_num.setFont(QFont("Consolas", 9, QFont.Bold))
                    if i == 6:
                        item_num.setForeground(QBrush(QColor("#e74c3c")))
                    else:
                        item_num.setForeground(QBrush(QColor("#2c3e50")))
                    self.table.setItem(row, 5 + i, item_num)

                # --- Custom Color Mapping ---
                match_color = QColor("#2c3e50")
                prob_color = QColor("#7f8c8d")
                rank_color = QColor("#7f8c8d")
                font_weight = QFont.Normal

                if match_count == 0:
                    match_color = QColor("#e74c3c")
                    prob_color = QColor("#e74c3c")
                elif match_count in [1, 2]:
                    match_color = QColor("#e3872d")
                    prob_color = QColor("#e3872d")
                elif match_count == 3:
                    match_color = QColor("#27ae60")
                    prob_color = QColor("#27ae60")
                    rank_color = QColor("#27ae60")
                elif match_count == 4:
                    match_color = QColor("#2980b9")
                    prob_color = QColor("#2980b9")
                    rank_color = QColor("#2980b9")
                elif match_count == 5:
                    match_color = QColor("#8e44ad")
                    prob_color = QColor("#8e44ad")
                    rank_color = QColor("#e67e22") if "5+B" in rank_label else QColor("#8e44ad")
                elif match_count >= 6:
                    match_color = QColor("#d4ac0d")
                    prob_color = QColor("#d4ac0d")
                    rank_color = QColor("#d4ac0d")
                    font_weight = QFont.Bold

                # --- 12. Rounds Column ---
                draw_only_rounds = "-"
                if rounds_info and rounds_info != "-":
                    extracted_draws = []
                    parts = [p.strip() for p in rounds_info.split(",") if p.strip()]
                    for part in parts:
                        draw_num = part.split()[0] if part else ""
                        if draw_num and draw_num not in extracted_draws:
                            extracted_draws.append(draw_num)
                    
                    if extracted_draws:
                        if len(extracted_draws) > 3:
                            draw_only_rounds = f"{', '.join(extracted_draws[:3])} ... (+{len(extracted_draws) - 3})"
                        else:
                            draw_only_rounds = ", ".join(extracted_draws)

                item_rounds_info = QTableWidgetItem(str(draw_only_rounds))
                if rounds_info and rounds_info != "-":
                    item_rounds_info.setToolTip(str(rounds_info))
                item_rounds_info.setTextAlignment(Qt.AlignCenter)
                item_rounds_info.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item_rounds_info.setForeground(QColor("#16a085") if rounds_info != "-" else QColor("#95a5a6"))
                self.table.setItem(row, 12, item_rounds_info)

                # 13. Match Count Item
                item_match = QTableWidgetItem(f"{match_count} Matches" if match_count > 0 else "0 Match")
                item_match.setTextAlignment(Qt.AlignCenter)
                item_match.setFont(QFont("Segoe UI", 9, font_weight))
                item_match.setForeground(match_color)
                self.table.setItem(row, 13, item_match)

                # 14. Rank Column
                display_rank = rank_label if rank_label != "-" else "-"
                item_rank = QTableWidgetItem(display_rank)
                item_rank.setTextAlignment(Qt.AlignCenter)
                item_rank.setFont(QFont("Segoe UI", 9, font_weight))
                item_rank.setForeground(rank_color)
                self.table.setItem(row, 14, item_rank)

                # 15. Probability Percentage Item
                item_prob = QTableWidgetItem(prob_str)
                item_prob.setTextAlignment(Qt.AlignCenter)
                item_prob.setFont(QFont("Segoe UI", 9, font_weight))
                item_prob.setForeground(prob_color)
                self.table.setItem(row, 15, item_prob)

            self.table.setSortingEnabled(True)
            _log.info("Generated sets history successfully loaded with isolated Rounds and Ranks formatting.")
        except Exception as e:
            _log.error(f"Failed to load generated sets history into UI table: {e}")

    def run_bonus_swap_optimizer(self):
        try:
            current_row = self.table.currentRow()
            if current_row < 0:
                if self.table.rowCount() > 0:
                    current_row = 0
                else:
                    QMessageBox.warning(self, "Warning", "No generated sets available to optimize.")
                    return

            nums = []
            bonus_no = 0
            for col_idx in range(5, 11):
                item = self.table.item(current_row, col_idx)
                if item and item.text().isdigit():
                    nums.append(int(item.text()))
            
            bonus_item = self.table.item(current_row, 11)
            if bonus_item and bonus_item.text().isdigit():
                bonus_no = int(bonus_item.text())

            if len(nums) != 6:
                QMessageBox.warning(self, "Warning", "Selected row does not contain a valid 6-number set.")
                return

            if not bonus_no:
                import random
                remaining = [n for n in range(1, 46) if n not in nums]
                bonus_no = random.choice(remaining)

            latest_winning_tuple = (set(), 0)
            try:
                draws = LottoDBHelper.get_generation_history()
            except Exception:
                pass

            result = LottoEvaluator.optimize_bonus_swap(nums, bonus_no, latest_winning_tuple)
            if result.get("status") == "error":
                QMessageBox.warning(self, "Error", result.get("message", "Optimization failed."))
                return

            dialog = BonusSwapDialog(result, self)
            dialog.exec_()

        except Exception as e:
            _log.error(f"Failed to execute Bonus Swap Optimizer: {e}")
            QMessageBox.critical(self, "Error", f"Failed to execute optimizer: {e}")

    def export_to_excel(self, selected_only: bool = False):
        try:
            data_list = []
            row_count = self.table.rowCount()
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(1, self.table.columnCount())]

            for row in range(row_count):
                if selected_only:
                    cell_widget = self.table.cellWidget(row, 0)
                    if cell_widget:
                        chk = cell_widget.findChild(QCheckBox)
                        if not chk or not chk.isChecked():
                            continue
                    else:
                        continue

                row_data = []
                for col in range(1, self.table.columnCount()):
                    item = self.table.item(row, col)
                    cell_text = item.toolTip() if (col == 12 and item and item.toolTip()) else (item.text() if item else "")
                    row_data.append(cell_text)
                data_list.append(row_data)

            if not data_list:
                QMessageBox.warning(self, "Export Warning", "No rows selected or available for export.")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to Excel", "lotto_generated_sets.xlsx", "Excel Files (*.xlsx);;All Files (*)"
            )
            if not file_path:
                return

            if pd is not None:
                df = pd.DataFrame(data_list, columns=headers)
                df.to_excel(file_path, index=False)
            else:
                with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(data_list)

            QMessageBox.information(self, "Success", f"Successfully exported data to:\n{file_path}")
            _log.info(f"Successfully exported generated sets to {file_path}")

        except Exception as e:
            _log.error(f"Failed to export data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")