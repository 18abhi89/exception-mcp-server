#!/usr/bin/env python3
"""
Test the simplified, production-grade analysis output.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server import get_high_retry_exceptions, analyze_exception_with_history, load_exception_history, exception_db

print("=" * 70)
print("TESTING PRODUCTION-GRADE ANALYSIS")
print("=" * 70)

# Load historical data
print("\n1. Loading historical data...")
load_exception_history()
print(f"   Historical records: {exception_db.count()}")

# Get a test exception
print("\n2. Getting test exception...")
exceptions = get_high_retry_exceptions(threshold=0)
if not exceptions:
    print("   ✗ No exceptions found")
    sys.exit(1)

test_exception = exceptions[1]  # EVT-006 - validation error
print(f"   Selected: {test_exception['event_id']}")
print(f"   Error: {test_exception['error_message'][:60]}...")
print(f"   Category: {test_exception['exception_category']}")
print(f"   Times replayed: {test_exception['times_replayed']}")

# Analyze
print("\n3. Analyzing exception...")
print("=" * 70)

try:
    analysis = analyze_exception_with_history(test_exception)
    print(analysis)
    print("=" * 70)

    # Verify output structure
    print("\n4. Verifying analysis structure...")

    checks = [
        ("Root Cause Analysis", "Root Cause Analysis" in analysis),
        ("Category-specific explanation", "Error" in analysis and ("VALIDATION" in analysis or "SEQUENCING" in analysis)),
        ("Similar cases section", "Similar Historical Cases" in analysis),
        ("Recommended Action", "Recommended Action" in analysis),
        ("No duplicates", analysis.count("Similar Historical Cases") == 1)
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ Analysis is clean and production-grade!")
    else:
        print("\n⚠ Some checks failed")

except Exception as e:
    print(f"✗ Analysis failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ TEST COMPLETE")
print("=" * 70)
