# -*- coding: utf-8 -*-
# core/algorithms/group_ml_ai.py
import sys
import os
import logging
import pickle
import random
import numpy as np

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) if "algorithms" in current_dir else current_dir
if project_root not in sys.path:
    sys.path.insert(0, project_root)

_log = logging.getLogger("GroupMLAIAlgorithms")

from typing import List, Dict, Any
from data.repositories.lotto_repository import LottoRepository
from data.repositories.ml_model_repository import MLModelRepository
from core.algorithms.base import BaseAlgorithm, HistoricalContext, _normalize, register_algorithm

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.cluster import KMeans
    from sklearn.naive_bayes import GaussianNB
    from sklearn.neural_network import MLPRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    _log.warning("scikit-learn is not available. Algorithms will run in robust statistical fallback mode.")


def _extract_draw_numbers(draw: dict) -> List[int]:
    """Helper utility to extract and validate 6 numbers from a historical draw record safely."""
    nums = []
    for k in ["num1", "num2", "num3", "num4", "num5", "num6", "drwtNo1", "drwtNo2", "drwtNo3", "drwtNo4", "drwtNo5", "drwtNo6"]:
        val = draw.get(k)
        if val is not None:
            try:
                iv = int(val)
                if 1 <= iv <= 45:
                    nums.append(iv)
            except (ValueError, TypeError):
                pass
    return sorted(list(set(nums)))[:6]


# ==========================================
# 1. Machine Learning & Time-Series Functional Algorithms
# ==========================================

@register_algorithm("ml_001", "[ML] Random Forest Multi-Output Classification Analysis")
def generate_by_random_forest_ensemble() -> List[int]:
    """Trains a genuine scikit-learn RandomForestClassifier on historical draw sequence patterns."""
    try:
        all_draws = LottoRepository.get_all_draws()
        if not SKLEARN_AVAILABLE or not all_draws or len(all_draws) < 30:
            return sorted(random.sample(range(1, 46), 6))
            
        # Build feature matrix: past draw indicators -> next draw indicators
        X, y = [], []
        history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
        
        if len(history_sets) < 20:
            return sorted(random.sample(range(1, 46), 6))

        for i in range(len(history_sets) - 1):
            curr_vec = [1 if n in history_sets[i] else 0 for n in range(1, 46)]
            next_vec = [1 if n in history_sets[i+1] else 0 for n in range(1, 46)]
            X.append(curr_vec)
            y.append(next_vec)

        X_arr, y_arr = np.array(X, dtype=np.float64), np.array(y, dtype=np.float64)
        
        # Train RandomForest for each number or multi-label prediction
        rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        rf.fit(X_arr, y_arr)

        latest_vec = np.array([[1 if n in history_sets[-1] else 0 for n in range(1, 46)]], dtype=np.float64)
        probs = rf.predict_proba(latest_vec)
        
        # Extract appearance probabilities for each number (class 1 probability)
        number_probs = []
        for idx, p in enumerate(probs):
            if isinstance(p, np.ndarray) and p.shape[-1] > 1:
                number_probs.append(float(p[0, 1]))
            else:
                number_probs.append(0.5)

        candidate_pool = list(range(1, 46))
        weight_values = [max(0.01, wp) for wp in number_probs]
        total_w = sum(weight_values)
        
        if total_w > 0:
            final_probs = np.array(weight_values, dtype=np.float64)
            final_probs /= final_probs.sum()
            selected = np.random.choice(candidate_pool, size=6, replace=False, p=final_probs)
            return sorted([int(n) for n in selected])
    except Exception as e:
        _log.error(f"Error in generate_by_random_forest_ensemble (sklearn): {e}", exc_info=True)

    return sorted(random.sample(range(1, 46), 6))


