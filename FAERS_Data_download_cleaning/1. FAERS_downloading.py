# downloads all the FAERS datasets from 2012 - 2025

import urllib.request
import zipfile
import os
from itertools import product

output_dir = "FAERSdata"
os.makedirs(output_dir, exist_ok=True)

# Adjust year range as needed
years = range(2012, 2025)
quarters = range(1, 5)

base_url = "https://fis.fda.gov/content/Exports/faers_ascii_"

for year, quarter in product(years, quarters):
    filename = f"faers_ascii_{year}q{quarter}.zip"
    url = base_url + f"{year}q{quarter}.zip"
    dest = os.path.join(output_dir, filename)

    try:
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, dest)

        # Auto-extract
        with zipfile.ZipFile(dest, 'r') as z:
            z.extractall(output_dir)
        os.remove(dest)  # delete zip after extracting

    except Exception as e:
        print(f"Skipped {filename}: {e}")

print("Done!")
