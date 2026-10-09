# config.py
import sys
import os
import logging

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is delegated to launcher.py or main entry points to prevent premature folder creation outside root.
_log = logging.getLogger("ConfigModule")

"""
Centralized configuration management for Lotto 6/45 Prediction Engine.
Contains database paths, data sources, quality gate constants, and ML/algorithm hyperparameters.
"""

# ==========================================
# 1. Database & Data Source Settings (Absolute Path Fix)
# ==========================================
DB_DIR = os.path.join(project_root, "db")
DB_PATH = os.path.join(DB_DIR, "lottomater.db")

# Ensure db directory exists unconditionally to prevent runtime path errors
os.makedirs(DB_DIR, exist_ok=True)

# Official GitHub source URL for lotto history data sync
GITHUB_DATA_URL = "https://raw.githubusercontent.com/jeong760/lotto-data/main/data/lotto-history.json"


# ==========================================
# 2. Quality Gate & Constraint Constants
# ==========================================
SUM_MIN = 100
SUM_MAX = 170
AC_MIN_THRESHOLD = 7


# ==========================================
# 3. Machine Learning & Training Pipeline Settings
# ==========================================
ML_MAX_ITERATIONS = 500000
ML_TARGET_ACCURACY = 99.0
ML_RECENT_DRAWS_LIMIT = 10000
ML_CLUSTER_COUNT = 5


# ==========================================
# 4. Time Series & Statistical Window Settings
# ==========================================
TS_ROLLING_WINDOW = 10
TS_MIN_RECORDS_ARIMA = 30
AI_SEQUENCE_WINDOW = 5


# ==========================================
# 5. Security & Audit Settings
# ==========================================
AUDIT_HASH_ALGORITHM = "sha256"
DEFAULT_CONFIDENCE_SCORE = 85.0

_log.info("Configuration module loaded successfully with centralized logging setup and absolute paths.")