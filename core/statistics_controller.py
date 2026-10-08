# -*- coding: utf-8 -*-
# core/statistics_controller.py
import sys
import os
import logging
from collections import Counter, defaultdict
import numpy as np
import scipy.stats as stats

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "core" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Note: Logging setup is centralized in launcher.py to prevent redundant or misplaced log directory creation.
_log = logging.getLogger("StatisticsController")

class AdvancedLottoStatisticsEngine:
    """
    Expert-level lotto statistics and probability analysis engine.
    Calculates advanced metrics such as periodicity, co-occurrence matrix,
    sector distribution, Chi-Square goodness of fit, and ML weight propagation arrays.
    """
    def __init__(self, history_data):
        """
        Initialize the engine with historical draw data.
        :param history_data: List of dicts, e.g., [{'draw': int, 'numbers': [int, ...]}, ...]
        """
        parsed_history = []
        if history_data:
            for entry in history_data:
                if not isinstance(entry, dict):
                    continue
                d_no = entry.get('draw') or entry.get('drwNo') or 0
                nums = entry.get('numbers')
                if not nums:
                    nums = []
                    for i in range(1, 7):
                        val = entry.get(f"num{i}") or entry.get(f"drwtNo{i}")
                        if val is not None:
                            try:
                                nums.append(int(val))
                            except (ValueError, TypeError):
                                pass
                try:
                    valid_nums = sorted([int(n) for n in nums if n is not None and 1 <= int(n) <= 45])
                except (ValueError, TypeError):
                    valid_nums = []

                if len(valid_nums) >= 6:
                    try:
                        parsed_history.append({'draw': int(d_no), 'numbers': valid_nums[:6]})
                    except (ValueError, TypeError):
                        pass

        self.history = sorted(parsed_history, key=lambda x: x['draw'])
        self.total_draws = len(self.history)
        self.all_numbers_flat = [num for draw in self.history for num in draw.get('numbers', [])]
        self.number_counts = Counter(self.all_numbers_flat)

    # =========================================================================
    # 1. Frequency & Periodicity Analysis
    # =========================================================================
    def analyze_periodicity_and_gaps(self):
        """
        Analyzes the overdue period (Lotto Gap) and appearance interval standard deviation
        for each number (1-45).
        """
        latest_draw = int(self.history[-1]['draw']) if self.history else 0
        intervals = defaultdict(list)
        last_seen = {i: -1 for i in range(1, 46)}
        
        for entry in self.history:
            draw_num = int(entry.get('draw', 0))
            for num in entry.get('numbers', []):
                try:
                    num_val = int(num)
                    if 1 <= num_val <= 45:
                        if last_seen[num_val] != -1:
                            intervals[num_val].append(draw_num - last_seen[num_val])
                        last_seen[num_val] = draw_num
                except (ValueError, TypeError):
                    pass

        periodicity_results = {}
        for num in range(1, 46):
            current_gap = latest_draw - last_seen[num] if last_seen[num] != -1 else latest_draw
            num_intervals = intervals[num]
            
            std_dev = float(np.std(num_intervals)) if len(num_intervals) > 1 else 0.0
            mean_interval = float(np.mean(num_intervals)) if len(num_intervals) > 0 else 0.0

            periodicity_results[num] = {
                "current_gap": int(current_gap),
                "mean_interval": round(mean_interval, 2),
                "interval_std_dev": round(std_dev, 2),
                "is_hot": bool(current_gap <= mean_interval * 0.5) if mean_interval > 0 else False,
                "is_cold": bool(current_gap >= mean_interval * 1.5) if mean_interval > 0 else True
            }
        return periodicity_results

    # =========================================================================
    # 2. Pair & Matrix Analysis (Co-occurrence)
    # =========================================================================
    def analyze_cooccurrence_matrix(self):
        """
        Computes the co-occurrence frequency matrix for number pairs
        and extracts top partner numbers for each digit.
        """
        pair_counts = defaultdict(int)
        for entry in self.history:
            try:
                nums = sorted([int(n) for n in entry.get('numbers', []) if 1 <= int(n) <= 45])
                for i in range(len(nums)):
                    for j in range(i + 1, len(nums)):
                        pair_counts[(nums[i], nums[j])] += 1
            except (ValueError, TypeError):
                pass

        matrix = {i: defaultdict(int) for i in range(1, 46)}
        for (n1, n2), count in pair_counts.items():
            matrix[n1][n2] = count
            matrix[n2][n1] = count

        top_partners = {}
        for num in range(1, 46):
            sorted_partners = sorted(matrix[num].items(), key=lambda x: x[1], reverse=True)
            top_partners[num] = [(int(p), int(c)) for p, c in sorted_partners[:5]]

        return top_partners

    # =========================================================================
    # 3. Decade & Digit Distribution Analysis
    # =========================================================================
    def analyze_decade_and_digit_distribution(self):
        """
        Analyzes distribution across decade sectors (1-10, 11-20, etc.)
        and trailing digit sums (0-9).
        """
        decade_stats = defaultdict(int)
        digit_sums = defaultdict(int)

        for entry in self.history:
            for num in entry.get('numbers', []):
                try:
                    val = int(num)
                    if 1 <= val <= 45:
                        decade = (val - 1) // 10
                        decade_stats[decade] += 1
                        
                        digit = val % 10
                        digit_sums[digit] += 1
                except (ValueError, TypeError):
                    pass

        return {
            "decade_distribution": {str(k): int(v) for k, v in decade_stats.items()},
            "digit_distribution": {str(k): int(v) for k, v in digit_sums.items()}
        }

    # =========================================================================
    # 4. Chi-Square Goodness of Fit Test
    # =========================================================================
    def chi_square_goodness_of_fit(self):
        """
        Performs a Chi-Square goodness of fit test to evaluate whether 
        the historical number distribution deviates significantly from uniform randomness.
        """
        observed = [int(self.number_counts.get(i, 0)) for i in range(1, 46)]
        total_selections = sum(observed)
        
        expected_prob = 6.0 / 45.0
        expected = [float(total_selections * expected_prob)] * 45

        chi2_stat, p_value = 0.0, 1.0
        try:
            if total_selections > 0:
                chi2_stat, p_value = stats.chisquare(f_obs=np.array(observed, dtype=np.float64), f_exp=np.array(expected, dtype=np.float64))
        except Exception:
            chi2_stat, p_value = 0.0, 1.0
        
        bias_analysis = {}
        for i in range(1, 46):
            obs = observed[i-1]
            exp = expected[i-1]
            if exp > 0:
                if obs < exp * 0.9:
                    bias_analysis[i] = "Undersampled"
                elif obs > exp * 1.1:
                    bias_analysis[i] = "Oversampled"
                else:
                    bias_analysis[i] = "Balanced"
            else:
                bias_analysis[i] = "Balanced"

        return {
            "chi2_statistic": float(chi2_stat),
            "p_value": float(p_value),
            "is_uniformly_distributed": bool(p_value > 0.05),
            "bias_status": bias_analysis
        }

    # =========================================================================
    # 5. ML Weight Propagation Array Generator (Integration Feature)
    # =========================================================================
    def get_ml_frequency_weights(self) -> np.ndarray:
        """
        [Integration Addition] Computes a normalized 45-element NumPy probability array 
        combining historical frequencies and gap pressures for algorithm group injection.
        """
        weights = np.zeros(45, dtype=np.float64)
        gaps = self.analyze_periodicity_and_gaps()
        
        for i in range(1, 46):
            freq_val = int(self.number_counts.get(i, 1))
            gap_val = int(gaps.get(i, {}).get("current_gap", 1))
            # Blend frequency and gap pressure securely
            weights[i - 1] = float(freq_val) * (1.0 + min(2.0, float(gap_val) / 15.0))
            
        total = np.sum(weights)
        if total > 0:
            return weights / total
        return np.full(45, 1.0 / 45.0, dtype=np.float64)


