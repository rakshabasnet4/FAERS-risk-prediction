import polars as pl

df = pl.scan_parquet("FAERS_final.parquet")

df = df.with_columns([
    pl.col("dose_amt")
    .cast(pl.Utf8)
    .str.to_lowercase()
    .str.replace_all(",", "")
    .str.strip_chars()
    .alias("dose_amt_str")
])

df = df.with_columns([
    pl.when(pl.col("dose_amt_str").str.contains(r"\d+\s*-\s*\d+"))
    .then(
        pl.col("dose_amt_str")
        .str.extract_all(r"(\d+\.?\d*)")
        .list.eval(pl.element().cast(pl.Float64))
        .list.mean()
    )
    .otherwise(
        pl.col("dose_amt_str")
        .str.extract(r"(\d+\.?\d*)")
        .cast(pl.Float64)
    )
    .alias("dose_amt_clean")
])

df = df.with_columns([
    pl.col("dose_amt_clean").is_null().alias("dose_amt_missing"),
    pl.col("dose_amt_str").str.contains(r"[a-zA-Z]").alias("dose_amt_text_flag"),
    pl.col("dose_amt_str").str.contains(r"\d+\s*-\s*\d+").alias("dose_amt_range_flag"),
    pl.col("dose_amt_clean").is_not_null().alias("dose_amt_numeric_flag")
])

df.sink_parquet("faers_cleaned_full_with_flags.parquet")
