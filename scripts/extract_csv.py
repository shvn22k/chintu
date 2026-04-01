import _repo  # noqa: F401

import zipfile
import os

from chintu.config import GDELT_RAW_DIR, GDELT_ZIPS_DIR

os.makedirs(GDELT_RAW_DIR, exist_ok=True)

zip_files = list(GDELT_ZIPS_DIR.glob("*.zip"))
print(f"Found {len(zip_files)} zip files to extract")

extracted = 0
failed = 0

for zip_path in zip_files:
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('.CSV'):
                    zf.extract(name, GDELT_RAW_DIR)
                    extracted += 1
                    print(f"Extracted: {name}")
    except Exception as e:
        print(f"Failed: {zip_path.name} | {e}")
        failed += 1

print(f"\nDone! Extracted {extracted} CSV files to '{GDELT_RAW_DIR}/'")
if failed:
    print(f"Failed: {failed} files")
