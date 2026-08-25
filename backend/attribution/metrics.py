import polars as pl


def compute_metrics(journeys: pl.DataFrame) -> dict:
    total_users = journeys["user_id"].n_unique()
    total_touches = journeys["journey"].list.len().sum()

    converting = journeys.filter(pl.col("has_conversion"))
    non_converting = journeys.filter(~pl.col("has_conversion"))

    total_revenue = journeys["total_revenue"].sum()
    conversion_users = converting["user_id"].n_unique()
    non_conversion_users = non_converting["user_id"].n_unique()

    conversion_rate = (conversion_users / total_users * 100) if total_users > 0 else 0.0
    avg_revenue = (total_revenue / conversion_users) if conversion_users > 0 else 0.0

    touches_by_channel = {}
    if not journeys.is_empty():
        exploded = journeys.select("journey").explode("journey").rename({"journey": "channel"})
        counts = exploded.group_by("channel").len().sort("len", descending=True)
        touches_by_channel = dict(zip(counts["channel"].to_list(), counts["len"].to_list()))

    return {
        "total_users": total_users,
        "total_touches": total_touches,
        "conversion_users": conversion_users,
        "non_conversion_users": non_conversion_users,
        "conversion_rate": conversion_rate,
        "avg_revenue_per_converting_user": avg_revenue,
        "total_revenue": total_revenue,
        "touches_by_channel": touches_by_channel,
    }