@register_algorithm("ml_002", "[ML] K-Means Clustering on Number Feature Vectors")
def generate_by_kmeans_clustering() -> List[int]:
    """Applies scikit-learn KMeans clustering on multi-dimensional feature vectors of all 45 lotto numbers."""
    try:
        all_draws = LottoRepository.get_all_draws()
        if not SKLEARN_AVAILABLE or not all_draws or len(all_draws) < 20:
            return sorted(random.sample(range(1, 46), 6))
            
        history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
        total_draws_count = len(history_sets)

        # Build feature vector for each number (1 to 45): [Total Frequency, Recent Freq (last 20), Average Gap]
        features = []
        for num in range(1, 46):
            appearances = [idx for idx, s in enumerate(history_sets) if num in s]
            total_freq = len(appearances)
            recent_freq = sum(1 for idx in appearances if idx >= total_draws_count - 20)
            
            gaps = [appearances[i] - appearances[i-1] for i in range(1, len(appearances))] if len(appearances) > 1 else [total_draws_count]
            avg_gap = float(np.mean(gaps)) if gaps else float(total_draws_count)
            
            features.append([float(total_freq), float(recent_freq * 3.0), float(avg_gap)])

        X = np.array(features, dtype=np.float64)
        
        # Fit KMeans with 5 clusters
        kmeans = KMeans(n_clusters=min(5, len(X)), random_state=42, n_init=10)
        kmeans.fit(X)
        
        # Calculate cluster desirability based on distance to optimal features (high recent activity, moderate gap)
        center_scores = []
        for center in kmeans.cluster_centers_:
            score = center[1] - (center[2] * 0.1) # recent freq weight - gap penalty
            center_scores.append(score)
            
        best_cluster = int(np.argmax(center_scores))
        labels = kmeans.labels_
        
        weights = {}
        for idx, num in enumerate(range(1, 46)):
            if labels[idx] == best_cluster:
                weights[num] = 2.0
            else:
                weights[num] = 1.0

        candidate_pool = list(range(1, 46))
        weight_values = [max(0.01, weights[i]) for i in candidate_pool]
        total_w = sum(weight_values)
        
        if total_w > 0:
            probs = np.array([w / total_w for w in weight_values], dtype=np.float64)
            probs /= probs.sum()
            selected = np.random.choice(candidate_pool, size=6, replace=False, p=probs)
            return sorted([int(n) for n in selected])
    except Exception as e:
        _log.error(f"Error in generate_by_kmeans_clustering (sklearn): {e}", exc_info=True)

    return sorted(random.sample(range(1, 46), 6))


@register_algorithm("ml_003", "[ML] Naive Bayes Conditional Probability Classifier")
def generate_by_naive_bayes() -> List[int]:
    """Uses scikit-learn GaussianNB to classify and score numbers based on historical features."""
    try:
        all_draws = LottoRepository.get_all_draws()
        if not SKLEARN_AVAILABLE or not all_draws or len(all_draws) < 20:
            return sorted(random.sample(range(1, 46), 6))
            
        history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
        
        X, y = [], []
        for i in range(10, len(history_sets)):
            past_10 = history_sets[i-10:i]
            target_set = history_sets[i]
            
            # Features for each number at draw i: [frequency in past 10, was present in draw i-1]
            for num in range(1, 46):
                freq_10 = sum(1 for s in past_10 if num in s)
                was_in_prev = 1 if num in history_sets[i-1] else 0
                is_target = 1 if num in target_set else 0
                
                X.append([float(freq_10), float(was_in_prev)])
                y.append(int(is_target))

        X_arr, y_arr = np.array(X, dtype=np.float64), np.array(y, dtype=np.int64)
        
        gnb = GaussianNB()
        gnb.fit(X_arr, y_arr)

        latest_past_10 = history_sets[-10:] if len(history_sets) >= 10 else history_sets
        latest_draw = history_sets[-1]

        latest_features = []
        for num in range(1, 46):
            freq_10 = sum(1 for s in latest_past_10 if num in s)
            was_in_prev = 1 if num in latest_draw else 0
            latest_features.append([float(freq_10), float(was_in_prev)])

        preds_proba = gnb.predict_proba(np.array(latest_features, dtype=np.float64))
        
        weights = {}
        for idx, num in enumerate(range(1, 46)):
            weights[num] = float(preds_proba[idx, 1]) if preds_proba.shape[1] > 1 else 0.5

        candidate_pool = list(range(1, 46))
        weight_values = [max(0.01, weights[i]) for i in candidate_pool]
        total_w = sum(weight_values)
        
        if total_w > 0:
            probs = np.array([w / total_w for w in weight_values], dtype=np.float64)
            probs /= probs.sum()
            selected = np.random.choice(candidate_pool, size=6, replace=False, p=probs)
            return sorted([int(n) for n in selected])
    except Exception as e:
        _log.error(f"Error in generate_by_naive_bayes (sklearn): {e}", exc_info=True)

    return sorted(random.sample(range(1, 46), 6))