class StatisticsWidgetConnector:
    """
    Bridge controller that dispatches analytics results from the statistical engine
    to the respective UI widgets in the main application window.
    """
    def __init__(self, main_window):
        self.main_window = main_window

    def update_all_widgets(self, history_data):
        """
        Executes advanced analysis and updates connected UI widgets securely.
        """
        if not history_data:
            return

        try:
            engine = AdvancedLottoStatisticsEngine(history_data)
            
            # 1. Compute advanced metrics
            gaps_data = engine.analyze_periodicity_and_gaps()
            decade_data = engine.analyze_decade_and_digit_distribution()
            chi2_data = engine.chi_square_goodness_of_fit()

            # 2. Sync with DecadeDistWidget
            if hasattr(self.main_window, 'decade_dist_widget') and self.main_window.decade_dist_widget:
                if hasattr(self.main_window.decade_dist_widget, 'update_distribution_data'):
                    self.main_window.decade_dist_widget.update_distribution_data(decade_data["decade_distribution"])

            # 3. Sync with LottoHeatmapWidget (Inject gap weights & cold/hot states)
            if hasattr(self.main_window, 'heatmap_widget') and self.main_window.heatmap_widget:
                if hasattr(self.main_window.heatmap_widget, 'update_heat_with_gaps'):
                    self.main_window.heatmap_widget.update_heat_with_gaps(gaps_data)

            # 4. Sync with StatisticalMetricsWidget (Inject Chi-Square test metrics)
            if hasattr(self.main_window, 'statistical_metrics_widget') and self.main_window.statistical_metrics_widget:
                if hasattr(self.main_window.statistical_metrics_widget, 'update_chi_square_metrics'):
                    self.main_window.statistical_metrics_widget.update_chi_square_metrics(chi2_data)

            # 5. Output telemetry status to Live Console Widget
            if hasattr(self.main_window, 'live_console_widget') and self.main_window.live_console_widget:
                p_val_str = f"{chi2_data['p_value']:.4f}"
                uniform_status = "Normal (Uniform)" if chi2_data['is_uniformly_distributed'] else "Biased (Skewed)"
                if hasattr(self.main_window.live_console_widget, 'log_message'):
                    self.main_window.live_console_widget.log_message(f"Advanced Stats: Chi2 p-value={p_val_str} [{uniform_status}]")

            _log.info("All analytical statistics successfully pushed to connected UI widgets.")
        except Exception as e:
            _log.error(f"Error in StatisticsWidgetConnector.update_all_widgets: {e}", exc_info=True)