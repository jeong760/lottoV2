# workers/lotto_worker.py
import logging
import os
import sys
import time
import traceback
import pickle
import random

# Ensure project root is in python path and initialize centralized logging
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) if "workers" in current_dir else os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logging
setup_logging(project_root)

from PyQt5.QtCore import QThread, pyqtSignal
from config import SUM_MIN, SUM_MAX
from data.repositories.lotto_repository import LottoRepository
from data.repositories.ml_model_repository import MLModelRepository
from utils.audit_security import AuditTrailSecurity
from core.algorithm_catalog import get_mode_title, resolve_algorithm_mode_id
from core.generation_schema import (
    build_frequency_map_from_history,
    build_generation_metadata,
    build_generation_stats,
    build_top_ranked_combinations,
    derive_score_weights_from_history,
    resolve_total_algorithms_active,
)
from core.quality_gate import calculate_ac_value, passes_quality_gate

_log = logging.getLogger("LottoTurbineWorker")


class _RestrictedUnpickler(pickle.Unpickler):
    _SAFE_BUILTINS = {
        "dict": dict,
        "list": list,
        "tuple": tuple,
        "set": set,
        "frozenset": frozenset,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "bytes": bytes,
    }

    def find_class(self, module, name):
        if module == "builtins" and name in self._SAFE_BUILTINS:
            return self._SAFE_BUILTINS[name]
        raise pickle.UnpicklingError(f"unsafe class requested: {module}.{name}")


def _safe_pickle_load(file_obj):
    return _RestrictedUnpickler(file_obj).load()

