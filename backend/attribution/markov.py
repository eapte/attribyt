import numpy as np
from collections import defaultdict
import polars as pl

START = "START"
CONVERSION = "CONVERSION"
NULL = "NULL"


def build_transition_counts(paths: list, outcomes: list) -> dict:
    counts = defaultdict(lambda: defaultdict(int))
    for path, converted in zip(paths, outcomes):
        if not path:
            continue
        chain = [START] + path + ([CONVERSION] if converted else [NULL])
        for i in range(len(chain) - 1):
            counts[chain[i]][chain[i + 1]] += 1
    return counts


def _conversion_probability(counts: dict, excluded_channel: str = None) -> float:
    """
    Exact absorption probability of reaching CONVERSION from START,
    via the fundamental matrix of the absorbing Markov chain:
    N = (I - Q)^-1, B = N @ R.
    """
    transient = {START}
    for src, targets in counts.items():
        if src not in (CONVERSION, NULL) and src != excluded_channel:
            transient.add(src)
        for tgt in targets:
            if tgt not in (CONVERSION, NULL) and tgt != excluded_channel:
                transient.add(tgt)

    transient = [START] + sorted(s for s in transient if s != START)
    index = {s: i for i, s in enumerate(transient)}
    n = len(transient)

    Q = np.zeros((n, n))
    R = np.zeros((n, 2))  # columns: [CONVERSION, NULL]

    for src in transient:
        targets = counts.get(src, {})
        total = sum(targets.values())
        if total == 0:
            continue
        for tgt, c in targets.items():
            p = c / total
            if tgt == excluded_channel:
                tgt = NULL
            if tgt == CONVERSION:
                R[index[src], 0] += p
            elif tgt == NULL:
                R[index[src], 1] += p
            elif tgt in index:
                Q[index[src], index[tgt]] += p

    try:
        N = np.linalg.inv(np.eye(n) - Q)
    except np.linalg.LinAlgError:
        return 0.0

    B = N @ R
    return float(B[index[START], 0])


def markov_attribution(journeys: pl.DataFrame, total_revenue: float,
                        n_simulations: int = 20000, seed: int = 42) -> dict:
    """
    Removal-effect attribution via exact absorbing-Markov-chain algebra.
    n_simulations/seed kept for backward compatibility, no longer used.
    """
    if journeys.is_empty():
        return {}

    paths = journeys["journey"].to_list()
    outcomes = journeys["has_conversion"].to_list()

    all_channels = set()
    for path in paths:
        all_channels.update(path)
    if not all_channels:
        return {}

    counts = build_transition_counts(paths, outcomes)
    base_rate = _conversion_probability(counts)

    if base_rate <= 0:
        return {ch: 0.0 for ch in all_channels}

    removal_effects = {}
    for channel in all_channels:
        rate_without = _conversion_probability(counts, excluded_channel=channel)
        effect = (base_rate - rate_without) / base_rate
        removal_effects[channel] = max(effect, 0.0)

    total_effect = sum(removal_effects.values())
    if total_effect > 0:
        for channel in removal_effects:
            removal_effects[channel] = (removal_effects[channel] / total_effect) * total_revenue
    else:
        removal_effects = {ch: 0.0 for ch in removal_effects}

    return removal_effects


def calculate_last_click(journeys: pl.DataFrame, total_revenue: float) -> dict:
    """Credits each conversion's own revenue to its last touchpoint —
    not an equal share of the average order value."""
    converting = journeys.filter(pl.col("has_conversion"))
    last_clicks = defaultdict(float)
    if len(converting) == 0:
        return {}

    for row in converting.iter_rows(named=True):
        path = row["journey"]
        if path:
            last_clicks[path[-1]] += row["total_revenue"]

    return dict(last_clicks)


def calculate_linear(journeys: pl.DataFrame, total_revenue: float) -> dict:
    """Splits each conversion's own revenue evenly across its touches —
    not an equal share of the average order value."""
    converting = journeys.filter(pl.col("has_conversion"))
    touches = defaultdict(float)
    if len(converting) == 0:
        return {}

    for row in converting.iter_rows(named=True):
        path = row["journey"]
        revenue = row["total_revenue"]
        if path:
            share = revenue / len(path)
            for ch in path:
                touches[ch] += share

    return dict(touches)


def calculate_time_decay(journeys: pl.DataFrame, total_revenue: float, decay: float = 0.5) -> dict:
    """Weights each conversion's own revenue toward its most recent
    touches — not an equal share of the average order value."""
    converting = journeys.filter(pl.col("has_conversion"))
    touches = defaultdict(float)
    if len(converting) == 0:
        return {}

    for row in converting.iter_rows(named=True):
        path = row["journey"]
        revenue = row["total_revenue"]
        if not path:
            continue
        n = len(path)
        weights = [decay ** (n - i - 1) for i in range(n)]
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        for ch, w in zip(path, weights):
            touches[ch] += w * revenue

    return dict(touches) 
