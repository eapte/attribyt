import random
from collections import defaultdict
import polars as pl

START = "START"
CONVERSION = "CONVERSION"
NULL = "NULL"


def build_transition_graph(paths: list, outcomes: list) -> dict:
    """Build transition probabilities between channels, including
    virtual START, CONVERSION and NULL states."""
    counts = defaultdict(lambda: defaultdict(int))

    for path, converted in zip(paths, outcomes):
        if not path:
            continue
        chain = [START] + path + ([CONVERSION] if converted else [NULL])
        for i in range(len(chain) - 1):
            counts[chain[i]][chain[i + 1]] += 1

    probabilities = {}
    for src, targets in counts.items():
        total = sum(targets.values())
        probabilities[src] = {tgt: c / total for tgt, c in targets.items()}

    return probabilities


def _simulate_conversion_rate(graph: dict, n_simulations: int, excluded_channel: str, rng: random.Random) -> float:
    """Monte Carlo random walk over the transition graph. If
    excluded_channel is set, any transition into it is redirected to
    NULL, simulating that channel's removal from all journeys."""
    conversions = 0
    for _ in range(n_simulations):
        state = START
        for _ in range(100):  # safety cap against pathological cycles
            targets = graph.get(state)
            if not targets:
                break
            next_state = rng.choices(list(targets.keys()), weights=list(targets.values()))[0]
            if next_state == excluded_channel:
                next_state = NULL
            state = next_state
            if state in (CONVERSION, NULL):
                break
        if state == CONVERSION:
            conversions += 1
    return conversions / n_simulations if n_simulations else 0.0


def markov_attribution(journeys: pl.DataFrame, total_revenue: float,
                        n_simulations: int = 20000, seed: int = 42) -> dict:
    """Removal-effect attribution via Monte Carlo simulation on the
    channel transition graph (a practical alternative to solving the
    absorbing Markov chain analytically)."""
    if journeys.is_empty():
        return {}

    paths = journeys["journey"].to_list()
    outcomes = journeys["has_conversion"].to_list()

    all_channels = set()
    for path in paths:
        all_channels.update(path)

    if not all_channels:
        return {}

    rng = random.Random(seed)
    graph = build_transition_graph(paths, outcomes)
    base_rate = _simulate_conversion_rate(graph, n_simulations, excluded_channel=None, rng=rng)

    if base_rate <= 0:
        return {ch: 0.0 for ch in all_channels}

    removal_effects = {}
    for channel in all_channels:
        rate_without = _simulate_conversion_rate(graph, n_simulations, excluded_channel=channel, rng=rng)
        effect = (base_rate - rate_without) / base_rate
        removal_effects[channel] = max(effect, 0.0)

    total_effect = sum(removal_effects.values())
    if total_effect > 0:
        for channel in removal_effects:
            removal_effects[channel] = (removal_effects[channel] / total_effect) * total_revenue

    return removal_effects


def calculate_last_click(journeys: pl.DataFrame, total_revenue: float) -> dict:
    last_clicks = defaultdict(float)
    total_paths = len(journeys)
    if total_paths == 0:
        return {}

    for path in journeys["journey"].to_list():
        if path:
            last_clicks[path[-1]] += 1.0

    for ch in last_clicks:
        last_clicks[ch] = (last_clicks[ch] / total_paths) * total_revenue

    return dict(last_clicks)


def calculate_linear(journeys: pl.DataFrame, total_revenue: float) -> dict:
    touches = defaultdict(float)
    total_paths = len(journeys)
    if total_paths == 0:
        return {}

    for path in journeys["journey"].to_list():
        if path:
            share = 1.0 / len(path)
            for ch in path:
                touches[ch] += share

    for ch in touches:
        touches[ch] = (touches[ch] / total_paths) * total_revenue

    return dict(touches)


def calculate_time_decay(journeys: pl.DataFrame, total_revenue: float, decay: float = 0.5) -> dict:
    touches = defaultdict(float)
    total_paths = len(journeys)
    if total_paths == 0:
        return {}

    for path in journeys["journey"].to_list():
        if not path:
            continue
        n = len(path)
        weights = [decay ** (n - i - 1) for i in range(n)]
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        for ch, w in zip(path, weights):
            touches[ch] += w

    for ch in touches:
        touches[ch] = (touches[ch] / total_paths) * total_revenue

    return dict(touches)
