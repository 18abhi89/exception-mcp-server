#!/usr/bin/env python3
"""
Test script for exception analysis tools.

Tests all MCP tools end-to-end without requiring MCP client.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from exception_db import ExceptionDB
from server import (
    load_schema_from_csv,
    get_high_retry_exceptions,
    analyze_exception_with_history,
    load_exception_history,
    EXCEPTION_HISTORY_CSV
)


def test_schema_loading():
    """Test schema loading from CSV."""
    print("="*60)
    print("TEST 1: Schema Loading")
    print("="*60)
    schema = load_schema_from_csv()
    assert "exception_events" in schema
    assert "times_replayed" in schema
    print("✓ Schema loaded successfully")
    print(f"\nSchema preview:\n{schema[:200]}...\n")


def test_exception_db():
    """Test ChromaDB wrapper."""
    print("="*60)
    print("TEST 2: ChromaDB Operations")
    print("="*60)

    # Initialize DB
    db = ExceptionDB()

    # Clear existing data
    db.clear()
    print("✓ Database initialized and cleared")

    # Load history
    if EXCEPTION_HISTORY_CSV.exists():
        count = db.load_from_csv(str(EXCEPTION_HISTORY_CSV))
        print(f"✓ Loaded {count} historical exceptions")

        # Test similarity search
        similar = db.find_similar(
            error_message="Unsupported event type TRANSFER",
            exception_type="ValidationException",
            n_results=3
        )
        print(f"✓ Found {len(similar)} similar exceptions")

        if similar:
            print(f"\n  Top match similarity: {(1 - similar[0]['distance']) * 100:.1f}%")
            print(f"  Resolution: {similar[0]['metadata'].get('resolution', 'N/A')[:80]}...")
    else:
        print("✗ Exception history file not found")


def test_high_retry_exceptions():
    """Test getting high retry exceptions."""
    print("\n" + "="*60)
    print("TEST 3: High Retry Exceptions")
    print("="*60)

    exceptions = get_high_retry_exceptions(threshold=5)
    print(f"✓ Found {len(exceptions)} exceptions with > 5 retries")

    for exc in exceptions:
        print(f"\n  - Event {exc['event_id']}: {exc['times_replayed']} retries")
        print(f"    Error: {exc['error_message'][:60]}...")
        print(f"    Category: {exc['exception_category']}")


def test_exception_analysis():
    """Test exception analysis with historical data."""
    print("\n" + "="*60)
    print("TEST 4: Exception Analysis")
    print("="*60)

    # Get a high-retry exception
    exceptions = get_high_retry_exceptions(threshold=5)

    if exceptions:
        exc = exceptions[0]  # Pick the first one
        print(f"\nAnalyzing exception: {exc['exception_id']}")
        print(f"Event ID: {exc['event_id']}")
        print(f"Retries: {exc['times_replayed']}")

        # Load history first
        load_exception_history()

        # Analyze
        analysis = analyze_exception_with_history(exc)
        print("\n" + "-"*60)
        print(analysis[:500])  # Show first 500 chars
        print("...")
        print("-"*60)
        print("✓ Analysis completed successfully")
    else:
        print("No high-retry exceptions found for analysis")


def test_similarity_search():
    """Test finding similar exceptions."""
    print("\n" + "="*60)
    print("TEST 5: Similarity Search")
    print("="*60)

    load_exception_history()

    # Test various error messages
    test_cases = [
        "DELETE operation on non-existent trade",
        "Schema validation failed missing field",
        "Settlement date calculation failed"
    ]

    for error_msg in test_cases:
        from server import exception_db
        similar = exception_db.find_similar(error_message=error_msg, n_results=2)
        print(f"\nQuery: '{error_msg}'")
        print(f"Found {len(similar)} similar cases")
        if similar:
            similarity = (1 - similar[0]['distance']) * 100
            print(f"  Best match: {similarity:.1f}% similar")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("EXCEPTION ANALYSIS TOOLS - END-TO-END TEST")
    print("="*60 + "\n")

    try:
        test_schema_loading()
        test_exception_db()
        test_high_retry_exceptions()
        test_exception_analysis()
        test_similarity_search()

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60 + "\n")
        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
