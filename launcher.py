# launcher.py
import sys
import os
import subprocess
import logging
import platform
import shutil
import atexit
import importlib.util
import warnings
import traceback

# [Debug] Enable all warnings so they are fully visible for debugging purposes
warnings.simplefilter('default')

project_root = os.path.dirname(os.path.abspath(__file__))

# Force the working directory to be the exact directory where launcher.py resides (Project Root)
os.chdir(project_root)

# Import and initialize logging via utils/logger.py (Centralized Logging Architecture)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("LottoLauncher")


def register_cleanup_handlers():
    @atexit.register
    def on_exit():
        try:
            _log.info("[LottoLauncher] Initiating safety shutdown sequence...")
            _log.info("[LottoLauncher] Dashboard session and virtual environment resources closed safely.")
        except Exception as e:
            _log.error(f"[LottoLauncher] Error during safety cleanup: {e}\n{traceback.format_exc()}")


def clean_bytecode_cache():
    try:
        for dirpath, dirnames, filenames in os.walk(project_root):
            if "__pycache__" in dirnames:
                cache_path = os.path.join(dirpath, "__pycache__")
                shutil.rmtree(cache_path, ignore_errors=True)
        _log.info("[LottoLauncher] Cleaned up bytecode cache (__pycache__).")
    except Exception as e:
        _log.warning(f"[LottoLauncher] Warning during cache cleanup: {e}\n{traceback.format_exc()}")


def check_and_install_required_packages(python_executable):
    req_path = os.path.join(project_root, "requirements.txt")
    
    missing_core = False
    for mod_name in ["PyQt5", "pandas", "requests", "sklearn", "statsmodels", "openpyxl", "scipy"]:
        if importlib.util.find_spec(mod_name) is None:
            missing_core = True
            break

    if missing_core or os.path.exists(req_path):
        _log.info("[LottoLauncher] Verifying/Installing dependencies from requirements.txt (quiet mode)...")
        try:
            subprocess.run(
                [python_executable, "-m", "pip", "install", "numpy<2"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )

            if os.path.exists(req_path):
                subprocess.run(
                    [python_executable, "-m", "pip", "install", "-r", req_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                _log.info("[LottoLauncher] All dependencies installed and verified successfully.")
        except Exception as e:
            _log.error(f"[LottoLauncher] Error during dependency installation: {e}\n{traceback.format_exc()}")


def ensure_virtual_environment():
    if platform.system() == "Windows":
        venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
        venv_dir = os.path.join(project_root, ".venv")
    else:
        venv_python = os.path.join(project_root, ".venv", "bin", "python")
        venv_dir = os.path.join(project_root, ".venv")

    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

    if not os.path.exists(venv_python):
        _log.warning("[LottoLauncher] Virtual environment (.venv) not detected. Creating virtual environment automatically...")
        try:
            import venv
            venv.create(venv_dir, with_pip=True)
            _log.info("[LottoLauncher] Virtual environment (.venv) created successfully.")
        except Exception as e:
            _log.error(f"[LottoLauncher] Failed to automatically create virtual environment: {e}\n{traceback.format_exc()}")
            check_and_install_required_packages(sys.executable)
            return

    if os.path.exists(venv_python):
        check_and_install_required_packages(venv_python)

    if not in_venv and os.path.exists(venv_python):
        _log.info("[LottoLauncher] Switching session to virtual environment Python and relaunching dashboard...")
        try:
            cmd = [venv_python] + sys.argv
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        except Exception as e:
            _log.error(f"[LottoLauncher] Exception occurred while relaunching in virtual environment: {e}\n{traceback.format_exc()}")


def initialize_databases_and_data():
    """Validates DB integrity (Main DB & AI DB) and updates latest draw records prior to UI startup with debug logs."""
    _log.info("[LottoLauncher] [DEBUG] Performing pre-launch database integrity check and synchronization...")
    
    try:
        from data.db_guardian import DBGuardian
        
        db_paths = [
            os.path.join(project_root, "db", "lottomater.db"),
            os.path.join(project_root, "db", "mllearn.db")
        ]
        
        for db_path in db_paths:
            _log.info(f"[LottoLauncher] [DEBUG] Checking integrity for: {db_path}")
            DBGuardian.verify_and_heal_database(db_path)
            
    except Exception as db_ex:
        _log.critical(f"[LottoLauncher] [CRITICAL DEBUG] Database guardian exception: {db_ex}\n{traceback.format_exc()}")

    try:
        from data.updater import update_lotto_data
        _log.info("[LottoLauncher] [DEBUG] Synchronizing latest official lotto draw data...")
        update_lotto_data()
        _log.info("[LottoLauncher] [DEBUG] Data synchronization completed successfully.")
    except Exception as update_ex:
        _log.warning(f"[LottoLauncher] [DEBUG] Online data sync skipped (operating on offline cache): {update_ex}\n{traceback.format_exc()}")


def main():
    register_cleanup_handlers()
    clean_bytecode_cache()
    ensure_virtual_environment()

    # Execute mandatory DB verification, self-healing, and data update BEFORE launching UI
    initialize_databases_and_data()

    _log.info("[LottoLauncher] [DEBUG] Booting Lotto V2 Simulation Dashboard...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        _log.info("[LottoLauncher] [DEBUG] Instantiating MainWindow...")
        main_window = MainWindow()
        main_window.show()

        _log.info("[LottoLauncher] [DEBUG] Dashboard main window rendered successfully.")
        sys.exit(app.exec_())

    except Exception as e:
        _log.critical(f"[LottoLauncher] [CRITICAL DEBUG] Critical exception occurred while booting dashboard: {e}\n{traceback.format_exc()}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()