@register_algorithm("ml_004", "[ML] Hidden Markov Model State Transition Prediction (DB Cached)")
def generate_by_hidden_markov_model() -> List[int]:
    """Computes empirical Markov chain transition probability matrix with Laplace smoothing and DB caching."""
    try:
        all_draws = LottoRepository.get_all_draws()
        if not all_draws or len(all_draws) < 10:
            return sorted(random.sample(range(1, 46), 6))
            
        current_latest_draw = int(all_draws[-1].get("draw_no") or all_draws[-1].get("drwNo") or len(all_draws))
        model_key = "hmm_transition_matrix"
        
        cached_model = MLModelRepository.load_model_state(model_key)
        transition_matrix = None
        
        if cached_model and cached_model.get("trained_latest_draw") == current_latest_draw:
            try:
                transition_matrix = {int(k): {int(sub_k): float(sub_v) for sub_k, sub_v in v.items()} for k, v in cached_model["model_data"].items()}
            except Exception:
                transition_matrix = None

        if not transition_matrix:
            # Laplace smoothing initialization
            transition_matrix = {i: {j: 0.01 for j in range(1, 46)} for i in range(1, 46)}
            history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
            
            for i in range(len(history_sets) - 1):
                nums1 = history_sets[i]
                nums2 = history_sets[i+1]
                for n1 in nums1:
                    for n2 in nums2:
                        transition_matrix[n1][n2] += 1.0
            
            # Normalize rows
            for n1 in transition_matrix:
                row_sum = sum(transition_matrix[n1].values())
                if row_sum > 0:
                    for n2 in transition_matrix[n1]:
                        transition_matrix[n1][n2] /= row_sum

            try:
                MLModelRepository.save_model_state(model_key, "HiddenMarkovModel", transition_matrix, current_latest_draw)
            except Exception:
                pass

        latest_nums = _extract_draw_numbers(all_draws[-1]) if all_draws else []
        weights = {i: 1.0 for i in range(1, 46)}
        
        for n1 in latest_nums:
            if n1 in transition_matrix:
                for n2, prob in transition_matrix[n1].items():
                    weights[n2] += float(prob) * 2.5

        candidate_pool = list(range(1, 46))
        weight_values = [max(0.01, weights[i]) for i in candidate_pool]
        total_w = sum(weight_values)
        
        if total_w > 0:
            probs = np.array([w / total_w for w in weight_values], dtype=np.float64)
            probs /= probs.sum()
            selected = np.random.choice(candidate_pool, size=6, replace=False, p=probs)
            return sorted([int(n) for n in selected])
    except Exception as e:
        _log.error(f"Error in generate_by_hidden_markov_model: {e}", exc_info=True)

    return sorted(random.sample(range(1, 46), 6))


@register_algorithm("ml_ts_001", "[Time-Series ML] Gradient Boosting Regressor Trend Forecasting")
def generate_by_timeseries_momentum() -> List[int]:
    """Trains a scikit-learn GradientBoostingRegressor to forecast number selection probabilities based on time-series rolling momentum."""
    try:
        all_draws = LottoRepository.get_all_draws()
        if not SKLEARN_AVAILABLE or not all_draws or len(all_draws) < 30:
            return sorted(random.sample(range(1, 46), 6))
            
        history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
        
        X, y = [], []
        for i in range(10, len(history_sets) - 1):
            window = history_sets[i-10:i]
            target = history_sets[i+1]
            
            for num in range(1, 46):
                rolling_freq = sum(1 for s in window if num in s)
                momentum = rolling_freq - sum(1 for s in history_sets[i-20:i-10] if num in s) if i >= 20 else rolling_freq
                
                X.append([float(rolling_freq), float(momentum)])
                y.append(1.0 if num in target else 0.0)

        X_arr, y_arr = np.array(X, dtype=np.float64), np.array(y, dtype=np.float64)
        
        gbr = GradientBoostingRegressor(n_estimators=30, max_depth=3, random_state=42)
        gbr.fit(X_arr, y_arr)

        recent_window = history_sets[-10:]
        past_window = history_sets[-20:-10] if len(history_sets) >= 20 else history_sets[:10]

        latest_features = []
        for num in range(1, 46):
            rf = sum(1 for s in recent_window if num in s)
            mo = rf - sum(1 for s in past_window if num in s)
            latest_features.append([float(rf), float(mo)])

        predictions = gbr.predict(np.array(latest_features, dtype=np.float64))
        
        weights = {}
        min_p, max_p = np.min(predictions), np.max(predictions)
        diff_p = max_p - min_p if max_p > min_p else 1.0

        for idx, num in enumerate(range(1, 46)):
            norm_w = 0.1 + ((predictions[idx] - min_p) / diff_p) * 0.9
            weights[num] = float(norm_w)

        candidate_pool = list(range(1, 46))
        weight_values = [max(0.01, weights[i]) for i in candidate_pool]
        total_w = sum(weight_values)
        
        if total_w > 0:
            probs = np.array([w / total_w for w in weight_values], dtype=np.float64)
            probs /= probs.sum()
            selected = np.random.choice(candidate_pool, size=6, replace=False, p=probs)
            return sorted([int(n) for n in selected])
    except Exception as e:
        _log.error(f"Error in generate_by_timeseries_momentum (sklearn GBR): {e}", exc_info=True)

    return sorted(random.sample(range(1, 46), 6))


