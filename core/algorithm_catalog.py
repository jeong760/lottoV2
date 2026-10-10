"""Shared algorithm mode catalog used by UI, controller, and engine routing."""

from dataclasses import dataclass
from typing import Dict, List, Tuple
from collections.abc import Iterable


@dataclass(frozen=True)
class AlgorithmMode:
    mode_id: str
    title: str
    strategy_key: str
    aliases: tuple[str, ...] = ()


ALGORITHM_MODES: tuple[AlgorithmMode, ...] = (
    AlgorithmMode(
        mode_id="ensemble_auto",
        title="Advanced AI Ensemble",
        strategy_key="hybrid",
        aliases=("auto", "advanced ai ensemble"),
    ),
    AlgorithmMode(
        mode_id="statistics_distribution",
        title="Statistical Distribution Model",
        strategy_key="statistics",
        aliases=("hot/cold statistical balancing",),
    ),
    AlgorithmMode(
        mode_id="frequency_matrix",
        title="Frequency Matrix Analyzer",
        strategy_key="frequency",
    ),
    AlgorithmMode(
        mode_id="ml_gradient",
        title="Machine Learning Gradient Engine",
        strategy_key="ml_ai",
    ),
    AlgorithmMode(
        mode_id="ai_neural",
        title="AI Neural Predictor",
        strategy_key="ai_neural",
        aliases=("deep learning lstm trend predictor",),
    ),
    AlgorithmMode(
        mode_id="historical_pattern",
        title="Historical Pattern Matcher",
        strategy_key="pattern",
    ),
    AlgorithmMode(
        mode_id="advanced_markov",
        title="Advanced Markov Chain Ensemble",
        strategy_key="advanced",
        aliases=("markov chain & monte carlo hybrid (recommended)", "markov chain & monte carlo hybrid"),
    ),
    AlgorithmMode(
        mode_id="pure_random",
        title="Pure Random Physics Simulation",
        strategy_key="random",
    ),
)


DEFAULT_ALGORITHM_MODE_ID = "ensemble_auto"

ALGORITHM_MODE_BY_ID: dict[str, AlgorithmMode] = {mode.mode_id: mode for mode in ALGORITHM_MODES}

_ALIAS_TO_MODE_ID: dict[str, str] = {}
for mode in ALGORITHM_MODES:
    for token in (mode.mode_id, mode.title, *mode.aliases):
        _ALIAS_TO_MODE_ID[token.strip().lower()] = mode.mode_id


def resolve_algorithm_mode_id(raw_value: str | None) -> str:
    if raw_value is None:
        return DEFAULT_ALGORITHM_MODE_ID

    normalized = str(raw_value).strip().lower()
    if not normalized:
        return DEFAULT_ALGORITHM_MODE_ID

    return _ALIAS_TO_MODE_ID.get(normalized, DEFAULT_ALGORITHM_MODE_ID)


def get_mode_title(mode_id: str | None) -> str:
    resolved = resolve_algorithm_mode_id(mode_id)
    mode = ALGORITHM_MODE_BY_ID.get(resolved)
    return mode.title if mode else ALGORITHM_MODE_BY_ID[DEFAULT_ALGORITHM_MODE_ID].title


def get_mode_strategy(mode_id: str | None) -> str:
    resolved = resolve_algorithm_mode_id(mode_id)
    mode = ALGORITHM_MODE_BY_ID.get(resolved)
    return mode.strategy_key if mode else ALGORITHM_MODE_BY_ID[DEFAULT_ALGORITHM_MODE_ID].strategy_key


def get_mode_options(include_random: bool = False) -> list[AlgorithmMode]:
    if include_random:
        return list(ALGORITHM_MODES)
    return [mode for mode in ALGORITHM_MODES if mode.mode_id != "pure_random"]


def get_mode_titles(include_random: bool = False) -> list[str]:
    return [mode.title for mode in get_mode_options(include_random=include_random)]


def get_runtime_selectable_mode_ids(include_random: bool = False) -> list[str]:
    return [mode.mode_id for mode in get_mode_options(include_random=include_random) if mode.mode_id != DEFAULT_ALGORITHM_MODE_ID]


def iter_modes() -> Iterable[AlgorithmMode]:
    return iter(ALGORITHM_MODES)
