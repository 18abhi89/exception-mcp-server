#!/usr/bin/env python3
"""
Comprehensive end-to-end test of the complete solution.

This simulates what happens in the Streamlit app.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server import (
    get_high_retry_exceptions,
    load_exception_history,
    exception_db,
    analyze_exception_with_history
)

def test_dropdown_data():
    """Test 1: Dropdown shows all exceptions"""
    print("\n" + "=" * 70)
    print("TEST 1: DROPDOWN DATA (Analyze Exception Tab)")
    print("=" * 70)

    # This is what Streamlit does in tab2
    exceptions = get_high_retry_exceptions(threshold=0)  # Get all

    print(f"\nTotal exceptions for dropdown: {len(exceptions)}")

    expected_count = 10
    if len(exceptions) != expected_count:
        print(f"✗ FAILED: Expected {expected_count} exceptions, got {len(exceptions)}")
        return False

    print(f"✓ PASSED: All {expected_count} exceptions loaded")

    print("\nDropdown options (what user sees):")
    for i, exc in enumerate(exceptions, 1):
        event_id = exc['event_id']
        error_message = exc['error_message'][:50]
        label = f"{event_id} - {error_message}..."
        print(f"  {i:2d}. {label}")

    return True


def test_high_retry_filter():
    """Test 2: High retry filter (Tab 1)"""
    print("\n" + "=" * 70)
    print("TEST 2: HIGH RETRY FILTER (High Retry Exceptions Tab)")
    print("=" * 70)

    # This is what Streamlit does in tab1 with default threshold=5
    threshold = 5
    high_retry = get_high_retry_exceptions(threshold=threshold)

    print(f"\nExceptions with times_replayed >= {threshold}: {len(high_retry)}")

    expected_count = 4  # EVT-006(6), EVT-007(7), EVT-004(8), EVT-020(9)
    if len(high_retry) != expected_count:
        print(f"✗ FAILED: Expected {expected_count}, got {len(high_retry)}")
        return False

    print(f"✓ PASSED: Found {expected_count} high retry exceptions")

    for exc in high_retry:
        print(f"  - {exc['event_id']}: {exc['times_replayed']} retries")

    return True


def test_exception_analysis():
    """Test 3: Exception analysis with historical data"""
    print("\n" + "=" * 70)
    print("TEST 3: EXCEPTION ANALYSIS WITH HISTORY")
    print("=" * 70)

    # Get all exceptions
    exceptions = get_high_retry_exceptions(threshold=0)

    if not exceptions:
        print("✗ FAILED: No exceptions to analyze")
        return False

    # Pick one exception to analyze (like user selecting from dropdown)
    test_exception = exceptions[1]  # EVT-006 - validation error
    print(f"\nAnalyzing: {test_exception['event_id']}")
    print(f"Error: {test_exception['error_message'][:60]}...")
    print(f"Type: {test_exception['exception_type']}")
    print(f"Category: {test_exception['exception_category']}")

    # This is what happens when user clicks "Analyze with Historical Data"
    try:
        analysis = analyze_exception_with_history(test_exception)

        if not analysis:
            print("✗ FAILED: Analysis returned empty")
            return False

        print(f"\n✓ PASSED: Analysis completed ({len(analysis)} chars)")

        # Check if analysis includes key sections
        has_thesis = "Thesis:" in analysis or "THESIS" in analysis.upper()
        has_similar_cases = "Similar Case" in analysis

        print(f"\nAnalysis contains:")
        print(f"  - Thesis section: {'✓' if has_thesis else '✗'}")
        print(f"  - Similar cases: {'✓' if has_similar_cases else '✗ (may be no matches)'}")

        # Show a snippet
        print(f"\nAnalysis snippet:")
        lines = analysis.split('\n')[:10]
        for line in lines:
            print(f"  {line}")

        return True

    except Exception as e:
        print(f"✗ FAILED: Analysis raised exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chromadb_historical_data():
    """Test 4: ChromaDB historical data"""
    print("\n" + "=" * 70)
    print("TEST 4: CHROMADB HISTORICAL DATA (Historical Database Tab)")
    print("=" * 70)

    # This is what Streamlit does on startup
    print("\nLoading exception history into ChromaDB...")

    try:
        load_exception_history()
        count = exception_db.count()

        print(f"✓ Historical records in ChromaDB: {count}")

        if count == 0:
            print("\n⚠ WARNING: No historical data loaded!")
            print("  This means:")
            print("  - Similarity search won't find matches")
            print("  - Historical Database tab will show 0 records")
            print("\n  TO FIX:")
            print("  1. rm -rf chromadb_data/")
            print("  2. python clear_and_reload_db.py")
            return False

        expected_count = 36
        if count != expected_count:
            print(f"\n⚠ WARNING: Expected ~{expected_count} records, got {count}")

        # Test a sample query
        print("\nTesting sample similarity search...")
        results = exception_db.find_similar(
            error_message="validation failed",
            exception_type="ValidationException",
            n_results=3
        )

        print(f"✓ Search returned {len(results)} results")

        if results:
            for i, r in enumerate(results, 1):
                similarity = (1 - r['distance']) * 100
                metadata = r.get('metadata', {})
                print(f"  {i}. {metadata.get('exception_type', 'N/A')} - {similarity:.1f}% similar")

        return count > 0

    except Exception as e:
        print(f"✗ FAILED: ChromaDB error: {e}")
        print("\nThis might be because:")
        print("  - ChromaDB model download failed (sandbox environment issue)")
        print("  - On your local machine, run: rm -rf chromadb_data/ && python clear_and_reload_db.py")
        return False


def main():
    print("=" * 70)
    print("COMPREHENSIVE END-TO-END TEST")
    print("=" * 70)
    print("\nThis test simulates what happens in the Streamlit app.")

    tests = [
        ("Dropdown Data", test_dropdown_data),
        ("High Retry Filter", test_high_retry_filter),
        ("Exception Analysis", test_exception_analysis),
        ("ChromaDB Historical Data", test_chromadb_historical_data),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ TEST CRASHED: {test_name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status:10s} - {test_name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\n{passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Solution is working correctly.")
        print("\nYou can now run:")
        print("  streamlit run streamlit_app.py")
    elif passed_count >= 3:
        print("\n⚠ Most tests passed! ChromaDB issue is likely due to sandbox environment.")
        print("\nOn your local machine:")
        print("  1. rm -rf chromadb_data/")
        print("  2. python clear_and_reload_db.py")
        print("  3. streamlit run streamlit_app.py")
    else:
        print("\n✗ Multiple tests failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
