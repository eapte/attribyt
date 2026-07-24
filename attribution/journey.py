import polars as pl

def build_journeys(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(pl.col('revenue').cast(pl.Float64, strict=False))
    df_sorted = df.sort(['user_id', 'timestamp'])
    journeys = (
        df_sorted
        .group_by('user_id')
        .agg([
            pl.col('channel').alias('journey'),
            pl.col('revenue').sum().alias('total_revenue')
        ])
    )
    return journeys