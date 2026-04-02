import _bootstrap  # noqa: F401

import requests
import os
from datetime import datetime

from chintu.config import GDELT_ZIPS_DIR

# CONFIG
MASTER_URL = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
DOWNLOAD_DIR = str(GDELT_ZIPS_DIR)
FILES_PER_DAY = 2  # change if needed
TARGET_MONTH = "202603"  # March 2026 (YYYYMM format)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

print("Fetching master file list...")
response = requests.get(MASTER_URL)
lines = response.text.split("\n")

# Step 1: Filter only export files for target month
export_files = []

for line in lines:
    if ".export.CSV.zip" in line:
        parts = line.strip().split(" ")
        if len(parts) < 3:
            continue
        url = parts[-1]
        filename = url.split("/")[-1]

        # Extract timestamp from filename
        timestamp_str = filename.split(".")[0]  # e.g. 20260330161500
        if timestamp_str.startswith(TARGET_MONTH):
            export_files.append((timestamp_str, url))

# Step 2: Group by day
files_by_day = {}
for timestamp_str, url in export_files:
    day = timestamp_str[:8]  # YYYYMMDD
    files_by_day.setdefault(day, []).append((timestamp_str, url))

# Step 3: Sample files per day
selected_files = []

for day, files in sorted(files_by_day.items()):
    files.sort()
    step = max(1, len(files) // FILES_PER_DAY)

    sampled = files[::step][:FILES_PER_DAY]
    selected_files.extend(sampled)

print(f"Selected {len(selected_files)} files for download.")

# Step 4: Download files
for timestamp, url in selected_files:
    filename = url.split("/")[-1]
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    if os.path.exists(filepath):
        print(f"Skipping (exists): {filename}")
        continue

    print(f"Downloading: {filename}")
    try:
        r = requests.get(url, timeout=30)
        with open(filepath, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"Failed: {filename} | {e}")

print("Download complete.")