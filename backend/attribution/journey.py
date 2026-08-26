import polars as pl

JOURNEY_SCHEMA = {
    "user_id": pl.Utf8,
    "journey": pl.List(pl.Utf8),
    "total_revenue": pl.Float64,
    "has_conversion": pl.Boolean,
}


def build_journeys(df: pl.DataFrame) -> pl.DataFrame:
    """
    Build one journey per conversion event, plus one trailing journey for
    unconverted touches.

    Every row is counted as its own touchpoint, including the row that
    carries the conversion (revenue > 0) — this matches the convention
    used by GA and most multi-touch attribution tools, where each
    tracked event is a distinct interaction, even if a purchase event
    happens to carry the same channel tag as the click right before it.

    Touches are consumed once a conversion happens, so a user's second
    purchase does not re-include touches already credited to their
    first purchase.
    """
    if df.is_empty():
        return pl.DataFrame(schema=JOURNEY_SCHEMA)

    df_sorted = df.sort(["user_id", "timestamp"])
    journeys = []

    for user_id, user_data in df_sorted.group_by("user_id", maintain_order=True):
        uid = user_id[0] if isinstance(user_id, tuple) else user_id
        current_path = []

        for row in user_data.iter_rows(named=True):
            revenue = row.get("revenue") or 0.0
            current_path.append(row["channel"])

            if revenue > 0:
                journeys.append({
                    "user_id": uid,
                    "journey": current_path.copy(),
                    "total_revenue": float(revenue),
                    "has_conversion": True,
                })
                current_path = []

        # leftover touches with no conversion after them
        if current_path:
            journeys.append({
                "user_id": uid,
                "journey": current_path,
                "total_revenue": 0.0,
                "has_conversion": False,
            })

    if not journeys:
        return pl.DataFrame(schema=JOURNEY_SCHEMA)

    return pl.DataFrame(journeys, schema=JOURNEY_SCHEMA)