# ==========================================
# 2. AI & Deep Learning Functional Algorithms
# ==========================================

@register_algorithm("ALG-AI-01", "Machine Learning Weight-Based Smart Pattern Extraction")
def ai_smart_algorithm(db_data=None) -> List[int]:
    """Extracts numbers by reflecting knowledge if an AI brain (weight file) exists."""
    weight_file = "ai/model_weights.pkl"
    if os.path.exists(weight_file):
        try:
            with open(weight_file, "rb") as f:
                weights = pickle.load(f)
            preferred = weights.get("favorite_bias", [1, 2])
            preferred = [int(n) for n in preferred if 1 <= int(n) <= 45]
            remaining = [n for n in range(1, 46) if n not in preferred]
            
            if len(preferred) < 6:
                chosen = preferred + random.sample(remaining, 6 - len(preferred))
            else:
                chosen = random.sample(preferred, 6)
            return sorted([int(n) for n in chosen])
        except Exception as e:
            _log.warning(f"Failed to load AI model weights from {weight_file}: {e}")
            
    return sorted(random.sample(range(1, 46), 6))


@register_algorithm("dl_001", "[Deep Learning] MLP Neural Network Sequence Scoring")
def generate_by_lstm_sequence_memory() -> List[int]:
    """Trains a scikit-learn MLPRegressor (Multi-Layer Perceptron Neural Network) to score numbers based on sequence history."""
    try:
        all_draws = LottoRepository.get_all_draws()
        if not SKLEARN_AVAILABLE or not all_draws or len(all_draws) < 20:
            return sorted(random.sample(range(1, 46), 6))
            
        history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
        
        X, y = [], []
        for i in range(5, len(history_sets) - 1):
            window = history_sets[i-5:i]
            target = history_sets[i+1]
            
            for num in range(1, 46):
                # Simple sequence feature: number of appearances in past 5 draws and lag features
                feat = [sum(1 for s in window if num in s), 1.0 if num in history_sets[i] else 0.0]
                X.append(feat)
                y.append(1.0 if num in target else 0.0)

        X_arr, y_arr = np.array(X, dtype=np.float64), np.array(y, dtype=np.float64)
        
        mlp = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=100, random_state=42)
        mlp.fit(X_arr, y_arr)

        recent_5 = history_sets[-5:]
        latest_draw = history_sets[-1]

        latest_features = []
        for num in range(1, 46):
            latest_features.append([float(sum(1 for s in recent_5 if num in s)), 1.0 if num in latest_draw else 0.0])

        preds = mlp.predict(np.array(latest_features, dtype=np.float64))
        
        weights = {}
        min_p, max_p = np.min(preds), np.max(preds)
        diff_p = max_p - min_p if max_p > min_p else 1.0

        for idx, num in enumerate(range(1, 46)):
            weights[num] = float(max(0.01, 0.1 + ((preds[idx] - min_p) / diff_p) * 0.9))

        candidate_pool = list(range(1, 46))
        weight_values = [weights[i] for i in candidate_pool]
        total_w = sum(weight_values)
        
        if total_w > 0:
            probs = np.array([w / total_w for w in weight_values], dtype=np.float64)
            probs /= probs.sum()
            selected = np.random.choice(candidate_pool, size=6, replace=False, p=probs)
            return sorted([int(n) for n in selected])
    except Exception as e:
        _log.error(f"Error in generate_by_lstm_sequence_memory (MLP): {e}", exc_info=True)

    return sorted(random.sample(range(1, 46), 6))


