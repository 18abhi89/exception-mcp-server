#!/usr/bin/env python3
"""
Test what data Streamlit app would see.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server import (
    get_high_retry_exceptions,
    load_exception_history,
    exception_db,
    EXCEPTIONS_CSV,
    EXCEPTION_HISTORY_CSV
)

print("=" * 70)
print("TESTING STREAMLIT DATA SOURCES")
print("=" * 70)

# Test 1: Check CSV files exist
print("\n1. CSV Files:")
print(f"   Current exceptions: {EXCEPTIONS_CSV}")
print(f"   Exists: {EXCEPTIONS_CSV.exists()}")
print(f"   Historical exceptions: {EXCEPTION_HISTORY_CSV}")
print(f"   Exists: {EXCEPTION_HISTORY_CSV.exists()}")

# Test 2: Load exception history into ChromaDB
print("\n2. Loading Exception History into ChromaDB:")
load_exception_history()
db_count = exception_db.count()
print(f"   ChromaDB records: {db_count}")

# Test 3: Get exceptions for dropdown (with threshold=0 to get ALL)
print("\n3. Current Exceptions (for dropdowns):")
all_exceptions = get_high_retry_exceptions(threshold=0)
print(f"   Total exceptions: {len(all_exceptions)}")

if all_exceptions:
    print("\n   Exceptions in dropdown:")
    for i, exc in enumerate(all_exceptions, 1):
        event_id = exc.get('event_id', 'N/A')
        error_msg = exc.get('error_message', 'N/A')[:50]
        times_replayed = exc.get('times_replayed', 0)
        print(f"   {i}. {event_id} - {error_msg}... (replayed: {times_replayed})")

# Test 4: Test a specific exception analysis
print("\n4. Testing Exception Analysis:")
if all_exceptions:
    test_exception = all_exceptions[0]
    print(f"   Analyzing: {test_exception['event_id']}")
    print(f"   Exception has 'trace' field: {'trace' in test_exception}")

    from server import analyze_exception_with_history

    try:
        analysis = analyze_exception_with_history(test_exception)
        print(f"   ✓ Analysis completed")
        print(f"   Analysis length: {len(analysis)} chars")

        # Check if similar cases were found
        if "No similar historical cases found" in analysis:
            print("   ⚠ Warning: No similar cases found in ChromaDB")
        elif "Similar Case" in analysis:
            print("   ✓ Found similar historical cases")
    except Exception as e:
        print(f"   ✗ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

# Test 5: Test similarity search directly
print("\n5. Direct ChromaDB Similarity Search Test:")
if all_exceptions:
    test_exc = all_exceptions[0]
    error_message = test_exc.get('error_message', '')
    exception_type = test_exc.get('exception_type', '')
    exception_category = test_exc.get('exception_category', '')
    stacktrace = test_exc.get('trace', '')

    print(f"   Searching for: {error_message[:50]}...")
    print(f"   Type: {exception_type}")
    print(f"   Category: {exception_category}")
    print(f"   Has stacktrace: {bool(stacktrace)}")

    similar = exception_db.find_similar(
        error_message=error_message,
        exception_type=exception_type,
        exception_category=exception_category,
        stacktrace=stacktrace,
        n_results=3
    )

    print(f"   Found {len(similar)} similar exceptions")
    for i, sim in enumerate(similar, 1):
        similarity = (1 - sim['distance']) * 100
        metadata = sim.get('metadata', {})
        print(f"   {i}. {metadata.get('exception_type', 'N/A')} - {similarity:.1f}% similar")

print("\n" + "=" * 70)
print("✓ TEST COMPLETE")
print("=" * 70)
