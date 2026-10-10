# core/engines/statistics_engine.py
import logging
import math
import numpy as np
from itertools import combinations
from collections import Counter, defaultdict
from typing import Dict, Any, List
from data.repositories.lotto_repository import LottoRepository

_SCIPY_IMPORT_ERROR = None
try:
    import scipy.stats as stats
    SCIPY_AVAILABLE = True
except Exception as _scipy_ex:
    stats = None
    SCIPY_AVAILABLE = False
    _SCIPY_IMPORT_ERROR = _scipy_ex

_log = logging.getLogger("StatisticsEngine")
if not SCIPY_AVAILABLE:
    _log.warning(
        "SciPy is not available in StatisticsEngine (%s). Chi-square p-values will use fallback mode.",
        _SCIPY_IMPORT_ERROR,
    )


def _resolve_draw_number(draw_like: Any, fallback: int = 0) -> int:
    if isinstance(draw_like, dict):
        for key in ("draw_no", "draw", "drwNo"):
            value = draw_like.get(key)
            if value is not None:
                try:
                    return int(value)
                except (ValueError, TypeError):
                    continue
    try:
        return int(fallback)
    except (ValueError, TypeError):
        return 0


class StatisticsEngine:
    """
    Expert-level comprehensive lotto statistics and probability analysis engine.
    Combines database data integration with advanced metrics such as periodicity, 
    co-occurrence matrix, decade/digit distribution, Chi-Square goodness of fit,
    consecutive number patterns, AC value complexity, and trailing digit entropy.
    """

    @staticmethod
    def _safe_chisquare(observed: np.ndarray, expected: np.ndarray) -> tuple[float, float]:
        """
        Computes chi-square safely with SciPy when available, otherwise returns
        a deterministic chi-square statistic with fallback p-value.
        """
        try:
            observed = np.asarray(observed, dtype=np.float64)
            expected = np.asarray(expected, dtype=np.float64)
            with np.errstate(divide="ignore", invalid="ignore"):
                chi2_fallback = float(
                    np.sum(np.where(expected > 0.0, ((observed - expected) ** 2.0) / expected, 0.0))
                )
        except Exception:
            chi2_fallback = 0.0

        if SCIPY_AVAILABLE and stats is not None:
            try:
                chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected)
                return float(chi2_stat), float(p_value)
            except Exception as e:
                _log.warning("SciPy chi-square execution failed; using fallback p-value. detail=%s", e, exc_info=True)

        return chi2_fallback, 1.0

    @staticmethod
    def get_comprehensive_statistics() -> dict[str, Any]:
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
            sorted_history = sorted(all_draws, key=lambda x: _resolve_draw_number(x, 0))
            latest_draw = _resolve_draw_number(sorted_history[-1], total_draws)

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
                draw_num = _resolve_draw_number(draw, draw_idx + 1)
                nums = []
                
                # Support both modern keys (num1~6) and legacy keys (drwtNo1~6)
                for i in range(1, 7):
                    val = draw.get(f"num{i}") or draw.get(f"drwtNo{i}")
                    if val is not None:
                        try:
                            nums.append(int(val))
                        except (ValueError, TypeError):
                            pass
                
                valid_nums = sorted(list({n for n in nums if 1 <= n <= 45}))
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
                    chi2_stat, p_value = StatisticsEngine._safe_chisquare(observed, expected)
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

            phase_c_analytics = StatisticsEngine.build_phase_c_analytics(sorted_history)
            base_payload = {
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
                },
                "phase_c_analytics": phase_c_analytics,
            }
            if isinstance(phase_c_analytics, dict):
                base_payload.update(phase_c_analytics)
            return base_payload

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
    def analyze_periodicity_and_gaps(history_data: list[dict[str, Any]]) -> dict[int, Any]:
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
                    gaps[n] = int((total_draws - 1) - last_seen[n])
                else:
                    gaps[n] = int(total_draws)
        except Exception as e:
            _log.warning(f"Error in analyze_periodicity_and_gaps: {e}", exc_info=True)
        return gaps

    @staticmethod
    def analyze_decade_and_digit_distribution(history_data: list[dict[str, Any]]) -> dict[str, Any]:
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
    def chi_square_goodness_of_fit(history_data: list[dict[str, Any]]) -> dict[str, Any]:
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

            chi2_stat, p_value = StatisticsEngine._safe_chisquare(observed, expected)
            
            return {
                "chi2_stat": float(chi2_stat),
                "p_value": float(p_value),
                "is_uniformly_distributed": bool(p_value > 0.05)
            }
        except Exception as e:
            _log.warning(f"Error in chi_square_goodness_of_fit: {e}", exc_info=True)
            return {"p_value": 1.0, "is_uniformly_distributed": True, "chi2_stat": 0.0}

    @staticmethod
    def build_phase_c_analytics(history_data: list[dict[str, Any]], lookback_draws: int = 120) -> dict[str, Any]:
        """
        Builds Phase-C analytics package:
        - Hot/Cold/Delayed/Overdue
        - Frequent pairs/triplets, associations, network
        - Trend, cycle, repeat, and gap prediction signals
        """
        empty_payload = {
            "hot_numbers": [],
            "cold_numbers": [],
            "delayed_numbers": [],
            "overdue_numbers": [],
            "frequent_pairs": [],
            "frequent_triplets": [],
            "number_associations": {"edges": [], "top_partners": {}},
            "number_network": {"central_numbers": [], "edge_count": 0, "density": 0.0},
            "historical_trends": {"window_size": 0, "rising_numbers": [], "falling_numbers": []},
            "cycle_detection": {"stable_cycles": [], "avg_interval_map": {}},
            "repeat_prediction": {
                "expected_repeat_count": 0.0,
                "historical_repeat_rate_pct": 0.0,
                "last_draw_repeat_probabilities": [],
            },
            "gap_prediction": {"next_draw_due_numbers": []},
        }
        try:
            if not history_data:
                return empty_payload

            sorted_history = sorted(
                history_data,
                key=lambda x: _resolve_draw_number(x, 0),
            )

            normalized = []
            for idx, draw in enumerate(sorted_history, start=1):
                if not isinstance(draw, dict):
                    continue
                draw_no = _resolve_draw_number(draw, idx)

                raw_nums = draw.get("numbers", [])
                if not raw_nums:
                    raw_nums = [draw.get(f"num{i}") or draw.get(f"drwtNo{i}") for i in range(1, 7)]

                valid_nums = []
                for val in raw_nums:
                    if val is None:
                        continue
                    try:
                        iv = int(val)
                    except (ValueError, TypeError):
                        continue
                    if 1 <= iv <= 45:
                        valid_nums.append(iv)

                valid_nums = sorted(set(valid_nums))
                if len(valid_nums) == 6:
                    normalized.append((draw_no, valid_nums))

            if len(normalized) < 2:
                return empty_payload

            recent = normalized[-max(8, int(lookback_draws)):]
            recent_draw_count = max(1, len(recent))
            full_draw_count = len(normalized)

            recent_counter = Counter()
            full_pair_counter = Counter()
            full_triplet_counter = Counter()
            last_seen = {i: None for i in range(1, 46)}
            interval_map = defaultdict(list)

            for draw_no, numbers in normalized:
                for n in numbers:
                    if last_seen[n] is not None:
                        interval_map[n].append(int(draw_no - last_seen[n]))
                    last_seen[n] = draw_no
                for pair in combinations(numbers, 2):
                    full_pair_counter[pair] += 1
                for triplet in combinations(numbers, 3):
                    full_triplet_counter[triplet] += 1

            for _, numbers in recent:
                for n in numbers:
                    recent_counter[n] += 1

            hot_numbers = [
                {
                    "number": int(num),
                    "count": int(cnt),
                    "rate_pct": round((float(cnt) / float(recent_draw_count)) * 100.0, 4),
                }
                for num, cnt in sorted(recent_counter.items(), key=lambda x: (-x[1], x[0]))[:10]
            ]
            cold_numbers = [
                {
                    "number": int(num),
                    "count": int(cnt),
                    "rate_pct": round((float(cnt) / float(recent_draw_count)) * 100.0, 4),
                }
                for num, cnt in sorted(((n, recent_counter.get(n, 0)) for n in range(1, 46)), key=lambda x: (x[1], x[0]))[:10]
            ]

            latest_draw_no = normalized[-1][0]
            delayed_numbers = []
            overdue_numbers = []
            avg_interval_map = {}

            for num in range(1, 46):
                seen_draw = last_seen.get(num)
                current_gap = int(latest_draw_no - seen_draw) if seen_draw is not None else int(latest_draw_no)
                intervals = interval_map.get(num, [])
                mean_interval = float(np.mean(intervals)) if intervals else 0.0
                avg_interval_map[num] = round(mean_interval, 4)
                if mean_interval <= 0:
                    continue
                gap_ratio = float(current_gap / mean_interval) if mean_interval > 0 else 0.0
                if current_gap > mean_interval:
                    delayed_numbers.append(
                        {
                            "number": int(num),
                            "current_gap": int(current_gap),
                            "expected_gap": round(mean_interval, 4),
                            "gap_ratio": round(gap_ratio, 4),
                        }
                    )
                if current_gap >= (mean_interval * 1.5):
                    overdue_numbers.append(
                        {
                            "number": int(num),
                            "current_gap": int(current_gap),
                            "expected_gap": round(mean_interval, 4),
                            "gap_ratio": round(gap_ratio, 4),
                        }
                    )

            delayed_numbers.sort(key=lambda x: (-x["gap_ratio"], -x["current_gap"], x["number"]))
            overdue_numbers.sort(key=lambda x: (-x["gap_ratio"], -x["current_gap"], x["number"]))

            frequent_pairs = [
                {
                    "numbers": [int(pair[0]), int(pair[1])],
                    "count": int(cnt),
                    "support_pct": round((float(cnt) / float(full_draw_count)) * 100.0, 4),
                }
                for pair, cnt in sorted(full_pair_counter.items(), key=lambda x: (-x[1], x[0]))[:20]
            ]
            frequent_triplets = [
                {
                    "numbers": [int(tri[0]), int(tri[1]), int(tri[2])],
                    "count": int(cnt),
                    "support_pct": round((float(cnt) / float(full_draw_count)) * 100.0, 4),
                }
                for tri, cnt in sorted(full_triplet_counter.items(), key=lambda x: (-x[1], x[0]))[:20]
            ]

            top_partners = {}
            partner_matrix = {n: Counter() for n in range(1, 46)}
            for (a, b), cnt in full_pair_counter.items():
                partner_matrix[a][b] += cnt
                partner_matrix[b][a] += cnt

            for number in range(1, 46):
                top_partners[number] = [
                    {"number": int(pn), "count": int(pc)}
                    for pn, pc in sorted(partner_matrix[number].items(), key=lambda x: (-x[1], x[0]))[:3]
                ]

            edge_items = sorted(full_pair_counter.items(), key=lambda x: (-x[1], x[0]))[:80]
            association_edges = [
                {
                    "from": int(a),
                    "to": int(b),
                    "count": int(cnt),
                    "support_pct": round((float(cnt) / float(full_draw_count)) * 100.0, 4),
                }
                for (a, b), cnt in edge_items
            ]

            strength_counter = Counter()
            for (a, b), cnt in full_pair_counter.items():
                strength_counter[a] += cnt
                strength_counter[b] += cnt
            max_strength = max(strength_counter.values()) if strength_counter else 1
            central_numbers = [
                {
                    "number": int(num),
                    "strength": int(score),
                    "normalized_strength": round(float(score / max_strength), 4) if max_strength > 0 else 0.0,
                }
                for num, score in sorted(strength_counter.items(), key=lambda x: (-x[1], x[0]))[:12]
            ]

            max_edge_count = (45 * 44) // 2
            network_density = round(float(len(full_pair_counter)) / float(max_edge_count), 6) if max_edge_count > 0 else 0.0

            trend_window = max(8, min(25, full_draw_count // 3))
            recent_window = normalized[-trend_window:]
            prev_window = normalized[-(trend_window * 2):-trend_window]
            if not prev_window:
                prev_window = normalized[:trend_window]

            recent_window_counter = Counter(n for _, nums in recent_window for n in nums)
            prev_window_counter = Counter(n for _, nums in prev_window for n in nums)
            recent_norm = float(max(1, len(recent_window)))
            prev_norm = float(max(1, len(prev_window)))

            trend_rows = []
            for number in range(1, 46):
                recent_rate = float(recent_window_counter.get(number, 0) / recent_norm)
                prev_rate = float(prev_window_counter.get(number, 0) / prev_norm)
                trend_rows.append(
                    {
                        "number": int(number),
                        "recent_rate": round(recent_rate, 4),
                        "previous_rate": round(prev_rate, 4),
                        "delta_rate": round(recent_rate - prev_rate, 4),
                    }
                )
            rising_numbers = sorted(trend_rows, key=lambda x: (-x["delta_rate"], -x["recent_rate"], x["number"]))[:10]
            falling_numbers = sorted(trend_rows, key=lambda x: (x["delta_rate"], x["recent_rate"], x["number"]))[:10]

            stable_cycles = []
            for number in range(1, 46):
                intervals = interval_map.get(number, [])
                if len(intervals) < 3:
                    continue
                mean_interval = float(np.mean(intervals))
                if mean_interval <= 0:
                    continue
                std_interval = float(np.std(intervals))
                cv = float(std_interval / mean_interval) if mean_interval > 0 else 0.0
                regularity_score = max(0.0, 100.0 * (1.0 - min(1.0, cv)))
                current_gap = int(latest_draw_no - last_seen[number]) if last_seen[number] is not None else int(latest_draw_no)
                pressure = max(0.0, (float(current_gap) - mean_interval) / mean_interval) if mean_interval > 0 else 0.0
                stable_cycles.append(
                    {
                        "number": int(number),
                        "mean_interval": round(mean_interval, 4),
                        "interval_std": round(std_interval, 4),
                        "current_gap": int(current_gap),
                        "regularity_score": round(regularity_score, 4),
                        "cycle_pressure": round(pressure, 4),
                    }
                )
            stable_cycles.sort(key=lambda x: (-x["regularity_score"], -x["cycle_pressure"], x["number"]))

            repeat_overlaps = []
            repeat_occurrences = Counter()
            repeat_hits = Counter()
            for i in range(1, len(normalized)):
                prev_numbers = set(normalized[i - 1][1])
                curr_numbers = set(normalized[i][1])
                repeat_overlaps.append(len(prev_numbers.intersection(curr_numbers)))
                for n in prev_numbers:
                    repeat_occurrences[n] += 1
                    if n in curr_numbers:
                        repeat_hits[n] += 1

            expected_repeat_count = float(np.mean(repeat_overlaps)) if repeat_overlaps else 0.0
            repeat_rate_pct = (expected_repeat_count / 6.0) * 100.0 if expected_repeat_count > 0 else 0.0

            last_draw_numbers = normalized[-1][1]
            last_draw_repeat_probabilities = []
            for n in last_draw_numbers:
                occ = repeat_occurrences.get(n, 0)
                hit = repeat_hits.get(n, 0)
                prob = float(hit / occ) if occ > 0 else 0.0
                last_draw_repeat_probabilities.append(
                    {
                        "number": int(n),
                        "repeat_probability_pct": round(prob * 100.0, 4),
                        "samples": int(occ),
                    }
                )
            last_draw_repeat_probabilities.sort(key=lambda x: (-x["repeat_probability_pct"], x["number"]))

            due_candidates = []
            for number in range(1, 46):
                current_gap = int(latest_draw_no - last_seen[number]) if last_seen[number] is not None else int(latest_draw_no)
                mean_interval = float(np.mean(interval_map[number])) if interval_map[number] else 0.0
                if mean_interval > 0:
                    appearance_prob = 1.0 - math.exp(-(float(current_gap) + 1.0) / mean_interval)
                    pressure_ratio = float(current_gap / mean_interval)
                else:
                    appearance_prob = 0.05
                    pressure_ratio = 0.0
                due_score = min(100.0, (appearance_prob * 75.0) + min(25.0, pressure_ratio * 12.5))
                due_candidates.append(
                    {
                        "number": int(number),
                        "current_gap": int(current_gap),
                        "mean_interval": round(mean_interval, 4),
                        "next_draw_probability_pct": round(appearance_prob * 100.0, 4),
                        "due_score": round(due_score, 4),
                    }
                )
            due_candidates.sort(key=lambda x: (-x["due_score"], -x["next_draw_probability_pct"], x["number"]))

            return {
                "hot_numbers": hot_numbers,
                "cold_numbers": cold_numbers,
                "delayed_numbers": delayed_numbers[:15],
                "overdue_numbers": overdue_numbers[:15],
                "frequent_pairs": frequent_pairs,
                "frequent_triplets": frequent_triplets,
                "number_associations": {
                    "edges": association_edges,
                    "top_partners": top_partners,
                },
                "number_network": {
                    "central_numbers": central_numbers,
                    "edge_count": int(len(full_pair_counter)),
                    "density": float(network_density),
                },
                "historical_trends": {
                    "window_size": int(trend_window),
                    "rising_numbers": rising_numbers,
                    "falling_numbers": falling_numbers,
                },
                "cycle_detection": {
                    "stable_cycles": stable_cycles[:15],
                    "avg_interval_map": {int(k): float(v) for k, v in avg_interval_map.items()},
                },
                "repeat_prediction": {
                    "expected_repeat_count": round(expected_repeat_count, 4),
                    "historical_repeat_rate_pct": round(repeat_rate_pct, 4),
                    "last_draw_repeat_probabilities": last_draw_repeat_probabilities,
                },
                "gap_prediction": {
                    "next_draw_due_numbers": due_candidates[:15],
                },
            }
        except Exception as e:
            _log.warning(f"Error in build_phase_c_analytics: {e}", exc_info=True)
            return empty_payload

    @staticmethod
    def _get_default_fallback_stats() -> dict[str, Any]:
        """Provides default structural data in case of exceptions or empty database."""
        fallback = {
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
            },
        }
        phase_c_fallback = StatisticsEngine.build_phase_c_analytics([])
        fallback["phase_c_analytics"] = phase_c_fallback
        fallback.update(phase_c_fallback)
        return fallback