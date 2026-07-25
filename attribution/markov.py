import polars as pl
from collections import defaultdict


def build_transition_matrix(paths: list) -> dict:
    matrix = defaultdict(lambda: defaultdict(float))
    start_counts = defaultdict(int)
    conv_counts = defaultdict(int)
    
    for path in paths:
        if not path:
            continue
        
        start_counts[path[0]] += 1
        
        for i in range(len(path) - 1):
            matrix[path[i]][path[i + 1]] += 1
        
        conv_counts[path[-1]] += 1
    
    for src in matrix:
        total = sum(matrix[src].values())
        if total > 0:
            for tgt in matrix[src]:
                matrix[src][tgt] /= total
    
    total_starts = sum(start_counts.values())
    for ch in start_counts:
        start_counts[ch] /= total_starts
    
    for ch in conv_counts:
        total_visits = len([p for p in paths if ch in p])
        conv_counts[ch] = conv_counts[ch] / total_visits if total_visits > 0 else 0
    
    return {
        "transitions": dict(matrix),
        "starts": dict(start_counts),
        "conversions": dict(conv_counts)
    }


def markov_attribution(journeys: pl.DataFrame, total_revenue: float) -> dict:
    all_paths = journeys['journey'].to_list()
    
    all_channels = set()
    for path in all_paths:
        all_channels.update(path)
    all_channels = list(all_channels)
    
    if not all_channels or not all_paths:
        return {}
    
    contributions = {}
    base_conv_prob = len([p for p in all_paths if p]) / len(all_paths) if all_paths else 0
    
    for channel in all_channels:
        paths_without = []
        for path in all_paths:
            filtered = [c for c in path if c != channel]
            if filtered:
                paths_without.append(filtered)
        
        if not paths_without:
            conv_prob_without = 0
        else:
            conv_without = sum(1 for p in paths_without if p)
            conv_prob_without = conv_without / len(all_paths)
        
        removal_effect = (base_conv_prob - conv_prob_without) / base_conv_prob if base_conv_prob > 0 else 0
        
        if removal_effect < 0:
            removal_effect = 0
        
        contributions[channel] = removal_effect
    
    total_effect = sum(contributions.values())
    if total_effect > 0:
        for ch in contributions:
            contributions[ch] = (contributions[ch] / total_effect) * total_revenue
    
    return contributions


def calculate_last_click(journeys: pl.DataFrame, total_revenue: float) -> dict:
    last_clicks = defaultdict(float)
    total_paths = len(journeys)
    
    if total_paths == 0:
        return {}
    
    for path in journeys['journey'].to_list():
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
    
    for path in journeys['journey'].to_list():
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
    
    for path in journeys['journey'].to_list():
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