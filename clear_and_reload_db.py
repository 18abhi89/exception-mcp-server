#!/usr/bin/env python3
"""
Clear ChromaDB and reload with fresh data including stacktraces.

Run this script after updating exception_db.py to ensure old data is cleared
and new data with proper metadata is loaded.
"""
import shutil
from pathlib import Path
from exception_db import ExceptionDB

def main():
    print("=" * 70)
    print("CLEARING AND RELOADING CHROMADB DATABASE")
    print("=" * 70)

    # Remove the entire chromadb_data directory to ensure clean state
    chromadb_dir = Path(__file__).parent / "chromadb_data"

    print(f"\n1. Removing chromadb_data directory: {chromadb_dir}")
    if chromadb_dir.exists():
        shutil.rmtree(chromadb_dir)
        print("   ✓ Removed old database")
    else:
        print("   ✓ No existing database found")

    # Initialize fresh database
    print("\n2. Initializing fresh ChromaDB database...")
    db = ExceptionDB()
    print(f"   ✓ Database initialized, count: {db.count()}")

    # Load exception history
    csv_path = Path(__file__).parent / "data" / "exception_history.csv"
    print(f"\n3. Loading exception history from: {csv_path}")

    if not csv_path.exists():
        print(f"   ✗ ERROR: CSV file not found at {csv_path}")
        return

    try:
        count = db.load_from_csv(str(csv_path))
        print(f"   ✓ Successfully loaded {count} exception records")
    except Exception as e:
        print(f"   ✗ ERROR loading data: {e}")
        import traceback
        traceback.print_exc()
        return

    # Verify loaded data
    final_count = db.count()
    print(f"\n4. Verification:")
    print(f"   - Expected records: {count}")
    print(f"   - Actual records: {final_count}")

    if final_count == count:
        print("   ✓ All records loaded successfully!")
    else:
        print(f"   ✗ WARNING: Count mismatch!")

    # Test a simple query
    print("\n5. Testing similarity search...")
    try:
        test_results = db.find_similar(
            error_message="validation failed",
            exception_type="ValidationException",
            n_results=3
        )
        print(f"   ✓ Search returned {len(test_results)} results")
    except Exception as e:
        print(f"   ✗ Search failed: {e}")

    print("\n" + "=" * 70)
    print("✓ DATABASE RELOAD COMPLETE!")
    print("=" * 70)
    print("\nYou can now run: streamlit run streamlit_app.py")
    print()

if __name__ == "__main__":
    main()
