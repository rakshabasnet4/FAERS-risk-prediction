# Uses the RXnorm API to normalize the drug names in the FAERS dataset.

import polars as pl
import requests
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import local

DRUG_PATH  = "FAERSdata/drug.parquet"
CACHE_PATH = "FAERSdata/rxnorm_cache.parquet"
OUTPUT_PATH = "FAERSdata/drug_normalized.parquet"
BASE       = "https://rxnav.nlm.nih.gov/REST"
N_THREADS  = 4

# ── Step 1: Get unique drug names ─────────────────────────────────────────────
# Get the drugname col from the Drug df and perform basic cleaning, drop nulls, then get unique drugs, then make new drug list into a python list
unique_drugs = (
    pl.scan_parquet(DRUG_PATH)
    .select(
        pl.col("drugname")
        .str.strip_chars()
        .str.to_uppercase()
        .str.replace_all(r"\s+", " ")
        .alias("drugname_clean")
    )
    .drop_nulls()
    .unique()
    .collect()
    .get_column("drugname_clean")
    .to_list()
)

# ── Step 2: Thread-local session ──────────────────────────────────────────────
thread_local = local()

# get a session for each thread
def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session

#API lookup function
def get_rxnorm(drugname: str, retries: int = 3) -> dict:
    session = get_session()
    null_result = {"drugname_clean": drugname, "rxcui": None, "rx_name": None, "rx_score": None}

    #loops attemps, sleeps to stop from getting banned from API
    for attempt in range(retries):
        try:
            time.sleep(0.2)

            #get request to Rxnorm API
            r = session.get(
                f"{BASE}/approximateTerm.json",
                params={"term": drugname, "maxEntries": 2},
                timeout=10
            )

            r.raise_for_status()

            #gets info from API result, if null return null result field
            candidates = r.json().get("approximateGroup", {}).get("candidate", [])
            if not candidates:
                return null_result
            best = next((c for c in candidates if c.get("source") == "RXNORM"), candidates[0])

            #returns important info about the drug that was queried to the API, turns into dict object
            return {
                "drugname_clean": drugname,
                "rxcui":          best.get("rxcui"),
                "rx_name":        best.get("name"),
                "rx_score":       best.get("score")
            }

        #if there is an error waits then tries again up to re-tries times (3).
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.5)
            continue
    return null_result

# ── Step 3: Load cache ────────────────────────────────────────────────────────
#Create a cache so if the program fails lookup doesn't have to start all over again.
try:
    cache_df = pl.read_parquet(CACHE_PATH)
    cache    = {row["drugname_clean"]: row for row in cache_df.to_dicts()}
    print(f"Loaded {len(cache):,} cached lookups")
except Exception:
    cache = {}
    print("Starting fresh cache")

# filter missing from cache
to_lookup = [d for d in unique_drugs if d not in cache or cache[d]["rxcui"] is None]
print(f"Still need to look up: {len(to_lookup):,}")

# ── Step 4: Parallel lookup ───────────────────────────────────────────────────
results = []
#start thread pool.
with ThreadPoolExecutor(max_workers=N_THREADS) as executor:
    futures = {executor.submit(get_rxnorm, d): d for d in to_lookup}

    for future in tqdm(as_completed(futures), total=len(futures), desc="RxNorm lookups"):
        result = future.result()
        cache[result["drugname_clean"]] = result
        results.append(result)

        if len(results) % 1000 == 0:
            pl.DataFrame(list(cache.values())).write_parquet(CACHE_PATH)

pl.DataFrame(list(cache.values())).write_parquet(CACHE_PATH)
print(f"Cache saved: {len(cache):,} total entries")

# ── Step 5: Merge back onto drug_df ──────────────────────────────────────────
import pyarrow.parquet as pq

rxnorm_map = pl.read_parquet(CACHE_PATH).to_dicts()
rxnorm_map = {r["drugname_clean"]: r for r in rxnorm_map}


#chunk writing parameters
pf         = pq.ParquetFile(DRUG_PATH)
CHUNK_SIZE = 200_000
writer     = None

#perform previous name cleaning again in batches
for batch in tqdm(pf.iter_batches(batch_size=CHUNK_SIZE), desc="Merging chunks"):
    chunk = pl.from_arrow(batch).with_columns(
        pl.col("drugname")
        .str.strip_chars()
        .str.to_uppercase()
        .str.replace_all(r"\s+", " ")
        .alias("drugname_clean")
    )

    #dict lookup adding drug info to new column
    for col in ("rxcui", "rx_name", "rx_score"):
        chunk = chunk.with_columns(
            pl.Series(col, [rxnorm_map.get(d, {}).get(col) for d in chunk["drugname_clean"]])
        )

    # Write incrementally to parquet instead of collecting all chunks in memory
    arrow_table = chunk.to_arrow()
    if writer is None:
        writer = pq.ParquetWriter(OUTPUT_PATH, arrow_table.schema)
    writer.write_table(arrow_table)
    del chunk, arrow_table

if writer:
    writer.close()

# Compute match rate without loading full df
match_rate = (
    pl.scan_parquet(OUTPUT_PATH)
    .select(pl.col("rxcui").is_not_null().mean())
    .collect()
    .item()
)
print(f"Match rate: {match_rate:.1%}")
print(
    pl.scan_parquet(OUTPUT_PATH)
    .select(["drugname", "drugname_clean", "rx_name", "rxcui", "rx_score"])
    .head(10)
    .collect()
)