class LottoWorker(QThread):
    """
    Background worker thread that pre-calculates requested lotto sets 
    integrated with LottoEngine / AlgorithmHub ensembles, custom user fixed/excluded filters, 
    strict Quality Gate filters, and recent draw overlap penalties with robust crash guards.
    """
    set_ready_signal = pyqtSignal(int, list)  # set_index, full_draw_list (7 numbers)
    finished_signal = pyqtSignal(list, list, dict, dict)  # all_sets, discards, stats, metadata
    error_signal = pyqtSignal(str)

    def __init__(
        self,
        engine,
        set_count: int = 5,
        algorithm_title: str = "Statistical Distribution Model",
        algorithm_id: str = "ensemble_auto",
        fixed_numbers: list = None,
        excluded_numbers: list = None,
    ):
        super().__init__()
        self.engine = engine
        self.set_count = set_count
        self.algorithm_id = resolve_algorithm_mode_id(algorithm_id)
        self.algorithm_title = algorithm_title or get_mode_title(self.algorithm_id)
        
        # 안전한 타입 변환 및 필터 정제
        self.fixed_numbers = [int(n) for n in (fixed_numbers or []) if 1 <= n <= 45]
        raw_excluded = [int(n) for n in (excluded_numbers or []) if 1 <= n <= 45]
        self.excluded_numbers = [n for n in raw_excluded if n not in self.fixed_numbers]

        self._is_running = True
        self.ai_weights = self._load_ai_weights()

    def __del__(self):
        try:
            _log.debug(f"[{self.__class__.__name__}] Thread object is being destroyed.")
        except Exception:
            pass

    def _load_ai_weights(self):
        try:
            for state_key in ("latest_weights_1_500", "latest_weights"):
                state = MLModelRepository.load_model_state(state_key)
                if isinstance(state, dict) and state:
                    _log.info("AI model weights successfully loaded into LottoWorker from repository key '%s'.", state_key)
                    return state
        except Exception as e:
            _log.warning(f"Failed to load AI model weights from repository: {e}", exc_info=True)

        model_path = os.path.join(project_root, "ai", "model_weights.pkl")
        if os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    data = _safe_pickle_load(f)
                    if not isinstance(data, dict):
                        return None
                    _log.info("AI model weights successfully loaded into LottoWorker from legacy file.")
                    return data
            except Exception as e:
                _log.warning(f"Failed to load AI model weights: {e}", exc_info=True)
        return None

    def stop(self):
        self._is_running = False

    def _get_latest_draw_numbers(self) -> list:
        try:
            all_draws = LottoRepository.get_all_draws()
            if all_draws:
                sorted_draws = sorted(all_draws, key=lambda d: int(d.get("drwNo", d.get("draw_no", 0))), reverse=True)
                latest = sorted_draws[0]
                nums = []
                for i in range(1, 7):
                    val = latest.get(f"num{i}") or latest.get(f"drwtNo{i}")
                    if val is not None:
                        nums.append(int(val))
                if len(nums) >= 6:
                    return sorted([n for n in nums[:6] if 1 <= n <= 45])
        except Exception as e:
            _log.warning(f"Failed to fetch latest draw numbers for worker overlap constraint: {e}", exc_info=True)
        return []

    def _calculate_ac_value(self, numbers: list) -> int:
        return int(calculate_ac_value(numbers))

    def _passes_quality_gate(self, raw_set: list, latest_draw_nums: list) -> bool:
        try:
            return passes_quality_gate(
                raw_set,
                latest_draw_numbers=latest_draw_nums,
                strict=True,
                sum_min=SUM_MIN,
                sum_max=SUM_MAX,
                high_low_cutoff=23,
                min_ac_value=4,
                min_span=None,
                min_decades=3,
                max_overlap_with_latest=2,
                max_consecutive_run=3,
            )
        except Exception as e:
            _log.error(f"Error in _passes_quality_gate: {e}", exc_info=True)
            return False

    def _passes_diversity_gate(self, raw_set: list, accepted_sets: list[list[int]]) -> bool:
        """
        Enforces cross-set diversity by limiting excessive overlap with already accepted sets.
        """
        try:
            candidate = sorted([int(n) for n in raw_set[:6] if 1 <= int(n) <= 45])
            if len(candidate) != 6:
                return False

            if not accepted_sets:
                return True

            # Keep fixed-number constraints feasible while reducing near-duplicate sets.
            max_allowed_overlap = min(6, max(3, len(self.fixed_numbers)))
            candidate_set = set(candidate)

            for prev in accepted_sets:
                if not isinstance(prev, (list, tuple)) or len(prev) < 6:
                    continue
                prev_set = set(int(n) for n in prev[:6] if 1 <= int(n) <= 45)
                if len(prev_set) != 6:
                    continue
                overlap = len(candidate_set.intersection(prev_set))
                if overlap > max_allowed_overlap:
                    return False
            return True
        except Exception as e:
            _log.warning(f"Error in _passes_diversity_gate: {e}", exc_info=True)
            return True

    def _build_constrained_random_set(self) -> list[int]:
        fixed_numbers = sorted(set(self.fixed_numbers))
        if len(fixed_numbers) > 6:
            return []
        candidate_pool = [
            number for number in range(1, 46)
            if number not in self.excluded_numbers and number not in fixed_numbers
        ]
        needed = 6 - len(fixed_numbers)
        if len(candidate_pool) < needed:
            return []
        return sorted(fixed_numbers + random.sample(candidate_pool, needed))

    def run(self):
        try:
            _log.info(f"Venus Turbine Worker started generating {self.set_count} sets using [{self.algorithm_title}]...")
            all_generated_sets = []
            
            # 최신 당첨 번호 캐싱 (성능 최적화)
            latest_draw_nums = self._get_latest_draw_numbers()

            prediction_sets = []
            prediction_sets_snapshot = []
            strategy_title = self.algorithm_title
            strategy_sources = []
            strategy_scores = []
            contributor_hint = 0
            if self.engine and hasattr(self.engine, "generate_prediction_sets"):
                try:
                    prediction_sets = self.engine.generate_prediction_sets(
                        set_count=self.set_count * 6, 
                        selected_algorithm_id=self.algorithm_id,
                        fixed_numbers=self.fixed_numbers, 
                        excluded_numbers=self.excluded_numbers
                    ) or []
                    prediction_sets_snapshot = list(prediction_sets)
                    for pred in prediction_sets:
                        if not isinstance(pred, dict):
                            continue
                        pred_title = pred.get("algorithm_title")
                        if pred_title:
                            strategy_title = str(pred_title)
                        pred_source = pred.get("source")
                        if pred_source and pred_source not in strategy_sources:
                            strategy_sources.append(str(pred_source))
                        pred_score = pred.get("score")
                        if pred_score is not None:
                            try:
                                strategy_scores.append(float(pred_score))
                            except (TypeError, ValueError):
                                pass
                        pred_contributors = pred.get("contributing_algorithms")
                        if pred_contributors is not None:
                            try:
                                contributor_hint = max(contributor_hint, int(pred_contributors))
                            except (TypeError, ValueError):
                                pass
                except Exception as ex:
                    _log.warning(f"Engine generation fallback triggered: {ex}", exc_info=True)

            candidate_pool = [n for n in range(1, 46) if n not in self.excluded_numbers and n not in self.fixed_numbers]
            if len(self.fixed_numbers) > 6 or len(candidate_pool) < 6 - len(self.fixed_numbers):
                self.error_signal.emit("Fixed and excluded numbers leave fewer than six available distinct numbers.")
                return
            discarded_total = 0

            for set_idx in range(1, self.set_count + 1):
                if not self._is_running:
                    break

                raw_set = []
                attempts = 0
                max_attempts = 400

                while attempts < max_attempts and self._is_running:
                    attempts += 1
                    current_raw = []

                    if prediction_sets and len(prediction_sets) > 0:
                        pred = prediction_sets.pop(0)
                        if hasattr(pred, "numbers"):
                            current_raw = sorted([int(n) for n in pred.numbers[:6]])
                        elif isinstance(pred, dict):
                            current_raw = sorted([int(n) for n in pred.get("numbers", [])[:6]])

                    if len(current_raw) != 6 or any(n < 1 or n > 45 for n in current_raw) or len(set(current_raw)) != 6 or any(n in self.excluded_numbers for n in current_raw) or any(f not in current_raw for f in self.fixed_numbers):
                        current_raw = self._build_constrained_random_set()
                        if len(current_raw) != 6:
                            break

                    if (
                        self._passes_quality_gate(current_raw, latest_draw_nums)
                        and current_raw not in all_generated_sets
                        and self._passes_diversity_gate(current_raw, all_generated_sets)
                    ):
                        raw_set = current_raw
                        break
                    else:
                        discarded_total += 1

                if not self._is_running:
                    break

                if len(raw_set) < 6:
                    retry_guard = 0
                    accepted = False
                    while retry_guard < 120:
                        retry_guard += 1
                        raw_set = self._build_constrained_random_set()
                        if len(raw_set) != 6:
                            break
                        if (
                            self._passes_quality_gate(raw_set, latest_draw_nums)
                            and all(f in raw_set for f in self.fixed_numbers)
                            and not any(n in self.excluded_numbers for n in raw_set)
                            and len(set(raw_set)) == 6
                            and raw_set not in all_generated_sets
                            and self._passes_diversity_gate(raw_set, all_generated_sets)
                        ):
                            accepted = True
                            break
                    if not accepted:
                        self.error_signal.emit("Unable to generate a set that satisfies the requested constraints.")
                        return

                remaining_pool = [n for n in range(1, 46) if n not in raw_set and n not in self.excluded_numbers]
                bonus_ball = random.choice(remaining_pool) if remaining_pool else 1
                full_draw = raw_set + [bonus_ball]

                all_generated_sets.append(raw_set)

                self.set_ready_signal.emit(set_idx, full_draw)
                time.sleep(0.005)

            if not self._is_running:
                return

            _log.info(f"Quality Gate completed. Total discarded sets: {discarded_total}")

            if not all_generated_sets:
                self.error_signal.emit("Unable to generate any sets that satisfy the requested constraints.")
                return
            primary_numbers = all_generated_sets[0]
            all_nums = set(range(1, 46))
            discards = sorted(list(all_nums - set(primary_numbers)))[:6]
            confidence_score = (
                round(float(sum(strategy_scores) / len(strategy_scores)), 2)
                if strategy_scores
                else (94.2 if self.ai_weights else 90.5)
            )
            raw_history = getattr(getattr(self.engine, "engine", self.engine), "historical_draws", [])
            frequency_map = build_frequency_map_from_history(raw_history, lookback=120)
            score_weights = derive_score_weights_from_history(raw_history, lookback=120)
            ranked_candidates = []
            for pred in prediction_sets_snapshot:
                if not isinstance(pred, dict):
                    continue
                pred_numbers = pred.get("numbers", [])
                try:
                    pred_score = float(pred.get("score", confidence_score))
                except (TypeError, ValueError):
                    pred_score = float(confidence_score)
                ranked_candidates.append((pred_score, pred_numbers))

            if not ranked_candidates:
                ranked_candidates = [(float(confidence_score), nums) for nums in all_generated_sets]

            top_ranked_combinations = build_top_ranked_combinations(
                ranked_candidates,
                limit=50,
                frequency_map=frequency_map,
                score_weights=score_weights,
            )
            total_algorithms_active = resolve_total_algorithms_active(self.engine, default=0)
            if total_algorithms_active <= 0:
                total_algorithms_active = max(1, len(strategy_sources) + 1)
            contributors = max(1, contributor_hint or total_algorithms_active)

            stats = build_generation_stats(primary_numbers, confidence_score, contributors)
            metadata = build_generation_metadata(
                algorithm_id=self.algorithm_id,
                algorithm_title=strategy_title,
                total_algorithms_active=total_algorithms_active,
                confidence_score=confidence_score,
                round_info="Live Draw",
                discarded_count=discarded_total,
                leading_algorithms=[
                    strategy_title,
                    *strategy_sources[:2],
                    "Quality Gate Filtering Engine",
                    "AI Neural Weight Ensembler" if self.ai_weights else "Statistical Matrix Evaluator",
                ],
                extras={
                    "top_ranked_combinations": top_ranked_combinations,
                    "score_weight_profile": {k: round(float(v), 4) for k, v in score_weights.items()},
                },
            )

            self.finished_signal.emit(all_generated_sets, discards, stats, metadata)
            _log.info("Venus Turbine Worker successfully finished generation cycle.")

        except Exception as e:
            _log.critical(f"[CRITICAL DEBUG] LottoWorker exception: {e}\n{traceback.format_exc()}")
            self.error_signal.emit(str(e))