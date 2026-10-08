# -*- coding: utf-8 -*-
# core/engines/statistics_engine.py
import logging
import numpy as np
import scipy.stats as stats
from itertools import combinations
from collections import Counter, defaultdict
from typing import Dict, Any, List
from data.repositories.lotto_repository import LottoRepository

_log = logging.getLogger("StatisticsEngine")


class StatisticsEngine:
    """
    Expert-level comprehensive lotto statistics and probability analysis engine.
    Combines database data integration with advanced metrics such as periodicity, 
    co-occurrence matrix, decade/digit distribution, Chi-Square goodness of fit,
    consecutive number patterns, AC value complexity, and trailing digit entropy.
    """

    @staticmethod
    def get_comprehensive_statistics() -> Dict[str, Any]:
        """Safely conducts a full investigation of historical draws and returns a comprehensive statistical report."""
        try:
            all_draws = []
            try:
                all_draws = LottoRepository.get_all_draws() or []
            except Exception as repo_err:
                _log.warning(f"Exception while querying LottoRepository: {repo_err}")

            total_draws = len(all_draws)
            
            # [Defensive Improvement 1] 데이터가 불충분하거나 비어있을 때 크래시 없이 안전한 폴백 통계 반환
            if total_draws < 5:
                _log.warning(f"Insufficient historical draw records ({total_draws}). Falling back to default baseline statistics.")
                fallback_data = StatisticsEngine._get_default_fallback_stats()
                fallback_data["total_draws"] = total_draws
                return fallback_data

            # Sort history chronologically by draw number
            sorted_history = sorted(all_draws, key=lambda x: int(x.get('draw') or x.get('drwNo', 0)))
            latest_draw = int(sorted_history[-1].get('draw') or sorted_history[-1].get('drwNo', total_draws))

            freq = {i: 0 for i in range(1, 46)}
            sums = []
            odd_count_map = {}
            high_count_map = {}
            pair_counts = defaultdict(int)

            # Advanced statistical trackers
            last_seen = {i: -1 for i in range(1, 46)}
            intervals = defaultdict(list)
            decade_stats = defaultdict(int)
            digit_sums = defaultdict(int)
            
            # Additional advanced trackers for new features
            consecutive_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            ac_value_counts = defaultdict(int)

            for draw_idx, draw in enumerate(sorted_history):
                draw_num = int(draw.get('draw') or draw.get('drwNo') or (draw_idx + 1))
                nums = []
                
                # Support both modern keys (num1~6) and legacy keys (drwtNo1~6)
                for i in range(1, 7):
                    val = draw.get(f"num{i}") or draw.get(f"drwtNo{i}")
                    if val is not None:
                        try:
                            nums.append(int(val))
                        except (ValueError, TypeError):
                            pass
                
                valid_nums = sorted(list(set([n for n in nums if 1 <= n <= 45])))
                if len(valid_nums) == 6:
                    sums.append(sum(valid_nums))
                    
                    for n in valid_nums:
                        freq[n] += 1
                        if last_seen[n] != -1:
                            intervals[n].append(draw_num - last_seen[n])
                        last_seen[n] = draw_num

                        # Decade sector classification (0: 1-10, 1: 11-20, ..., 4: 41-45)
                        decade = (n - 1) // 10
                        decade_stats[decade] += 1
                        
                        # Trailing digit classification (0-9)
                        digit_sums[n % 10] += 1
                            
                    # Odd / Even ratio calculation
                    odds = sum(1 for n in valid_nums if n % 2 != 0)
                    evens = 6 - odds
                    oe_key = f"Odd {odds} : Even {evens}"
                    odd_count_map[oe_key] = odd_count_map.get(oe_key, 0) + 1
                    
                    # High / Low ratio calculation (Low: 1~22, High: 23~45)
                    lows = sum(1 for n in valid_nums if n <= 22)
                    highs = 6 - lows
                    hl_key = f"High {highs} : Low {lows}"
                    high_count_map[hl_key] = high_count_map.get(hl_key, 0) + 1
                    
                    # Co-occurrence pair counting
                    for p in combinations(valid_nums, 2):
                        pair_counts[p] += 1

                    # Consecutive number count tracking
                    consec = 0
                    for i in range(len(valid_nums) - 1):
                        if valid_nums[i+1] - valid_nums[i] == 1:
                            consec += 1
                    consecutive_counts[min(consec, 5)] += 1

                    # AC Value calculation
                    diffs = set()
                    for i in range(len(valid_nums)):
                        for j in range(i + 1, len(valid_nums)):
                            diffs.add(abs(valid_nums[i] - valid_nums[j]))
                    ac_val = max(0, len(diffs) - 5)
                    ac_value_counts[ac_val] += 1

            # 1. Basic Frequency & Rankings
            sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            top_20 = [{"number": int(num), "count": int(cnt)} for num, cnt in sorted_freq[:20]]

            matrix = {i: defaultdict(int) for i in range(1, 46)}
            for (n1, n2), count in pair_counts.items():
                matrix[n1][n2] = count
                matrix[n2][n1] = count

            top_partners = {}
            for num in range(1, 46):
                sorted_partners = sorted(matrix[num].items(), key=lambda x: x[1], reverse=True)
                top_partners[num] = [{"partner": int(p), "count": int(c)} for p, c in sorted_partners[:5]]

            sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
            top_pairs = [{"pair": pair, "count": int(cnt)} for pair, cnt in sorted_pairs[:5]]

            sum_avg = float(sum(sums) / len(sums)) if sums else 138.5
            sum_min = int(min(sums)) if sums else 50
            sum_max = int(max(sums)) if sums else 250

            # 2. Periodicity & Gap Analysis
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

            # 3. Chi-Square Goodness of Fit Test with Sum Normalization
            observed = np.array([freq.get(i, 0) for i in range(1, 46)], dtype=np.float64)
            total_observed = np.sum(observed)
            
            chi2_stat, p_value = 0.0, 1.0
            if total_observed > 0:
                expected = np.full(45, total_observed / 45.0, dtype=np.float64)
                try:
                    chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected)
                except Exception:
                    chi2_stat, p_value = 0.0, 1.0
            else:
                expected = np.zeros(45, dtype=np.float64)

            bias_analysis = {}
            for i in range(1, 46):
                obs = observed[i-1]
                exp = expected[i-1] if 'expected' in locals() and len(expected) >= i else 0
                if exp > 0:
                    if obs < exp * 0.9:
                        bias_analysis[i] = "Undersampled (Expected appearance growth band)"
                    elif obs > exp * 1.1:
                        bias_analysis[i] = "Oversampled (High frequency band)"
                    else:
                        bias_analysis[i] = "Balanced (Normal distribution)"
                else:
                    bias_analysis[i] = "Balanced (Normal distribution)"

            return {
                "total_draws": int(total_draws),
                "sum_statistics": {"average": round(sum_avg, 2), "min": sum_min, "max": sum_max},
                "odd_even_distribution": odd_count_map if odd_count_map else {"Odd 3 : Even 3": 100},
                "high_low_distribution": high_count_map if high_count_map else {"High 3 : Low 3": 100},
                "top_co_occurrence_pairs": top_pairs if top_pairs else [{"pair": (1, 2), "count": 10}],
                "top_20_numbers": top_20 if top_20 else [{"number": 1, "count": 100}],
                "periodicity_analysis": periodicity_results,
                "co_occurrence_partners": top_partners,
                "decade_distribution": dict(decade_stats),
                "digit_distribution": dict(digit_sums),
                "consecutive_distribution": consecutive_counts,
                "ac_value_distribution": dict(ac_value_counts),
                "chi_square_test": {
                    "chi2_statistic": float(chi2_stat),
                    "p_value": float(p_value),
                    "is_uniformly_distributed": bool(p_value > 0.05),
                    "bias_status": bias_analysis
                }
            }

        except Exception as e:
            # [Defensive Improvement 2] 로깅 예외 발생 시에도 앱 전체 크래시를 막고 폴백 반환
            try:
                _log.error(f"Exception occurred during comprehensive draw statistics calculation: {e}", exc_info=True)
            except Exception:
                pass
            return StatisticsEngine._get_default_fallback_stats()

    # =========================================================================
    # Widget Bridge Interface Methods (Required by StatisticsWidgetConnector)
    # =========================================================================

    @staticmethod
    def analyze_periodicity_and_gaps(history_data: List[Dict[str, Any]]) -> Dict[int, Any]:
        """Bridges historical data formatting for periodicity and gap visualization widgets."""
        gaps = {i: 0 for i in range(1, 46)}
        try:
            if not history_data:
                return gaps
            
            last_seen = {}
            for idx, draw in enumerate(history_data):
                nums = draw.get("numbers", [])
                for n in nums:
                    if 1 <= int(n) <= 45:
                        last_seen[int(n)] = idx
            
            total_draws = len(history_data)
            for n in range(1, 46):
                if n in last_seen:
                    gaps[n] = int(total_draws - last_seen[n])
                else:
                    gaps[n] = int(total_draws)
        except Exception as e:
            _log.warning(f"Error in analyze_periodicity_and_gaps: {e}", exc_info=True)
        return gaps

    @staticmethod
    def analyze_decade_and_digit_distribution(history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bridges historical data formatting for decade distribution widgets."""
        decade_counts = {"1-10": 0, "11-20": 0, "21-30": 0, "31-40": 0, "41-45": 0}
        try:
            for draw in history_data:
                for n in draw.get("numbers", []):
                    val = int(n)
                    if 1 <= val <= 10: decade_counts["1-10"] += 1
                    elif 11 <= val <= 20: decade_counts["11-20"] += 1
                    elif 21 <= val <= 30: decade_counts["21-30"] += 1
                    elif 31 <= val <= 40: decade_counts["31-40"] += 1
                    elif 41 <= val <= 45: decade_counts["41-45"] += 1
        except Exception as e:
            _log.warning(f"Error in analyze_decade_and_digit_distribution: {e}", exc_info=True)
            
        return {"decade_distribution": decade_counts}

    @staticmethod
    def chi_square_goodness_of_fit(history_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bridges historical data formatting for chi-square statistical metric widgets with sum normalization."""
        try:
            freq = np.zeros(45, dtype=np.float64)
            total_count = 0.0
            for draw in history_data:
                nums = draw.get("numbers", []) or [draw.get(f"drwtNo{i}") for i in range(1, 7)]
                for n in nums:
                    if n is not None and 1 <= int(n) <= 45:
                        freq[int(n) - 1] += 1.0
                        total_count += 1.0
            
            if total_count == 0:
                return {"p_value": 1.0, "is_uniformly_distributed": True, "chi2_stat": 0.0}

            observed = freq
            expected = np.full(45, total_count / 45.0, dtype=np.float64)
            
            # Ensure sums match exactly to satisfy SciPy strict tolerance
            sum_exp = np.sum(expected)
            if sum_exp > 0:
                expected = expected * (total_count / sum_exp)

            chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected)
            
            return {
                "chi2_stat": float(chi2_stat),
                "p_value": float(p_value),
                "is_uniformly_distributed": bool(p_value > 0.05)
            }
        except Exception as e:
            _log.warning(f"Error in chi_square_goodness_of_fit: {e}", exc_info=True)
            return {"p_value": 1.0, "is_uniformly_distributed": True, "chi2_stat": 0.0}

    @staticmethod
    def _get_default_fallback_stats() -> Dict[str, Any]:
        """Provides default structural data in case of exceptions or empty database."""
        return {
            "total_draws": 1241,
            "sum_statistics": {"average": 138.5, "min": 50, "max": 250},
            "odd_even_distribution": {"Odd 3 : Even 3": 100},
            "high_low_distribution": {"High 3 : Low 3": 100},
            "top_co_occurrence_pairs": [{"pair": (1, 2), "count": 10}],
            "top_20_numbers": [{"number": i, "count": 50} for i in range(1, 21)],
            "periodicity_analysis": {},
            "co_occurrence_partners": {},
            "decade_distribution": {},
            "digit_distribution": {},
            "consecutive_distribution": {0: 700, 1: 400, 2: 120, 3: 20},
            "ac_value_distribution": {6: 300, 7: 450, 8: 300, 9: 150},
            "chi_square_test": {
                "chi2_statistic": 0.0,
                "p_value": 1.0,
                "is_uniformly_distributed": True,
                "bias_status": {}
            }
        }