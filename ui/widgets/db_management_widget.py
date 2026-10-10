# ui/widgets/db_management_widget.py
import os
import sys
import logging
import datetime

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "widgets" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QFileDialog, QMessageBox, QSizePolicy
from PyQt5.QtCore import Qt
from utils.db_sync import DBSyncManager
from data.lotto_db_helper import LottoDBHelper

_log = logging.getLogger("DBManagementWidget")

class DBManagementWidget(QWidget):
    """Widget dedicated to database backup, restoration, and sync management between home and work PCs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.refresh_db_status()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # Group Box for DB Info & Status
        info_group = QGroupBox("Database Status & Information")
        info_layout = QVBoxLayout(info_group)
        
        self.lbl_db_path = QLabel("DB Path: Loading...")
        self.lbl_db_size = QLabel("File Size: Loading...")
        self.lbl_last_modified = QLabel("Last Modified: Loading...")
        
        info_layout.addWidget(self.lbl_db_path)
        info_layout.addWidget(self.lbl_db_size)
        info_layout.addWidget(self.lbl_last_modified)
        main_layout.addWidget(info_group)

        # Group Box for Sync Actions (Backup / Restore)
        action_group = QGroupBox("Cross-PC Synchronization & Backup")
        action_layout = QHBoxLayout(action_group)
        action_layout.setSpacing(10)

        self.btn_backup = QPushButton("Backup Database (Export)")
        self.btn_backup.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.btn_backup.clicked.connect(self.on_click_db_backup)

        self.btn_restore = QPushButton("Restore Database (Import)")
        self.btn_restore.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        self.btn_restore.clicked.connect(self.on_click_db_restore)

        action_layout.addWidget(self.btn_backup)
        action_layout.addWidget(self.btn_restore)
        main_layout.addWidget(action_group)

        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def get_db_path(self) -> str:
        """Retrieve the absolute path of the current active database."""
        try:
            if hasattr(LottoDBHelper, 'get_db_path'):
                path = LottoDBHelper.get_db_path()
                if path:
                    return path
            if hasattr(LottoDBHelper, '_get_db_path'):
                path = LottoDBHelper._get_db_path()
                if path:
                    return path
        except Exception:
            pass
        return os.path.abspath(os.path.join(project_root, "db", "lottomater.db"))

    def refresh_db_status(self):
        """Update database file metrics and path info labels."""
        try:
            db_path = self.get_db_path()
            if os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                size_kb = size_bytes / 1024.0
                mod_time = os.path.getmtime(db_path)
                mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')

                self.lbl_db_path.setText(f"<b>DB Path:</b> {db_path}")
                self.lbl_db_size.setText(f"<b>File Size:</b> {size_kb:.2f} KB")
                self.lbl_last_modified.setText(f"<b>Last Modified:</b> {mod_time_str}")
            else:
                self.lbl_db_path.setText(f"<b>DB Path:</b> {db_path} (Not Found)")
                self.lbl_db_size.setText("<b>File Size:</b> 0 KB")
                self.lbl_last_modified.setText("<b>Last Modified:</b> N/A")
        except Exception as e:
            _log.warning(f"Failed to refresh DB status: {e}", exc_info=True)

    def on_click_db_backup(self):
        """Export the current local database to a user-selected backup destination."""
        try:
            db_path = self.get_db_path()
            dest_path, _ = QFileDialog.getSaveFileName(
                self, "Save Database Backup", "lotto_sync_backup.db", "SQLite DB Files (*.db);;All Files (*)"
            )
            if dest_path:
                success = DBSyncManager.backup_database(db_path, dest_path)
                if success:
                    QMessageBox.information(self, "Backup Complete", f"Database successfully backed up to:\n{dest_path}")
                else:
                    QMessageBox.warning(self, "Backup Failed", "An error occurred during database backup. Check logs for details.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Exception occurred during backup: {str(e)}")

    def on_click_db_restore(self):
        """Import a backup database file from another PC and apply it to the current environment."""
        try:
            db_path = self.get_db_path()
            source_path, _ = QFileDialog.getOpenFileName(
                self, "Select Backup Database", "", "SQLite DB Files (*.db);;All Files (*)"
            )
            if source_path:
                reply = QMessageBox.question(
                    self, "Confirm Database Restoration", 
                    "Existing local data will be overwritten by the selected backup file.\nDo you want to proceed?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    success = DBSyncManager.restore_database(source_path, db_path)
                    if success:
                        QMessageBox.information(self, "Restoration Complete", "Database successfully restored.\nPlease restart the application.")
                        self.refresh_db_status()
                    else:
                        QMessageBox.warning(self, "Restoration Failed", "An error occurred during database restoration. Check logs for details.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Exception occurred during restoration: {str(e)}")