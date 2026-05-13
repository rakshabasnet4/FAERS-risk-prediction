import polars as pl
import pandas as pd
import os

demo = pl.scan_parquet("appended_data/demo.parquet", low_memory=False)

demo_len = demo.select(pl.len()).collect().item()
print("Original demo length:", demo_len)

demo = (
    demo
    .with_columns([
        pl.col("primaryid").cast(pl.Int64, strict=False),
        pl.col("caseid").cast(pl.Int64, strict=False),
        pl.col("event_dt").cast(pl.Int64, strict=False)  # or keep as string if needed
    ])
    .sort(
        ["caseid", "event_dt", "primaryid"],
        descending=[False, True, True]
    )
    .unique(subset=["caseid"], keep="first")
)

print("Checking deduped demo size...")
demo_len = demo.select(pl.len()).collect().item()
print("Deduped demo length:", demo_len)


drug = pl.scan_parquet("appended_data/drug.parquet")
reac = pl.scan_parquet("appended_data/reac.parquet")
indi = pl.scan_parquet("appended_data/indi.parquet")
ther = pl.scan_parquet("appended_data/ther.parquet")

def cast_keys(df):
    return df.with_columns([
        pl.col("primaryid").cast(pl.Int64, strict=False),
        pl.col("caseid").cast(pl.Int64, strict=False)
    ])

drug = cast_keys(drug)
reac = cast_keys(reac)
indi = cast_keys(indi)
ther = cast_keys(ther)

valid_keys = demo.select(["caseid", "primaryid"])

drug_f = drug.join(valid_keys, on=["caseid", "primaryid"], how="inner")
reac_f = reac.join(valid_keys, on=["caseid", "primaryid"], how="inner")
indi_f = indi.join(valid_keys, on=["caseid", "primaryid"], how="inner")
ther_f = ther.join(valid_keys, on=["caseid", "primaryid"], how="inner")

print("All tables filtered to latest PRIMARYID per CASEID")

def agg_unique_sorted(col_name, alias):
    return pl.col(col_name).drop_nulls().unique().sort().alias(alias)

drugs_agg = drug_f.select(["caseid", "drugname"]).group_by("caseid").agg(
    agg_unique_sorted("drugname", "drugs")
)
reac_agg = reac_f.select(["caseid", "pt"]).group_by("caseid").agg(
    agg_unique_sorted("pt", "reactions")
)
indi_agg = indi_f.select(["caseid", "indi_pt"]).group_by("caseid").agg(
    agg_unique_sorted("indi_pt", "indications")
)

ther_agg = ther_f.select(["caseid", "start_dt"]).group_by("caseid").agg([
    pl.col("start_dt").drop_nulls().unique().sort().alias("start_dt_all")
])

df = (
    demo
    .join(drugs_agg, on="caseid", how="left")
    .join(reac_agg, on="caseid", how="left")
    .join(indi_agg, on="caseid", how="left")
    .join(ther_agg, on="caseid", how="left")
)

dedup_cols = [
    "caseid", "primaryid", "gndr_cod", "age", "reporter_country",
    "event_dt", "drugs", "indications", "reactions", "start_dt_all"
]
df_dedup_ready = df.select(dedup_cols)

df_final = df_dedup_ready.collect()

print("Final Dedup:", len(df_final))

df_final.write_parquet("demo_dedup.parquet")
print("Dedup-ready dataset with start_dt saved!")

print("Unique CASEIDs:", df_final["caseid"].n_unique())
print("Total rows:", len(df_final))
