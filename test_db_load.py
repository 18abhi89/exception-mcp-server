#!/usr/bin/env python3
"""
Test script to verify ChromaDB data loading with metadata fix.
"""
import sys
from pathlib import Path
from exception_db import ExceptionDB

def main():
    print("=" * 60)
    print("Testing ChromaDB Data Loading")
    print("=" * 60)

    # Initialize DB
    print("\n1. Initializing database...")
    db = ExceptionDB()

    # Check current count
    current_count = db.count()
    print(f"   Current record count: {current_count}")

    # Clear existing data
    print("\n2. Clearing existing data...")
    db.clear()
    print(f"   Record count after clear: {db.count()}")

    # Load new data from CSV
    csv_path = Path(__file__).parent / "data" / "exception_history.csv"
    print(f"\n3. Loading data from: {csv_path}")

    try:
        count = db.load_from_csv(str(csv_path))
        print(f"   ✓ Successfully loaded {count} records")
    except Exception as e:
        print(f"   ✗ ERROR loading data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Verify data was loaded
    final_count = db.count()
    print(f"\n4. Final database count: {final_count}")

    if final_count != count:
        print(f"   ✗ WARNING: Expected {count} but got {final_count}")
    else:
        print(f"   ✓ Count matches expected value")

    # Test similarity search
    print("\n5. Testing similarity search...")
    try:
        similar = db.find_similar(
            error_message="Unsupported event type",
            exception_type="ValidationException",
            exception_category="VALIDATION",
            stacktrace="java.lang.IllegalArgumentException",
            n_results=3
        )

        if similar:
            print(f"   ✓ Found {len(similar)} similar exceptions")
            for i, sim in enumerate(similar, 1):
                similarity = (1 - sim['distance']) * 100
                metadata = sim.get('metadata', {})
                print(f"\n   Result {i}:")
                print(f"     - Similarity: {similarity:.1f}%")
                print(f"     - Type: {metadata.get('exception_type', 'N/A')}")
                print(f"     - Category: {metadata.get('exception_category', 'N/A')}")
                print(f"     - Resolution: {metadata.get('resolution', 'N/A')[:80]}...")
        else:
            print("   ✗ No similar exceptions found")
    except Exception as e:
        print(f"   ✗ ERROR during search: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("✓ Database test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
