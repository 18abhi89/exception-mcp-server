# ChromaDB Reload Instructions

## Problem Fixed
The metadata handling in `exception_db.py` has been updated to properly filter out `None` values while keeping empty strings, which ChromaDB accepts.

## How to Reload the Database

### Step 1: Clear Old Data
Delete the existing `chromadb_data` directory to remove old data:

```bash
rm -rf chromadb_data/
```

### Step 2: Reload with New Code
Run the reload script:

```bash
python clear_and_reload_db.py
```

OR manually reload in Python:

```python
from exception_db import ExceptionDB
import shutil
from pathlib import Path

# Remove old database
shutil.rmtree('chromadb_data/', ignore_errors=True)

# Create fresh database and load data
db = ExceptionDB()
count = db.load_from_csv('data/exception_history.csv')
print(f"Loaded {count} records")
```

### Step 3: Run Streamlit App
```bash
streamlit run streamlit_app.py
```

## What Was Fixed

### Before (Broken):
- `None` values in metadata caused ChromaDB TypeError
- Empty strings were being filtered out (incorrectly)
- Old database wasn't being cleared, so new code wasn't applied

### After (Fixed):
- `None` values are properly filtered out
- Empty strings are kept (ChromaDB accepts them)
- `load_from_csv()` safely handles missing/empty CSV fields
- Integer fields like `times_replayed` are properly converted

## Verification

After reloading, verify the database:

```python
from exception_db import ExceptionDB

db = ExceptionDB()
print(f"Total records: {db.count()}")

# Test search
results = db.find_similar(
    error_message="validation failed",
    exception_type="ValidationException",
    stacktrace="java.lang.IllegalArgumentException",
    n_results=5
)

for r in results:
    print(f"- {r['metadata']['exception_type']}: {r['distance']:.3f}")
```

## Troubleshooting

### If data still doesn't show up:
1. Completely remove `chromadb_data/` directory
2. Restart Python/Streamlit to clear caches
3. Run `clear_and_reload_db.py` again

### If you see "No similar exceptions found":
- Check that `data/exception_history.csv` has data with stacktrace column
- Verify `db.count()` returns > 0
- Check Chrome/browser console for JavaScript errors in Streamlit
