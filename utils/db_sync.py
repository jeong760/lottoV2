# -*- coding: utf-8 -*-
# utils/db_sync.py
import os
import shutil
import logging

_log = logging.getLogger("DBSyncManager")

class DBSyncManager:
    """Manager responsible for backing up and restoring database files (lottomater.db, mllearn.db, etc.) between work and home PCs."""

    @staticmethod
    def backup_database(source_path: str, dest_path: str) -> bool:
        """Safely copy the current database file to a specified backup destination."""
        try:
            if not os.path.exists(source_path):
                _log.error(f"Source database not found: {source_path}")
                return False
            
            dest_dir = os.path.dirname(dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
                
            shutil.copy2(source_path, dest_path)
            _log.info(f"Database successfully backed up from {source_path} to {dest_path}")
            return True
        except PermissionError as pe:
            _log.error(f"Permission denied while backing up database (file may be in use): {pe}", exc_info=True)
            return False
        except Exception as e:
            _log.error(f"Failed to backup database: {e}", exc_info=True)
            return False

    @staticmethod
    def restore_database(source_backup_path: str, target_path: str) -> bool:
        """Restore the database by overwriting the current project DB with a backup file from another PC."""
        try:
            if not os.path.exists(source_backup_path):
                _log.error(f"Backup source file not found: {source_backup_path}")
                return False
            
            target_dir = os.path.dirname(target_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                
            shutil.copy2(source_backup_path, target_path)
            _log.info(f"Database successfully restored from {source_backup_path} to {target_path}")
            return True
        except PermissionError as pe:
            _log.error(f"Permission denied while restoring database (file may be in use): {pe}", exc_info=True)
            return False
        except Exception as e:
            _log.error(f"Failed to restore database: {e}", exc_info=True)
            return False