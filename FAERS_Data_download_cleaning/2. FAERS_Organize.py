# Cleans up names of the FAERS data files and
# Organize downloaded FEARS data files into folders
# by year and quarter
import os
import shutil
import re

ascii_dir = "FAERSdata/ascii"

for filename in os.listdir(ascii_dir):
    if not filename.endswith(".txt"):
        continue

    # Match patterns like demo12q4.txt or DRUG2024Q1.txt
    match = re.search(r'(\d{2,4})q(\d)', filename, re.IGNORECASE)
    if not match:
        print(f"Could not parse: {filename}")
        continue

    year = match.group(1)
    quarter = match.group(2)

    # Normalize 2-digit years to 4-digit
    if len(year) == 2:
        year = "20" + year

    folder = os.path.join(ascii_dir, f"{year}_Q{quarter}")
    os.makedirs(folder, exist_ok=True)

    src = os.path.join(ascii_dir, filename)
    dst = os.path.join(folder, filename)
    shutil.move(src, dst)
    print(f"Moved {filename} to {year}_Q{quarter}/")

print("Organization complete")
