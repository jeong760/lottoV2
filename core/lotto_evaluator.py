# -*- coding: utf-8 -*-
# core/lotto_evaluator.py
import sys
import os
import math
import logging
import random
from typing import Any, Dict, List, Tuple, Optional

# Ensure project root is in sys.path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "core" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

_log = logging.getLogger("LottoEvaluator")

class LottoEvaluator:
    """
    Dedicated evaluation and simulation engine for cross-checking generated lotto number sets,
    optimizing bonus swaps, performing rigorous Walk-Forward backtesting with ROI analysis,
    and executing Monte Carlo simulations for long-term probabilistic stress-testing.
    """

    @staticmethod
    def get_rank_label(match_count: int, has_bonus: bool = False) -> str:
        """
        Determines the lotto rank based on match count and bonus number presence,
        explicitly separating 2nd and 3rd place for 5 matches to prevent any confusion.
        
        - 6 matches: 1st
        - 5 matches + Bonus: 2nd (5+B)
        - 5 matches: 3rd (5 Matches)
        - 4 matches: 4th
        - 3 matches: 5th
        - Otherwise: '-'
        """
        if match_count == 6:
            return "1st"
        elif match_count == 5:
            return "2nd (5+B)" if has_bonus else "3rd (5 Matches)"
        elif match_count == 4:
            return "4th"
        elif match_count == 3:
            return "5th"
        else:
            return "-"

    @staticmethod
    def calculate_prize_money(match_count: int, has_bonus: bool) -> int:
        """Determines prize money based on standard rank rules (Unit: KRW)."""
        if match_count == 6:
            return 2000000000  # 1st prize (~2 billion KRW)
        elif match_count == 5 and has_bonus:
            return 50000000    # 2nd prize (~50 million KRW)
        elif match_count == 5:
            return 1500500     # 3rd prize (~1.5 million KRW)
        elif match_count == 4:
            return 50000       # 4th prize (50,000 KRW fixed)
        elif match_count == 3:
            return 5000        # 5th prize (5,000 KRW fixed)
        return 0

    @staticmethod
    def evaluate(generated_6_numbers: list, bonus_number: int, history_records: list, target_draw_no: int = None) -> tuple:
        """
        Cross-checks generated number sets with official historical draws.
        - If target_draw_no is provided and > 0, strictly evaluates against that specific draw.
        - If target_draw_no is None or <= 0, limits the comparison pool 
          to the last 5 years (approx. recent 260 draws) to prevent false positives.
        Returns: (rounds_info_str, max_match_count)
        """
        if not history_records:
            return "-", 0

        sorted_history = sorted(
            history_records, 
            key=lambda x: int(x.get("draw_no", x.get("drwNo", 0)) if isinstance(x, dict) else 0), 
            reverse=True
        )

        if target_draw_no is not None and target_draw_no > 0:
            target_draw = next((d for d in sorted_history if int(d.get("draw_no", d.get("drwNo", 0))) == int(target_draw_no)), None)
            if target_draw:
                history_pool = [target_draw]
            else:
                return "-", 0
        else:
            history_pool = sorted_history[:260]

        try:
            gen_set = set(int(n) for n in generated_6_numbers if n is not None and str(n).isdigit() and 1 <= int(n) <= 45)
        except (ValueError, TypeError):
            gen_set = set()

        if len(gen_set) != 6:
            return "-", 0

        matched_records = []
        max_matched = 0

        for draw in history_pool:
            drw_no = int(draw.get("draw_no", draw.get("drwNo", 0)))
            
            raw_winning = draw.get("numbers", [])
            if not raw_winning:
                raw_winning = [draw.get(f"drwtNo{i}") for i in range(1, 7)]
            
            winning_nums = set()
            for n in raw_winning:
                if n is not None:
                    try:
                        iv = int(n)
                        if 1 <= iv <= 45:
                            winning_nums.add(iv)
                    except (ValueError, TypeError):
                        pass

            try:
                drw_bonus = int(draw.get("bonus", draw.get("bnusNo", 0)))
            except (ValueError, TypeError):
                drw_bonus = 0

            if not winning_nums:
                continue

            matches = len(gen_set.intersection(winning_nums))
            has_bonus = (int(bonus_number) == drw_bonus) or (drw_bonus in gen_set)
            
            max_matched = max(max_matched, matches)

            rank_str = LottoEvaluator.get_rank_label(matches, has_bonus)
            
            if "-" not in rank_str:
                rank_priority = 99
                if "1st" in rank_str: rank_priority = 1
                elif "2nd" in rank_str: rank_priority = 2
                elif "3rd" in rank_str: rank_priority = 3
                elif "4th" in rank_str: rank_priority = 4
                elif "5th" in rank_str: rank_priority = 5

                matched_records.append({
                    "priority": rank_priority,
                    "draw_no": drw_no,
                    "rank": rank_str,
                    "matches": matches
                })

        if not matched_records:
            return "-", max_matched

        matched_records.sort(key=lambda x: (x["priority"], -x["draw_no"]))
        rounds_desc = ", ".join([f"{item['draw_no']} ({item['rank']})" for item in matched_records])

        _log.debug(f"Evaluated set against history: max_matches={max_matched}, rounds={rounds_desc}")
        return rounds_desc, max_matched

    @staticmethod
    def calculate_probability(match_count: int, bonus_match: Any = False) -> str:
        """
        Calculates mathematical probability string based on match counts,
        strictly separating 2nd (5 + Bonus) and 3rd (5 matches only) place probabilities.
        Handles string/boolean coercion safely to prevent UI string bugs.
        """
        try:
            if isinstance(bonus_match, str):
                bonus_match_bool = bonus_match.strip().lower() in ("true", "1", "yes", "y")
            else:
                bonus_match_bool = bool(bonus_match)

            total_cases = math.comb(45, 6)
            favorable_cases = 0

            if match_count == 6:
                favorable_cases = math.comb(6, 6) * math.comb(39, 0)
            elif match_count == 5 and bonus_match_bool:
                favorable_cases = math.comb(6, 5) * math.comb(1, 1) * math.comb(38, 0)
            elif match_count == 5:
                favorable_cases = math.comb(6, 5) * math.comb(38, 1)
            elif match_count == 4:
                favorable_cases = math.comb(6, 4) * math.comb(39, 2)
            elif match_count == 3:
                favorable_cases = math.comb(6, 3) * math.comb(39, 3)
            elif match_count == 2:
                favorable_cases = math.comb(6, 2) * math.comb(39, 4)
            elif match_count == 1:
                favorable_cases = math.comb(6, 1) * math.comb(39, 5)
            else:
                favorable_cases = math.comb(6, 0) * math.comb(39, 6)

            raw_prob = (favorable_cases / total_cases) * 100 if total_cases > 0 else 0.0

            if 0 < raw_prob < 0.001:
                return f"{raw_prob:.7f}%"
            else:
                return f"{raw_prob:.4f}%"
        except Exception as e:
            _log.warning(f"Error in calculate_probability: {e}", exc_info=True)
            return "0.0000%"

    @staticmethod
    def run_monte_carlo_simulation(generated_6_numbers: list, simulations_count: int = 10000) -> dict:
        """
        Simulates thousands of virtual lotto draws to evaluate the long-term statistical 
        distribution of match counts, prize payouts, and expected ROI for a given number set.
        """
        if not generated_6_numbers or len(generated_6_numbers) != 6:
            return {"status": "error", "message": "Invalid 6 numbers set for Monte Carlo simulation."}

        try:
            gen_set = set(int(n) for n in generated_6_numbers)
            match_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
            total_prize = 0
            sim_count = int(simulations_count)
            total_cost = sim_count * 1000

            for _ in range(sim_count):
                all_balls = random.sample(range(1, 46), 7)
                win_set = set(all_balls[:6])
                bonus_no = all_balls[6]

                matches = len(gen_set.intersection(win_set))
                has_bonus = bonus_no in gen_set
                match_counts[matches] = match_counts.get(matches, 0) + 1

                prize = LottoEvaluator.calculate_prize_money(matches, has_bonus)
                total_prize += prize

            roi = (total_prize / total_cost) * 100 if total_cost > 0 else 0.0
            match_probabilities = {k: round((v / sim_count) * 100, 4) for k, v in match_counts.items()}

            _log.info(f"Monte Carlo simulation completed successfully ({sim_count:,} runs). Estimated ROI: {roi:.2f}%")
            return {
                "status": "success",
                "simulations_count": sim_count,
                "match_distribution": match_counts,
                "match_probabilities_pct": match_probabilities,
                "total_cost": total_cost,
                "total_prize": total_prize,
                "roi": round(roi, 2)
            }
        except Exception as e:
            _log.error(f"Error in run_monte_carlo_simulation: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    @staticmethod
    def run_backtest_simulation(all_draws: list, algorithm_engine, start_test_draw: int = 501, sets_per_draw: int = 5, algorithm_name: str = "GA & K-Means Ensemble", *args, **kwargs) -> dict:
        """
        [Fixed Train & Test Backtesting Simulation]
        - Training Pool: Fixed to draws 1 to (start_test_draw - 1) -> e.g., 1 to 500
        - Test Pool: Draws start_test_draw to the latest available draw -> e.g., 501 onwards
        - Random Baseline: Simultaneously measures performance against random number generation.
        - Robustly accepts any unexpected keyword arguments (e.g., test_window_size) to prevent type errors.
        """
        test_window_size = kwargs.get('test_window_size', None)
        start_draw = int(start_test_draw)
        set_count = int(sets_per_draw)

        if not all_draws or len(all_draws) < start_draw:
            return {"status": "error", "message": "Not enough historical data for the specified test range."}

        sorted_draws = sorted(all_draws, key=lambda x: int(x.get("draw_no", x.get("drwNo", 0)) if isinstance(x, dict) else 0))
        
        fixed_train_pool = [d for d in sorted_draws if int(d.get("draw_no", d.get("drwNo", 0))) < start_draw]
        test_draws = [d for d in sorted_draws if int(d.get("draw_no", d.get("drwNo", 0))) >= start_draw]

        if test_window_size and isinstance(test_window_size, int) and test_window_size > 0:
            test_draws = test_draws[-test_window_size:]

        def _safe_pct(part: float, total: float) -> float:
            return round((float(part) / float(total)) * 100.0, 4) if total > 0 else 0.0

        def _classification_metrics(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
            precision = (float(tp) / float(tp + fp)) if (tp + fp) > 0 else 0.0
            recall = (float(tp) / float(tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
            return round(precision * 100.0, 4), round(recall * 100.0, 4), round(f1 * 100.0, 4)

        algo_cost = 0
        algo_prize = 0
        algo_ranks = {"1st": 0, "2nd (5+B)": 0, "3rd (5 Matches)": 0, "4th": 0, "5th": 0, "-": 0}
        algo_match_distribution = {i: 0 for i in range(7)}
        algo_tp = 0
        algo_fp = 0
        algo_fn = 0

        rand_cost = 0
        rand_prize = 0
        rand_ranks = {"1st": 0, "2nd (5+B)": 0, "3rd (5 Matches)": 0, "4th": 0, "5th": 0, "-": 0}
        rand_match_distribution = {i: 0 for i in range(7)}
        rand_tp = 0
        rand_fp = 0
        rand_fn = 0

        for draw in test_draws:
            raw_winning = draw.get("numbers", [])
            if not raw_winning:
                raw_winning = [draw.get(f"drwtNo{i}") for i in range(1, 7)]
            
            winning_nums = set()
            for n in raw_winning:
                if n is not None:
                    try:
                        iv = int(n)
                        if 1 <= iv <= 45:
                            winning_nums.add(iv)
                    except (ValueError, TypeError):
                        pass

            try:
                winning_bonus = int(draw.get("bonus", draw.get("bnusNo", 0)))
            except (ValueError, TypeError):
                winning_bonus = 0

            if not winning_nums or len(winning_nums) < 6:
                continue

            generated_sets = []
            try:
                if hasattr(algorithm_engine, "generate_sets"):
                    generated_sets = algorithm_engine.generate_sets(set_count=set_count, history_data=fixed_train_pool)
                elif callable(algorithm_engine):
                    generated_sets = algorithm_engine(fixed_train_pool, set_count)
                else:
                    for _ in range(set_count):
                        generated_sets.append(sorted(random.sample(range(1, 46), 6)))
            except Exception:
                for _ in range(set_count):
                    generated_sets.append(sorted(random.sample(range(1, 46), 6)))

            # Evaluate algorithm sets
            algo_predicted_union = set()
            for s in generated_sets:
                try:
                    s_set = set(int(n) for n in s[:6])
                except (ValueError, TypeError):
                    continue
                if len(s_set) < 6:
                    continue
                algo_predicted_union.update(s_set)
                
                matches = len(s_set.intersection(winning_nums))
                has_bonus = (winning_bonus in s_set)
                algo_match_distribution[matches] = algo_match_distribution.get(matches, 0) + 1

                prize = LottoEvaluator.calculate_prize_money(matches, has_bonus)
                rank_str = LottoEvaluator.get_rank_label(matches, has_bonus)

                algo_cost += 1000
                algo_prize += prize
                if rank_str in algo_ranks:
                    algo_ranks[rank_str] += 1
                else:
                    algo_ranks["-"] += 1
            algo_tp += len(algo_predicted_union.intersection(winning_nums))
            algo_fp += len(algo_predicted_union.difference(winning_nums))
            algo_fn += len(winning_nums.difference(algo_predicted_union))

            # Evaluate random baseline sets
            rand_predicted_union = set()
            for _ in range(set_count):
                rand_s = set(random.sample(range(1, 46), 6))
                rand_predicted_union.update(rand_s)
                matches = len(rand_s.intersection(winning_nums))
                has_bonus = (winning_bonus in rand_s)
                rand_match_distribution[matches] = rand_match_distribution.get(matches, 0) + 1

                prize = LottoEvaluator.calculate_prize_money(matches, has_bonus)
                rank_str = LottoEvaluator.get_rank_label(matches, has_bonus)

                rand_cost += 1000
                rand_prize += prize
                if rank_str in rand_ranks:
                    rand_ranks[rank_str] += 1
                else:
                    rand_ranks["-"] += 1
            rand_tp += len(rand_predicted_union.intersection(winning_nums))
            rand_fp += len(rand_predicted_union.difference(winning_nums))
            rand_fn += len(winning_nums.difference(rand_predicted_union))

        algo_roi = (algo_prize / algo_cost) * 100 if algo_cost > 0 else 0.0
        rand_roi = (rand_prize / rand_cost) * 100 if rand_cost > 0 else 0.0
        algo_ticket_count = sum(algo_match_distribution.values())
        rand_ticket_count = sum(rand_match_distribution.values())

        algo_precision, algo_recall, algo_f1 = _classification_metrics(algo_tp, algo_fp, algo_fn)
        rand_precision, rand_recall, rand_f1 = _classification_metrics(rand_tp, rand_fp, rand_fn)

        algo_metrics = {
            "ticket_count": int(algo_ticket_count),
            "hit_rate": _safe_pct(
                algo_match_distribution.get(3, 0)
                + algo_match_distribution.get(4, 0)
                + algo_match_distribution.get(5, 0)
                + algo_match_distribution.get(6, 0),
                algo_ticket_count,
            ),
            "match_3_rate": _safe_pct(algo_match_distribution.get(3, 0), algo_ticket_count),
            "match_4_rate": _safe_pct(algo_match_distribution.get(4, 0), algo_ticket_count),
            "match_5_rate": _safe_pct(algo_match_distribution.get(5, 0), algo_ticket_count),
            "match_6_rate": _safe_pct(algo_match_distribution.get(6, 0), algo_ticket_count),
            "precision": algo_precision,
            "recall": algo_recall,
            "f1_score": algo_f1,
            "roi": round(algo_roi, 2),
        }

        rand_metrics = {
            "ticket_count": int(rand_ticket_count),
            "hit_rate": _safe_pct(
                rand_match_distribution.get(3, 0)
                + rand_match_distribution.get(4, 0)
                + rand_match_distribution.get(5, 0)
                + rand_match_distribution.get(6, 0),
                rand_ticket_count,
            ),
            "match_3_rate": _safe_pct(rand_match_distribution.get(3, 0), rand_ticket_count),
            "match_4_rate": _safe_pct(rand_match_distribution.get(4, 0), rand_ticket_count),
            "match_5_rate": _safe_pct(rand_match_distribution.get(5, 0), rand_ticket_count),
            "match_6_rate": _safe_pct(rand_match_distribution.get(6, 0), rand_ticket_count),
            "precision": rand_precision,
            "recall": rand_recall,
            "f1_score": rand_f1,
            "roi": round(rand_roi, 2),
        }

        return {
            "status": "success",
            "algorithm_name": algorithm_name,
            "train_range": f"1 ~ {start_draw - 1}",
            "test_start_draw": start_draw,
            "test_total_draws": len(test_draws),
            "algorithm": {
                "total_cost": algo_cost,
                "total_prize": algo_prize,
                "roi": round(algo_roi, 2),
                "ranks": algo_ranks,
                "match_distribution": algo_match_distribution,
                "metrics": algo_metrics,
                "hit_rate": algo_metrics["hit_rate"],
                "match_3_rate": algo_metrics["match_3_rate"],
                "match_4_rate": algo_metrics["match_4_rate"],
                "match_5_rate": algo_metrics["match_5_rate"],
                "match_6_rate": algo_metrics["match_6_rate"],
                "precision": algo_metrics["precision"],
                "recall": algo_metrics["recall"],
                "f1_score": algo_metrics["f1_score"],
            },
            "random_baseline": {
                "total_cost": rand_cost,
                "total_prize": rand_prize,
                "roi": round(rand_roi, 2),
                "ranks": rand_ranks,
                "match_distribution": rand_match_distribution,
                "metrics": rand_metrics,
                "hit_rate": rand_metrics["hit_rate"],
                "match_3_rate": rand_metrics["match_3_rate"],
                "match_4_rate": rand_metrics["match_4_rate"],
                "match_5_rate": rand_metrics["match_5_rate"],
                "match_6_rate": rand_metrics["match_6_rate"],
                "precision": rand_metrics["precision"],
                "recall": rand_metrics["recall"],
                "f1_score": rand_metrics["f1_score"],
            }
        }

    @staticmethod
    def optimize_bonus_swap(generated_6_numbers: list, bonus_number: int, latest_winning_tuple: tuple) -> dict:
        """
        Simulates replacing 1 number from the generated set with the bonus number.
        - latest_winning_tuple: (winning_set, winning_bonus)
        """
        if not generated_6_numbers or len(generated_6_numbers) != 6:
            return {"status": "error", "message": "Invalid 6 numbers set."}

        if bonus_number is None:
            return {"status": "error", "message": "No bonus number available."}

        try:
            winning_set, winning_bonus = latest_winning_tuple if latest_winning_tuple else (set(), 0)
            
            if winning_set:
                target_winning = set(int(n) for n in winning_set)
            else:
                target_winning = set([7, 14, 22, 31, 38, 45])

            target_bonus = int(winning_bonus) if winning_bonus and int(winning_bonus) > 0 else int(bonus_number)
            
            valid_gen = [int(n) for n in generated_6_numbers]
            original_matches = len(set(valid_gen).intersection(target_winning))
            has_orig_bonus = target_bonus > 0 and (target_bonus in valid_gen or (winning_bonus and int(winning_bonus) in valid_gen))
            
            original_prob_str = LottoEvaluator.calculate_probability(original_matches, has_orig_bonus)

            simulations = []
            for i in range(6):
                swapped_set = list(valid_gen)
                removed_num = swapped_set[i]
                swapped_set[i] = int(bonus_number)
                swapped_sorted = sorted(swapped_set)
                
                matches = len(set(swapped_sorted).intersection(target_winning))
                has_bonus = target_bonus > 0 and (int(bonus_number) == target_bonus or target_bonus in swapped_sorted)
                
                prob_str = LottoEvaluator.calculate_probability(matches, has_bonus)

                rank_label = LottoEvaluator.get_rank_label(matches, has_bonus)
                rank = "Miss"
                if "1st" in rank_label: rank = "1st Prize"
                elif "2nd" in rank_label: rank = "2nd Prize"
                elif "3rd" in rank_label: rank = "3rd Prize"
                elif "4th" in rank_label: rank = "4th Prize"
                elif "5th" in rank_label: rank = "5th Prize"

                simulations.append({
                    "swap_type": "1-Number Swap",
                    "removed": removed_num,
                    "added": int(bonus_number),
                    "new_set": swapped_sorted,
                    "matches": matches,
                    "has_bonus": has_bonus,
                    "rank": rank,
                    "probability": prob_str
                })

            simulations.sort(key=lambda x: x['matches'], reverse=True)
            best_option = simulations[0] if simulations else None

            _log.debug("Bonus swap optimization simulation completed.")
            return {
                "status": "success",
                "original_set": valid_gen,
                "original_matches": original_matches,
                "original_probability": original_prob_str,
                "bonus_number": int(bonus_number),
                "best_swap": best_option,
                "all_simulations": simulations
            }
        except Exception as e:
            _log.error(f"Error in optimize_bonus_swap: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}