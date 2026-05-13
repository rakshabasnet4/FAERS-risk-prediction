import polars as pl

df = pl.read_parquet("appended_data/demo_dedup.parquet")

print("Before simple dedup:")
print("Total rows:", len(df))
print("Unique CASEIDs:", df["caseid"].n_unique())

dedup_fields = [
    "reporter_country",
    "gndr_cod",
    "event_dt",
    "age",
    "reactions",
    "drugs"
]

df_simple_dedup = df.unique(subset=dedup_fields, keep="first")

print("After simple dedup:")
print("Total rows:", len(df_simple_dedup))
print("Unique CASEIDs:", df_simple_dedup["caseid"].n_unique())

df_simple_dedup.write_parquet("final_demo_dedup.parquet")
print("Simple dedup dataset saved!")
