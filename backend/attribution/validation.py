import polars as pl


class ValidationResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def is_valid(self) -> bool:
        return not self.errors


REQUIRED_COLUMNS = ["user_id", "timestamp", "channel", "revenue"]


def validate_and_clean(df: pl.DataFrame) -> tuple[pl.DataFrame, ValidationResult]:
    """
    Validates raw event data after column mapping has been applied.
    Returns a cleaned dataframe plus a report of what was wrong.
    Never raises on dirty data — collects errors/warnings instead,
    so the caller can decide whether to proceed or abort.
    """
    result = ValidationResult()

    if df.is_empty():
        result.errors.append("No rows found in the data source.")
        return df, result

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        result.errors.append(f"Missing required columns after mapping: {missing_cols}")
        return df, result

    original_count = len(df)

    # drop rows with null/empty user_id or channel — can't build a journey without them
    before = len(df)
    df = df.filter(
        pl.col("user_id").is_not_null()
        & (pl.col("user_id").cast(pl.Utf8).str.strip_chars() != "")
        & pl.col("channel").is_not_null()
        & (pl.col("channel").cast(pl.Utf8).str.strip_chars() != "")
    )
    dropped = before - len(df)
    if dropped:
        result.warnings.append(f"Dropped {dropped} row(s) with missing user_id or channel.")

    # parse timestamp; drop unparseable rows rather than crashing
    if df["timestamp"].dtype == pl.Utf8:
        before = len(df)
        df = df.with_columns(
            pl.col("timestamp").str.to_datetime(strict=False).alias("timestamp")
        )
        df = df.filter(pl.col("timestamp").is_not_null())
        dropped = before - len(df)
        if dropped:
            result.warnings.append(f"Dropped {dropped} row(s) with an unparseable timestamp.")

    # revenue: coerce to float, treat negative as invalid (not a valid conversion amount)
    df = df.with_columns(pl.col("revenue").cast(pl.Float64, strict=False))
    before = len(df)
    negative = df.filter(pl.col("revenue") < 0)
    if len(negative) > 0:
        result.warnings.append(
            f"Found {len(negative)} row(s) with negative revenue — treated as 0."
        )
        df = df.with_columns(
            pl.when(pl.col("revenue") < 0).then(0.0).otherwise(pl.col("revenue")).alias("revenue")
        )
    df = df.with_columns(pl.col("revenue").fill_null(0.0))

    # exact duplicate rows (same user, timestamp, channel, revenue) rarely intentional
    before = len(df)
    df = df.unique(subset=["user_id", "timestamp", "channel", "revenue"], keep="first")
    dropped = before - len(df)
    if dropped:
        result.warnings.append(f"Removed {dropped} exact duplicate row(s).")

    if df.is_empty():
        result.errors.append(
            f"All {original_count} row(s) were dropped during cleaning — check your data format."
        )
        return df, result

    kept_ratio = len(df) / original_count
    if kept_ratio < 0.5:
        result.warnings.append(
            f"More than half the rows ({original_count - len(df)} of {original_count}) "
            f"were dropped during cleaning — the source data may be malformed."
        )

    return df, result
