#!/usr/bin/env python3
"""
Test the dropdown fix.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server import get_high_retry_exceptions

print("=" * 70)
print("TESTING DROPDOWN FIX")
print("=" * 70)

# Test with threshold=0 (should get ALL exceptions now)
print("\n1. Testing threshold=0 (ALL exceptions):")
all_exceptions = get_high_retry_exceptions(threshold=0)
print(f"   Found: {len(all_exceptions)} exceptions")

expected_count = 10  # We know there are 10 in the CSV
if len(all_exceptions) == expected_count:
    print(f"   ✓ CORRECT! Got all {expected_count} exceptions")
else:
    print(f"   ✗ WRONG! Expected {expected_count} but got {len(all_exceptions)}")

print("\n   Exceptions in dropdown:")
for i, exc in enumerate(all_exceptions, 1):
    event_id = exc.get('event_id', 'N/A')
    times_replayed = exc.get('times_replayed', '0')
    error_msg = exc.get('error_message', 'N/A')[:50]
    print(f"   {i:2d}. {event_id} (replays: {times_replayed:2s}) - {error_msg}...")

# Test with threshold=5 (high retry exceptions)
print("\n2. Testing threshold=5 (high retry exceptions):")
high_retry = get_high_retry_exceptions(threshold=5)
print(f"   Found: {len(high_retry)} exceptions")

for exc in high_retry:
    event_id = exc.get('event_id', 'N/A')
    times_replayed = exc.get('times_replayed', '0')
    print(f"   - {event_id}: {times_replayed} retries")

# Verify: should include exceptions with times_replayed >= 5
expected_high_retry = ['EVT-006', 'EVT-007', 'EVT-004', 'EVT-020']  # 6,7,8,9 retries
found_event_ids = [exc['event_id'] for exc in high_retry]

print(f"\n   Expected: {expected_high_retry}")
print(f"   Got: {found_event_ids}")

if set(found_event_ids) == set(expected_high_retry):
    print("   ✓ CORRECT!")
else:
    print("   ✗ MISMATCH!")

print("\n" + "=" * 70)
print("✓ TEST COMPLETE")
print("=" * 70)
