import polars as pl

from attribution.connectors.csv import CSVConnector
from attribution.journey import build_journeys
from attribution.markov import (
    markov_attribution,
    calculate_last_click,
    calculate_linear,
    calculate_time_decay,
)
from attribution.metrics import compute_metrics
from attribution.validation import validate_and_clean

CONNECTORS = {
    "csv": CSVConnector,
}


class AnalysisError(Exception):
    """Raised when the analysis cannot proceed (bad config or unusable data)."""


def build_connector_config(config: dict) -> dict:
    source = config["source"]
    if source == "csv":
        if not config.get("file_path") and config.get("dataframe") is None:
            raise AnalysisError("A file path or in-memory dataframe is required for csv source")
        return {"file_path": config.get("file_path")}
    raise AnalysisError(f"Unsupported source: {source}")


def run_analysis(config: dict, raw_df: pl.DataFrame = None) -> dict:
    """
    Core analysis pipeline. Returns a plain dict (JSON-serialisable) with
    summary, per-model attribution results, top conversion paths, an
    optional segment breakdown, and a data-quality report.

    If raw_df is provided (an uploaded file already parsed by the caller),
    it is used directly instead of going through a connector.
    """
    if raw_df is not None:
        df = raw_df
    else:
        source = config["source"]
        if source not in CONNECTORS:
            raise AnalysisError(f"Unsupported source: {source}")
        connector = CONNECTORS[source](build_connector_config(config))
        df = connector.fetch(config.get("start_date"), config.get("end_date"))

    if df.is_empty():
        raise AnalysisError("No data found for the given source/date range.")

    # Segment column is optional — capture its values under a stable
    # name *before* the required-column rename, since the user's chosen
    # segment column name isn't part of the fixed mapping below.
    segment_col = config.get("segment_col")
    if segment_col:
        if segment_col not in df.columns:
            raise AnalysisError(f"Segment column not found in data: {segment_col}")
        df = df.rename({segment_col: "_segment"})

    mapping = {
        config["user_col"]: "user_id",
        config["timestamp_col"]: "timestamp",
        config["channel_col"]: "channel",
        config["revenue_col"]: "revenue",
    }
    missing = [c for c in mapping if c not in df.columns]
    if missing:
        raise AnalysisError(f"Column(s) not found in data: {missing}")
    df = df.rename(mapping)

    df, validation = validate_and_clean(df)
    if not validation.is_valid:
        raise AnalysisError("; ".join(validation.errors))

    journeys = build_journeys(df)
    if journeys.is_empty():
        raise AnalysisError("No journeys could be built from the cleaned data.")

    total_revenue = journeys["total_revenue"].sum()
    metrics = compute_metrics(journeys)

    model = config.get("model", "both")
    results = {}
    if model in ("last-click", "both"):
        results["last_click"] = calculate_last_click(journeys, total_revenue)
    if model in ("linear", "both"):
        results["linear"] = calculate_linear(journeys, total_revenue)
    if model in ("time-decay", "both"):
        results["time_decay"] = calculate_time_decay(journeys, total_revenue)
    if model in ("markov", "both"):
        results["markov"] = markov_attribution(journeys, total_revenue)

    for key in results:
        if results[key]:
            total = sum(results[key].values())
            if total > 0 and total != total_revenue:
                for ch in results[key]:
                    results[key][ch] = (results[key][ch] / total) * total_revenue

    all_channels = sorted({ch for key in results for ch in results[key]})
    comparison = [
        {"channel": ch, **{key: round(results[key].get(ch, 0.0), 2) for key in results}}
        for ch in all_channels
    ]

    top_paths = _top_conversion_paths(journeys, limit=15)
    segment_breakdown = _segment_breakdown(df) if segment_col else []

    return {
        "summary": {
            "total_users": metrics["total_users"],
            "total_touches": metrics["total_touches"],
            "conversion_users": metrics["conversion_users"],
            "non_conversion_users": metrics["non_conversion_users"],
            "conversion_rate": round(metrics["conversion_rate"], 2),
            "avg_revenue_per_converting_user": round(metrics["avg_revenue_per_converting_user"], 2),
            "total_revenue": round(total_revenue, 2),
        },
        "comparison": comparison,
        "top_paths": top_paths,
        "segment_breakdown": segment_breakdown,
        "data_quality": {
            "warnings": validation.warnings,
        },
    }


def _top_conversion_paths(journeys: pl.DataFrame, limit: int = 15) -> list[dict]:
    converting = journeys.filter(pl.col("has_conversion"))
    if converting.is_empty():
        return []

    grouped = (
        converting
        .with_columns(pl.col("journey").list.join(" → ").alias("path_label"))
        .group_by("path_label")
        .agg(
            pl.len().alias("count"),
            pl.col("total_revenue").sum().alias("revenue"),
        )
        .sort("count", descending=True)
        .head(limit)
    )

    return [
        {"path": row["path_label"], "count": row["count"], "revenue": round(row["revenue"], 2)}
        for row in grouped.iter_rows(named=True)
    ]


def _segment_breakdown(df: pl.DataFrame, limit: int = 20) -> list[dict]:
    """
    Simple total-revenue breakdown by an optional user-chosen segment
    column (e.g. country, device). Deliberately not cross-multiplied
    with the attribution models — that combination grows too large to
    show usefully, and this keeps the feature easy to reason about.
    """
    converting = df.filter(pl.col("revenue") > 0)
    if converting.is_empty():
        return []

    grouped = (
        converting
        .group_by("_segment")
        .agg(
            pl.len().alias("count"),
            pl.col("revenue").sum().alias("revenue"),
        )
        .sort("revenue", descending=True)
        .head(limit)
    )

    return [
        {
            "segment": str(row["_segment"]) if row["_segment"] is not None else "(empty)",
            "count": row["count"],
            "revenue": round(row["revenue"], 2),
        }
        for row in grouped.iter_rows(named=True)
    ] 