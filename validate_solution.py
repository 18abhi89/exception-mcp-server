#!/usr/bin/env python3
"""
Comprehensive validation script to verify the metadata fix works correctly.
"""
import sys
import csv
from pathlib import Path
from exception_db import ExceptionDB

def test_metadata_cleaning():
    """Test that metadata cleaning works correctly."""
    print("\n" + "="*70)
    print("TEST 1: Metadata Cleaning")
    print("="*70)

    test_cases = [
        {
            "input": {"key1": "value", "key2": None, "key3": "", "key4": 42},
            "expected": {"key1": "value", "key3": "", "key4": 42},
            "description": "None filtered, empty string kept, int kept"
        },
        {
            "input": {"bool_val": True, "none_val": None, "float_val": 3.14},
            "expected": {"bool_val": True, "float_val": 3.14},
            "description": "None filtered, bool and float kept"
        },
    ]

    for i, test in enumerate(test_cases, 1):
        result = ExceptionDB._clean_metadata(test["input"])
        if result == test["expected"]:
            print(f"✓ Test {i} PASSED: {test['description']}")
        else:
            print(f"✗ Test {i} FAILED: {test['description']}")
            print(f"  Expected: {test['expected']}")
            print(f"  Got: {result}")
            return False

    return True


def test_csv_data():
    """Test that CSV data has the expected format."""
    print("\n" + "="*70)
    print("TEST 2: CSV Data Format")
    print("="*70)

    csv_path = Path(__file__).parent / "data" / "exception_history.csv"

    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_path}")
        return False

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"✓ Found {len(rows)} rows in CSV")

    required_columns = [
        'exception_id', 'error_message', 'exception_type',
        'exception_category', 'stacktrace'
    ]

    if rows:
        first_row = rows[0]
        missing_cols = [col for col in required_columns if col not in first_row]

        if missing_cols:
            print(f"✗ Missing required columns: {missing_cols}")
            return False

        print(f"✓ All required columns present")

        # Check if stacktrace column has data
        rows_with_stacktrace = sum(1 for row in rows if row.get('stacktrace') and row.get('stacktrace').strip())
        print(f"✓ {rows_with_stacktrace}/{len(rows)} rows have stacktrace data")

    return True


def test_database_operations():
    """Test database operations without actually loading (to avoid ChromaDB issues)."""
    print("\n" + "="*70)
    print("TEST 3: Database Structure")
    print("="*70)

    try:
        db = ExceptionDB()
        print(f"✓ Database initialized successfully")
        print(f"✓ Current record count: {db.count()}")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False


def print_loading_instructions():
    """Print instructions for the user."""
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("""
To load the data with the fixed code:

1. Clear the old database:
   rm -rf chromadb_data/

2. Run the reload script:
   python clear_and_reload_db.py

3. Start Streamlit:
   streamlit run streamlit_app.py

4. Verify in Streamlit:
   - Go to "Analyze Exception" tab
   - Select any exception from the dropdown
   - Click "Analyze with Historical Data"
   - You should see similar historical cases with stacktraces

If you see "No similar historical cases found", the database needs to be
reloaded. Make sure you deleted chromadb_data/ directory first!
    """)


def main():
    print("="*70)
    print("VALIDATING METADATA FIX SOLUTION")
    print("="*70)

    tests = [
        ("Metadata Cleaning", test_metadata_cleaning),
        ("CSV Data Format", test_csv_data),
        ("Database Structure", test_database_operations),
    ]

    all_passed = True
    for test_name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL VALIDATION TESTS PASSED!")
        print("="*70)
        print_loading_instructions()
    else:
        print("✗ SOME TESTS FAILED - CHECK OUTPUT ABOVE")
        print("="*70)
        sys.exit(1)


if __name__ == "__main__":
    main()
