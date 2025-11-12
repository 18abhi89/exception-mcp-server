#!/usr/bin/env python3
"""
Reload ChromaDB with updated exception history including stacktraces.
"""

from exception_db import ExceptionDB
from pathlib import Path

def main():
    print("Reloading ChromaDB with updated exception history...")

    # Initialize DB
    db = ExceptionDB()

    # Clear existing data
    print("Clearing existing data...")
    db.clear()

    # Load new data from CSV
    csv_path = Path(__file__).parent / "data" / "exception_history.csv"
    print(f"Loading data from {csv_path}...")

    count = db.load_from_csv(str(csv_path))

    print(f"✓ Successfully loaded {count} exception records with stacktraces")
    print(f"✓ Total records in database: {db.count()}")

    # Test similarity search with stacktrace
    print("\nTesting similarity search with stacktrace...")
    test_stacktrace = """java.lang.IllegalArgumentException: Invalid event type: TRANSFER
    at com.trading.validation.EventTypeValidator.validate(EventTypeValidator.java:45)
    at com.trading.ingestion.MessageProcessor.processMessage(MessageProcessor.java:112)"""

    similar = db.find_similar(
        error_message="Unsupported event type",
        exception_type="ValidationException",
        stacktrace=test_stacktrace,
        n_results=3
    )

    if similar:
        print(f"\n✓ Found {len(similar)} similar exceptions")
        for i, sim in enumerate(similar, 1):
            similarity = (1 - sim['distance']) * 100
            metadata = sim.get('metadata', {})
            print(f"\n  {i}. Similarity: {similarity:.1f}%")
            print(f"     Type: {metadata.get('exception_type', 'N/A')}")
            print(f"     Category: {metadata.get('exception_category', 'N/A')}")
            print(f"     Sub-Category: {metadata.get('exception_sub_category', 'N/A')}")
    else:
        print("✗ No similar exceptions found")

    print("\n✓ Database reload complete!")

if __name__ == "__main__":
    main()
