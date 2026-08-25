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

    The row that carries the conversion (revenue > 0) is treated as the
    *outcome* of the journey, not an extra touchpoint — its channel is
    already implied by being the point of conversion, so counting it
    again as a separate touch would double-credit the last channel
    (this matters for datasets where the purchase event itself is
    tagged with a traffic_source, same as every click event).

    If no click preceded the conversion in a given segment (the very
    first event for a user is already a purchase), the conversion's own
    channel is used as the sole touchpoint — there's nothing else to
    attribute the revenue to.

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

            if revenue > 0:
                if not current_path:
                    # no prior click in this segment — attribute to the
                    # conversion's own channel, there's no alternative
                    current_path.append(row["channel"])
                journeys.append({
                    "user_id": uid,
                    "journey": current_path.copy(),
                    "total_revenue": float(revenue),
                    "has_conversion": True,
                })
                current_path = []
            else:
                current_path.append(row["channel"])

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
