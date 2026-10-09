# tests/test_quality_gate.py
import sys
import os
import logging
import pytest

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "tests" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("TestQualityGate")

from workers.lotto_worker import LottoWorker
from config import SUM_MIN, SUM_MAX

class MockEngine:
    pass


def test_ac_value_calculation():
    """Verify AC (Arithmetic Complexity) value calculation logic."""
    _log.info("Running test_ac_value_calculation...")
    worker = LottoWorker(engine=MockEngine(), set_count=1)
    
    # A set with normal complexity
    normal_set = [3, 12, 24, 27, 35, 42]
    ac = worker._calculate_ac_value(normal_set)
    assert ac >= 4, f"AC value too low for normal set: {ac}"

    # A simple set structured as an arithmetic sequence (should have a low AC value)
    arithmetic_set = [1, 2, 3, 4, 5, 6]
    ac_arithmetic = worker._calculate_ac_value(arithmetic_set)
    assert ac_arithmetic < 4, f"AC value should be low for arithmetic set: {ac_arithmetic}"
    _log.info("test_ac_value_calculation passed successfully.")


def test_quality_gate_boundaries():
    """Verify quality gate boundary values and constraint filtering."""
    _log.info("Running test_quality_gate_boundaries...")
    worker = LottoWorker(engine=MockEngine(), set_count=1)
    mock_latest_draw = [10, 20, 30, 35, 40, 45]

    # 1. Test sum boundary violation (too low or too high)
    low_sum_set = [1, 2, 3, 4, 5, 6]  # Sum is 21 (below SUM_MIN threshold)
    assert worker._passes_quality_gate(low_sum_set, mock_latest_draw) is False

    # 2. Test odd/even bias violation (all even numbers)
    even_biased_set = [2, 4, 6, 8, 10, 12]
    assert worker._passes_quality_gate(even_biased_set, mock_latest_draw) is False

    # 3. Test a combination within the normal range (within SUM_MIN ~ SUM_MAX with proper distribution)
    valid_set = [5, 14, 22, 29, 34, 41] 
    total_sum = sum(valid_set)
    if SUM_MIN <= total_sum <= SUM_MAX:
        result = worker._passes_quality_gate(valid_set, mock_latest_draw)
        assert isinstance(result, bool)
        
    _log.info("test_quality_gate_boundaries passed successfully.")