@register_algorithm("dl_002", "[Deep Learning] Attention-Based Similarity Scoring")
def generate_by_transformer_self_attention() -> List[int]:
    """Computes self-attention-like dot product similarity scores across recent historical draw embedding vectors."""
    try:
        all_draws = LottoRepository.get_all_draws()
        if not all_draws or len(all_draws) < 10:
            return sorted(random.sample(range(1, 46), 6))
            
        history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
        recent_draws = history_sets[-10:]
        
        # Construct 45-dim binary vectors for recent draws
        vectors = np.array([[1 if n in d else 0 for n in range(1, 46)] for d in recent_draws], dtype=np.float64)
        
        # Self-Attention scoring: Q = K = V = vectors
        # Attention weights = softmax(Q @ K.T / sqrt(d))
        d_k = float(vectors.shape[1])
        scores = np.matmul(vectors, vectors.T) / np.sqrt(d_k)
        
        # Softmax normalization across attention matrix
        exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attn_weights = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)
        
        # Aggregate attention-weighted number scores
        weighted_vector = np.matmul(attn_weights, vectors)
        final_scores = np.sum(weighted_vector, axis=0)

        weights = {num: float(final_scores[num-1] + 0.1) for num in range(1, 46)}

        candidate_pool = list(range(1, 46))
        weight_values = [max(0.01, weights[i]) for i in candidate_pool]
        total_w = sum(weight_values)
        
        if total_w > 0:
            probs = np.array([w / total_w for w in weight_values], dtype=np.float64)
            probs /= probs.sum()
            selected = np.random.choice(candidate_pool, size=6, replace=False, p=probs)
            return sorted([int(n) for n in selected])
    except Exception as e:
        _log.error(f"Error in generate_by_transformer_self_attention: {e}", exc_info=True)

    return sorted(random.sample(range(1, 46), 6))


@register_algorithm("dl_003", "[Deep Learning] Reinforcement Learning Q-Learning Reward Optimization")
def generate_by_reinforcement_q_learning() -> List[int]:
    """Executes true Q-learning updates based on reward-penalty feedback from recent draws."""
    try:
        all_draws = LottoRepository.get_all_draws()
        if not all_draws:
            return sorted(random.sample(range(1, 46), 6))
            
        q_table = {i: 10.0 for i in range(1, 46)}
        learning_rate = 0.15
        discount_factor = 0.9
        
        history_sets = [_extract_draw_numbers(d) for d in all_draws if len(_extract_draw_numbers(d)) == 6]
        target_slice = history_sets[-30:] if len(history_sets) >= 30 else history_sets
        
        for draw_set in target_slice:
            winning_nums = set(draw_set)
            max_q_val = max(q_table.values()) if q_table else 0.0

            for n in range(1, 46):
                reward = 5.0 if n in winning_nums else -0.2
                q_table[n] = float(q_table[n] + learning_rate * (reward + discount_factor * max_q_val - q_table[n]))
                
        min_val = min(q_table.values()) if q_table else 0.0
        weights = {n: max(0.1, float(val - min_val + 1.0)) for n, val in q_table.items()}

        candidate_pool = list(range(1, 46))
        weight_values = [max(0.01, weights[i]) for i in candidate_pool]
        total_w = sum(weight_values)
        
        if total_w > 0:
            probs = np.array([w / total_w for w in weight_values], dtype=np.float64)
            probs /= probs.sum()
            selected = np.random.choice(candidate_pool, size=6, replace=False, p=probs)
            return sorted([int(n) for n in selected])
    except Exception as e:
        _log.error(f"Error in generate_by_reinforcement_q_learning: {e}", exc_info=True)

    return sorted(random.sample(range(1, 46), 6))


# ==========================================
# 3. Class-based Unified ML/AI Algorithms
# ==========================================

class UnifiedMLAIAlgorithm(BaseAlgorithm):
    def __init__(self, sub_index: int):
        global_idx = sub_index + 101
        name = f"ALG-{global_idx:03d} | Unified_ML_AI_Model_{sub_index+1:02d}"
        super().__init__(name, "CAT-03", sub_index)

    def compute_weights(self, context: HistoricalContext, rng: np.random.Generator) -> np.ndarray:
        """
        Computes unified ML/AI weights combining transition strengths, pair centralities, 
        hotness scores, and machine learning propagation scores from HistoricalContext.
        """
        base_weights = context.transition_strength + context.pair_centrality + context.hotness
        ml_boost = context.db_freq_weight if context.db_freq_weight is not None else np.ones(45, dtype=np.float64)
        return _normalize(0.8 * base_weights + 0.2 * ml_boost)


def register_group_ml(registry):
    """Register unified ML and AI group algorithms."""
    _log.info("Registering Unified ML & AI group algorithms...")
    for i in range(90):
        algorithm_instance = UnifiedMLAIAlgorithm(i)
        if hasattr(registry, "register"):
            registry.register(algorithm_instance)
    _log.info("Unified ML & AI group algorithms registered successfully.")

def register_group_ai(registry):
    register_group_ml(registry)