# -*- coding: utf-8 -*-
# ui/widgets/generated_sets_widget.py
import sys
import os
import logging
import csv
import json

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
from core.reporting import build_generation_batch_report_text

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


class SessionDetailsDialog(QDialog):
    """Dialog displaying persisted metadata details for a selected generation session."""
    def __init__(self, session_payload: dict, parent=None):
        super().__init__(parent)
        self.session_payload = session_payload if isinstance(session_payload, dict) else {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Generation Session Details")
        self.resize(680, 520)
        self.setStyleSheet("background-color: #f8f9fa;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title_lbl = QLabel("[Session Drill-Down: Metadata & Explainability]")
        title_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_lbl.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title_lbl)

        metadata = self.session_payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        session_id = self.session_payload.get("id", "-")
        timestamp = self.session_payload.get("timestamp", "-")
        algo_title = self.session_payload.get("algorithm_title", metadata.get("algorithm_title", "-"))
        batch_id = self.session_payload.get("generation_batch_id", metadata.get("generation_batch_id", "")) or "-"
        sets_detail = self.session_payload.get("sets_detail", [])
        set_count = len(sets_detail) if isinstance(sets_detail, list) else 0

        leading_algos = metadata.get("leading_algorithms", [])
        leading_text = ", ".join(str(v) for v in leading_algos) if isinstance(leading_algos, list) and leading_algos else "-"
        top_ranked = metadata.get("top_ranked_combinations", [])
        top_ranked_count = len(top_ranked) if isinstance(top_ranked, list) else 0
        score_profile = metadata.get("score_weight_profile", {})

        top_preview = {}
        if isinstance(top_ranked, list) and top_ranked and isinstance(top_ranked[0], dict):
            top_preview = top_ranked[0]

        html = f"""
        <b>Session ID:</b> {session_id}<br>
        <b>Timestamp:</b> {timestamp}<br>
        <b>Algorithm:</b> {algo_title}<br>
        <b>Generation Batch:</b> {batch_id}<br>
        <b>Stored Sets:</b> {set_count}<br>
        <b>Confidence Score:</b> {metadata.get('confidence_score', '-')}<br>
        <b>Total Algorithms Active:</b> {metadata.get('total_algorithms_active', '-')}<br>
        <b>Leading Algorithms:</b> {leading_text}<br>
        <b>Top-Ranked Entries:</b> {top_ranked_count}<br><br>
        <b>Top Ranked Preview (Rank #1 if available)</b><br>
        <pre>{json.dumps(top_preview, ensure_ascii=False, indent=2)}</pre>
        <b>Score Weight Profile</b><br>
        <pre>{json.dumps(score_profile if isinstance(score_profile, dict) else {}, ensure_ascii=False, indent=2)}</pre>
        """

        browser = QTextBrowser()
        browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        browser.setHtml(html)
        layout.addWidget(browser)

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
    DEFAULT_UI_HISTORY_SESSION_LIMIT = 1200

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

        export_ranked_btn = QPushButton("Export Session Top-50")
        export_ranked_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e; color: white; font-weight: bold;
                padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #3d566e; }
        """)
        export_ranked_btn.clicked.connect(self.export_top_ranked_session)

        details_btn = QPushButton("Session Details")
        details_btn.setStyleSheet("""
            QPushButton {
                background-color: #1abc9c; color: white; font-weight: bold;
                padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #16a085; }
        """)
        details_btn.clicked.connect(self.show_session_details)

        filter_batch_btn = QPushButton("Filter Same Batch")
        filter_batch_btn.setStyleSheet("""
            QPushButton {
                background-color: #5d6d7e; color: white; font-weight: bold;
                padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #6c7a89; }
        """)
        filter_batch_btn.clicked.connect(self.filter_rows_by_selected_batch)

        clear_filter_btn = QPushButton("Clear Batch Filter")
        clear_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d; color: white; font-weight: bold;
                padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #95a5a6; }
        """)
        clear_filter_btn.clicked.connect(self.clear_batch_filter)

        export_batch_report_btn = QPushButton("Export Batch Report")
        export_batch_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50; color: white; font-weight: bold;
                padding: 6px 14px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #34495e; }
        """)
        export_batch_report_btn.clicked.connect(self.export_batch_report)

        top_layout.addWidget(refresh_btn)
        top_layout.addWidget(select_all_btn)
        top_layout.addWidget(deselect_all_btn)
        top_layout.addWidget(optimize_btn)
        top_layout.addWidget(export_all_btn)
        top_layout.addWidget(export_selected_btn)
        top_layout.addWidget(export_ranked_btn)
        top_layout.addWidget(details_btn)
        top_layout.addWidget(filter_batch_btn)
        top_layout.addWidget(clear_filter_btn)
        top_layout.addWidget(export_batch_report_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        headers = [
            "Select", "ID", "Date", "Round", "Algorithm", 
            "N1", "N2", "N3", "N4", "N5", "N6", "Bonus", 
            "Rounds", "Matches", "Rank", "Probability", "Batch"
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

            history_records = (
                LottoDBHelper.get_generation_history(max_sessions=self.DEFAULT_UI_HISTORY_SESSION_LIMIT)
                if hasattr(LottoDBHelper, 'get_generation_history')
                else []
            )
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
                session_meta = record.get("session_metadata", {}) if isinstance(record.get("session_metadata"), dict) else {}
                batch_id = str(session_meta.get("generation_batch_id", "") or "")
                batch_short = batch_id[:8] if batch_id else "-"
                
                numbers = record.get("numbers", record.get("set_numbers", record.get("nums", [])))
                if not numbers and isinstance(record, dict):
                    flat_nums = []
                    for i in range(1, 7):
                        value = next(
                            (record[key] for key in (f"n{i}", f"num{i}", f"drwtNo{i}")
                             if record.get(key) is not None),
                            0,
                        )
                        flat_nums.append(value)
                    bonus = next(
                        (record[key] for key in ("bonus", "bnusNo", "n7") if record.get(key) is not None),
                        0,
                    )
                    flat_nums.append(bonus)
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
                item_id.setData(Qt.UserRole, int(record.get("id", 0) or 0))
                item_id.setData(Qt.UserRole + 1, batch_id)
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

                # 16. Batch Column
                item_batch = QTableWidgetItem(batch_short)
                item_batch.setTextAlignment(Qt.AlignCenter)
                item_batch.setForeground(QColor("#34495e") if batch_id else QColor("#95a5a6"))
                item_batch.setToolTip(batch_id if batch_id else "No batch id")
                item_batch.setData(Qt.UserRole, batch_id)
                self.table.setItem(row, 16, item_batch)

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

    def _resolve_target_row(self) -> int:
        current_row = self.table.currentRow()
        if current_row >= 0:
            return int(current_row)

        for row in range(self.table.rowCount()):
            cell_widget = self.table.cellWidget(row, 0)
            if not cell_widget:
                continue
            chk = cell_widget.findChild(QCheckBox)
            if chk and chk.isChecked():
                return int(row)
        return -1

    def _get_row_batch_id(self, row: int) -> str:
        if row < 0:
            return ""
        batch_item = self.table.item(row, 16)
        if batch_item is None:
            return ""
        return str(batch_item.data(Qt.UserRole) or "").strip()

    def clear_batch_filter(self):
        try:
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
        except Exception as e:
            _log.error(f"Failed to clear batch filter: {e}", exc_info=True)

    def filter_rows_by_selected_batch(self):
        try:
            target_row = self._resolve_target_row()
            if target_row < 0:
                QMessageBox.warning(self, "Filter Warning", "Please select a row (or check one) to filter by batch.")
                return

            batch_id = self._get_row_batch_id(target_row)
            if not batch_id:
                QMessageBox.warning(self, "Filter Warning", "Selected row has no generation batch id.")
                return

            visible_count = 0
            for row in range(self.table.rowCount()):
                row_batch = self._get_row_batch_id(row)
                should_show = bool(row_batch and row_batch == batch_id)
                self.table.setRowHidden(row, not should_show)
                if should_show:
                    visible_count += 1

            QMessageBox.information(self, "Batch Filter Applied", f"Showing {visible_count} row(s) for batch:\n{batch_id}")
        except Exception as e:
            _log.error(f"Failed to filter rows by batch: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to filter rows by batch: {e}")

    def show_session_details(self):
        try:
            target_row = self._resolve_target_row()
            if target_row < 0:
                QMessageBox.warning(self, "Session Details", "Please select a row (or check one) first.")
                return

            id_item = self.table.item(target_row, 1)
            session_id = int(id_item.data(Qt.UserRole)) if id_item is not None and id_item.data(Qt.UserRole) else 0
            if session_id <= 0:
                QMessageBox.warning(self, "Session Details", "Invalid session id for selected row.")
                return

            session_payload = (
                LottoDBHelper.get_generation_session_by_id(session_id)
                if hasattr(LottoDBHelper, "get_generation_session_by_id")
                else None
            )
            if not isinstance(session_payload, dict) and hasattr(LottoDBHelper, "get_all_generation_history"):
                all_sessions = LottoDBHelper.get_all_generation_history(
                    max_sessions=self.DEFAULT_UI_HISTORY_SESSION_LIMIT
                )
                session_payload = next((row for row in all_sessions if int(row.get("id", 0) or 0) == session_id), None)
            if not isinstance(session_payload, dict):
                QMessageBox.warning(self, "Session Details", "Could not find selected session payload.")
                return

            dlg = SessionDetailsDialog(session_payload, self)
            dlg.exec_()
        except Exception as e:
            _log.error(f"Failed to show session details: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to show session details: {e}")

    def export_batch_report(self):
        try:
            target_row = self._resolve_target_row()
            if target_row < 0:
                QMessageBox.warning(self, "Export Warning", "Please select a row (or check one) to export batch report.")
                return

            id_item = self.table.item(target_row, 1)
            session_id = int(id_item.data(Qt.UserRole)) if id_item is not None and id_item.data(Qt.UserRole) else 0
            if session_id <= 0:
                QMessageBox.warning(self, "Export Warning", "Invalid session id for selected row.")
                return

            selected_session = (
                LottoDBHelper.get_generation_session_by_id(session_id)
                if hasattr(LottoDBHelper, "get_generation_session_by_id")
                else None
            )
            if not isinstance(selected_session, dict) and hasattr(LottoDBHelper, "get_all_generation_history"):
                all_sessions_fallback = LottoDBHelper.get_all_generation_history(
                    max_sessions=self.DEFAULT_UI_HISTORY_SESSION_LIMIT
                )
                selected_session = next(
                    (row for row in all_sessions_fallback if int(row.get("id", 0) or 0) == session_id),
                    None,
                )
            if not isinstance(selected_session, dict):
                QMessageBox.warning(self, "Export Warning", "Could not find selected session payload.")
                return

            batch_id = self._get_row_batch_id(target_row)
            if not batch_id:
                batch_id = str(
                    selected_session.get("generation_batch_id")
                    or (selected_session.get("metadata", {}) if isinstance(selected_session.get("metadata"), dict) else {}).get("generation_batch_id")
                    or f"session-{session_id}"
                ).strip()

            batch_summaries = LottoDBHelper.get_generation_batch_history() if hasattr(LottoDBHelper, "get_generation_batch_history") else []
            batch_summary = next((row for row in batch_summaries if str(row.get("batch_id", "")) == batch_id), None)
            if not isinstance(batch_summary, dict):
                batch_summary = {
                    "batch_id": batch_id,
                    "is_fallback_batch": str(batch_id).startswith("session-"),
                    "session_count": 1,
                    "set_count": len(selected_session.get("sets_detail", [])) if isinstance(selected_session.get("sets_detail"), list) else 0,
                    "algorithm_titles": [selected_session.get("algorithm_title", "")],
                    "first_timestamp": selected_session.get("timestamp", ""),
                    "latest_timestamp": selected_session.get("timestamp", ""),
                    "has_top_ranked": bool((selected_session.get("metadata", {}) if isinstance(selected_session.get("metadata"), dict) else {}).get("top_ranked_combinations")),
                    "score_weight_profile": (selected_session.get("metadata", {}) if isinstance(selected_session.get("metadata"), dict) else {}).get("score_weight_profile", {}),
                }

            sessions_for_batch = (
                LottoDBHelper.get_generation_sessions_by_batch_id(batch_id)
                if hasattr(LottoDBHelper, "get_generation_sessions_by_batch_id")
                else []
            )
            if (not sessions_for_batch) and hasattr(LottoDBHelper, "get_all_generation_history"):
                all_sessions_fallback = LottoDBHelper.get_all_generation_history(
                    max_sessions=self.DEFAULT_UI_HISTORY_SESSION_LIMIT
                )
                for session in all_sessions_fallback:
                    if not isinstance(session, dict):
                        continue
                    candidate_batch = str(
                        session.get("generation_batch_id")
                        or (session.get("metadata", {}) if isinstance(session.get("metadata"), dict) else {}).get("generation_batch_id")
                        or ""
                    ).strip()
                    if candidate_batch and candidate_batch == batch_id:
                        sessions_for_batch.append(session)
                if not sessions_for_batch and str(batch_id).startswith("session-"):
                    try:
                        fallback_id = int(str(batch_id).replace("session-", ""))
                    except Exception:
                        fallback_id = session_id
                    sessions_for_batch = [s for s in all_sessions_fallback if int(s.get("id", 0) or 0) == fallback_id]

            if not sessions_for_batch:
                sessions_for_batch = [selected_session]

            report_text = build_generation_batch_report_text(batch_summary, sessions_for_batch)
            default_name = f"lotto_generation_batch_report_{batch_id[:12] if batch_id else session_id}.txt"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Generation Batch Report",
                default_name,
                "Text Files (*.txt);;All Files (*)",
            )
            if not file_path:
                return

            with open(file_path, mode="w", encoding="utf-8") as f:
                f.write(report_text)

            QMessageBox.information(self, "Success", f"Successfully exported batch report to:\n{file_path}")
            _log.info("Exported generation batch report: batch_id=%s path=%s", batch_id, file_path)
        except Exception as e:
            _log.error(f"Failed to export batch report: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to export batch report: {e}")

    def export_top_ranked_session(self):
        try:
            target_row = self._resolve_target_row()
            if target_row < 0:
                QMessageBox.warning(self, "Export Warning", "Please select a row (or check one) to export session rankings.")
                return

            id_item = self.table.item(target_row, 1)
            session_id = int(id_item.data(Qt.UserRole)) if id_item is not None and id_item.data(Qt.UserRole) else 0
            if session_id <= 0:
                QMessageBox.warning(self, "Export Warning", "Invalid session id for selected row.")
                return

            session_payload = (
                LottoDBHelper.get_generation_session_by_id(session_id)
                if hasattr(LottoDBHelper, "get_generation_session_by_id")
                else None
            )
            if not isinstance(session_payload, dict) and hasattr(LottoDBHelper, "get_all_generation_history"):
                all_sessions = LottoDBHelper.get_all_generation_history(
                    max_sessions=self.DEFAULT_UI_HISTORY_SESSION_LIMIT
                )
                session_payload = next((row for row in all_sessions if int(row.get("id", 0) or 0) == session_id), None)
            if not isinstance(session_payload, dict):
                QMessageBox.warning(self, "Export Warning", "Could not find selected session payload.")
                return

            session_meta = session_payload.get("metadata", {}) if isinstance(session_payload.get("metadata"), dict) else {}
            top_ranked = session_meta.get("top_ranked_combinations", [])
            if not isinstance(top_ranked, list) or not top_ranked:
                QMessageBox.warning(self, "Export Warning", "No Top-50 ranking data stored for this session.")
                return

            default_name = f"lotto_top_ranked_session_{session_id}.json"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Session Top-50 Rankings",
                default_name,
                "JSON Files (*.json);;CSV Files (*.csv);;All Files (*)",
            )
            if not file_path:
                return

            if file_path.lower().endswith(".csv"):
                headers = [
                    "rank", "n1", "n2", "n3", "n4", "n5", "n6",
                    "confidence_score", "probability_score", "pattern_score",
                    "ai_score", "genetic_score", "ensemble_score",
                ]
                with open(file_path, mode="w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for row in top_ranked:
                        nums = row.get("numbers", []) if isinstance(row, dict) else []
                        nums = list(nums[:6]) if isinstance(nums, list) else []
                        while len(nums) < 6:
                            nums.append("")
                        writer.writerow([
                            row.get("rank", ""),
                            nums[0], nums[1], nums[2], nums[3], nums[4], nums[5],
                            row.get("confidence_score", ""),
                            row.get("probability_score", ""),
                            row.get("pattern_score", ""),
                            row.get("ai_score", ""),
                            row.get("genetic_score", ""),
                            row.get("ensemble_score", ""),
                        ])
            else:
                export_payload = {
                    "session_id": session_id,
                    "algorithm_title": session_payload.get("algorithm_title", ""),
                    "generation_batch_id": session_payload.get("generation_batch_id", session_meta.get("generation_batch_id", "")),
                    "score_weight_profile": session_meta.get("score_weight_profile", {}),
                    "top_ranked_combinations": top_ranked,
                }
                with open(file_path, mode="w", encoding="utf-8") as f:
                    json.dump(export_payload, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "Success", f"Successfully exported Top-50 rankings to:\n{file_path}")
            _log.info("Exported session Top-50 rankings: session_id=%s path=%s", session_id, file_path)
        except Exception as e:
            _log.error(f"Failed to export session Top-50 rankings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to export session Top-50 rankings: {e}")
