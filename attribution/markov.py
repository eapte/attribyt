import polars as pl
from collections import defaultdict

def markov_attribution(journeys: pl.DataFrame, total_revenue: float) -> dict:
    channels = set()
    for chain in journeys['journey'].to_list():
        channels.update(chain)
    channels = list(channels)
    
    total_paths = len(journeys)
    base_conv = 1.0
    contributions = {}
    
    for ch in channels:
        paths_without = sum(1 for chain in journeys['journey'].to_list() if ch not in chain)
        removal_prob = paths_without / total_paths
        contributions[ch] = (base_conv - removal_prob) / base_conv
    
    total = sum(contributions.values())
    if total > 0:
        for ch in contributions:
            contributions[ch] /= total
    
    for ch in contributions:
        contributions[ch] *= total_revenue
    
    return contributions

def calculate_last_click(journeys: pl.DataFrame, total_revenue: float) -> dict:
    last_clicks = {}
    for journey in journeys['journey'].to_list():
        if journey:
            last = journey[-1]
            last_clicks[last] = last_clicks.get(last, 0) + 1
    total_paths = len(journeys)
    for ch in last_clicks:
        last_clicks[ch] = (last_clicks[ch] / total_paths) * total_revenue
    return last_clicks