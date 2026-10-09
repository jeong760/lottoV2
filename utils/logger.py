# -*- coding: utf-8 -*-
# utils/logger.py
import sys
import os
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

def _resolve_project_root(project_root_path=None):
    marker_files = ("pyproject.toml", "requirements.txt", "launcher.py")

    if project_root_path is None:
        start_path = Path(__file__).resolve().parent
    else:
        start_path = Path(project_root_path).resolve()

    candidate = start_path if start_path.is_dir() else start_path.parent
    for check_dir in [candidate, *candidate.parents]:
        if any((check_dir / marker).exists() for marker in marker_files):
            return check_dir

    return Path(__file__).resolve().parent.parent

def setup_logging(project_root_path=None):
    project_root = _resolve_project_root(project_root_path)

    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "lotto_dashboard.log"
    log_file.touch(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 기존 핸들러 중복 방지 및 닫기 처리 (ResourceWarning 해결)
    if root_logger.handlers:
        for handler in list(root_logger.handlers):
            handler.close()
            root_logger.removeHandler(handler)

    file_handler = RotatingFileHandler(
        str(log_file), 
        maxBytes=5 * 1024 * 1024, 
        backupCount=3, 
        encoding="utf-8"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    logging.getLogger("LottoLogger").info(f"Centralized logging initialized. Log path: {log_file}")

setup_logger = setup_logging