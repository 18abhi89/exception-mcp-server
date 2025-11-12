#!/usr/bin/env python3
"""
Test CSV reading only (no ChromaDB).
"""
import csv
from pathlib import Path

print("=" * 70)
print("TESTING CSV DATA FOR DROPDOWNS")
print("=" * 70)

# Test current exceptions (what shows in dropdown)
exceptions_csv = Path(__file__).parent / "data" / "exceptions.csv"

print(f"\n1. Reading: {exceptions_csv}")
print(f"   Exists: {exceptions_csv.exists()}")

with open(exceptions_csv, 'r') as f:
    reader = csv.DictReader(f)
    exceptions = list(reader)

print(f"   Total rows: {len(exceptions)}")

print("\n2. All exceptions that should appear in dropdown:")
print(f"   (threshold=0 means get ALL exceptions)")
print()

for i, exc in enumerate(exceptions, 1):
    event_id = exc.get('event_id', 'N/A')
    error_msg = exc.get('error_message', 'N/A')[:60]
    times_replayed = exc.get('times_replayed', '0')
    status = exc.get('status', 'N/A')
    exception_id = exc.get('exception_id', 'N/A')[:30]

    print(f"{i:2d}. Event: {event_id:10s} | Replays: {times_replayed:2s} | Status: {status:6s}")
    print(f"    Error: {error_msg}")
    print(f"    ID: {exception_id}...")
    print()

# Test high retry exceptions (threshold > 5)
print("\n3. Exceptions with times_replayed > 5:")
high_retry = [exc for exc in exceptions if int(exc.get('times_replayed', 0)) > 5]
print(f"   Found: {len(high_retry)}")
for exc in high_retry:
    print(f"   - {exc['event_id']}: {exc['times_replayed']} retries")

print("\n" + "=" * 70)
print(f"SUMMARY: {len(exceptions)} exceptions total")
print("=" * 70)
