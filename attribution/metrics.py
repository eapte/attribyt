import polars as pl

def compute_metrics(journeys: pl.DataFrame) -> dict:
    total_users = len(journeys)
    total_touches = journeys["journey"].list.len().sum()
    total_revenue = journeys["total_revenue"].sum()
    avg_revenue = total_revenue / total_users if total_users else 0

    exploded = journeys.explode("journey")
    touches_by_channel = exploded.group_by("journey").len().to_dict(as_series=False)
    
    return {
        "total_users": total_users,
        "total_touches": total_touches,
        "avg_revenue_per_user": avg_revenue,
        "total_revenue": total_revenue,
        "touches_by_channel": touches_by_channel
    }