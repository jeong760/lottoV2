# -*- coding: utf-8 -*-
# data/db_guardian.py
import os
import shutil
import sqlite3
import logging
from datetime import datetime
from typing import List

_log = logging.getLogger("DBGuardian")


class DBGuardian:
    """
    Checks SQLite database integrity for multiple targets (Main lottomater.db, AI Learning DB, etc.),
    detects tampering or corruption, and executes automatic backup and recovery.
    """

    @staticmethod
    def verify_and_heal_databases(db_paths: List[str]) -> bool:
        """
        Inspects a list of SQLite database paths. 
        Returns True if all databases are healthy or successfully healed.
        """
        all_healthy = True
        for db_path in db_paths:
            if not DBGuardian.verify_and_heal_database(db_path):
                all_healthy = False
        return all_healthy

    @staticmethod
    def verify_and_heal_database(db_path: str) -> bool:
        """
        Inspects a single SQLite database integrity. If corrupted or tampered,
        moves the damaged file to a backup and prepares a clean state.
        """
        if not os.path.exists(db_path):
            _log.info(f"Database file not found at {db_path}. A new one will be initialized.")
            return True

        _log.info(f"Running pre-launch integrity check on database: {db_path}")
        
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()

            if row and row[0] == "ok":
                _log.info(f"Database integrity check passed for {db_path}. [OK]")
                return True
            else:
                _log.error(f"Database integrity violation detected in {db_path}: {row}")
                DBGuardian._execute_recovery(db_path, reason="integrity_failed")
                return False

        except sqlite3.DatabaseError as db_err:
            _log.critical(f"Database corruption or tampering detected in {db_path}: {db_err}")
            DBGuardian._execute_recovery(db_path, reason="tampered_or_corrupt")
            return False
        except Exception as ex:
            _log.error(f"Unexpected error during database verification for {db_path}: {ex}", exc_info=True)
            return False
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    @staticmethod
    def _execute_recovery(db_path: str, reason: str):
        """Backs up the corrupted or tampered database with a unique timestamp and resets."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{db_path}.{reason}.{timestamp}.bak"
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                _log.warning(f"Damaged database backed up to: {backup_path}")
                
                os.remove(db_path)
                _log.info(f"Damaged database file {db_path} removed. Clean initialization ready.")
        except Exception as e:
            _log.critical(f"Failed to execute database recovery for {db_path}: {e}", exc_info=True)