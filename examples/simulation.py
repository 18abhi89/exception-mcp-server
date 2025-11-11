#!/usr/bin/env python3
"""
Simulation program to test exception handling scenarios.
This program loads synthetic test data and validates various exception scenarios.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class ExceptionSimulator:
    """Simulates exception handling scenarios for the MCP server."""

    def __init__(self, test_data_path: str):
        """Initialize simulator with test data."""
        self.test_data_path = Path(test_data_path)
        self.test_data = None
        self.results = {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "details": []
        }

    def load_test_data(self) -> bool:
        """Load test data from JSON file."""
        try:
            with open(self.test_data_path, 'r') as f:
                self.test_data = json.load(f)
            print(f"✓ Loaded test data from {self.test_data_path}")
            return True
        except FileNotFoundError:
            print(f"✗ Error: Test data file not found at {self.test_data_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"✗ Error: Invalid JSON in test data file: {e}")
            return False

    def validate_schema(self) -> bool:
        """Validate that test data matches expected schema."""
        print("\n=== Validating Test Data Schema ===")

        required_fields = ['id', 'event_id', 'exception_sub_category', 'status', 'error_message', 'times_replayed']
        valid_sub_categories = ['OUT_OF_ORDER', 'INVALID_EVENT', 'PREVIOUSLY_PROCESSED_MESSAGE']
        valid_statuses = ['OPEN', 'CLOSED']

        all_valid = True

        for exception_category in self.test_data['exceptions']:
            category = exception_category['category']
            print(f"\nValidating {category} scenarios:")

            for scenario in exception_category['scenarios']:
                scenario_id = scenario.get('id', 'unknown')

                # Check required fields
                missing_fields = [field for field in required_fields if field not in scenario]
                if missing_fields:
                    print(f"  ✗ Scenario {scenario_id}: Missing fields {missing_fields}")
                    all_valid = False
                    continue

                # Validate sub_category
                if scenario['exception_sub_category'] not in valid_sub_categories:
                    print(f"  ✗ Scenario {scenario_id}: Invalid sub_category '{scenario['exception_sub_category']}'")
                    all_valid = False
                    continue

                # Validate status
                if scenario['status'] not in valid_statuses:
                    print(f"  ✗ Scenario {scenario_id}: Invalid status '{scenario['status']}'")
                    all_valid = False
                    continue

                # Validate data types
                if not isinstance(scenario['times_replayed'], int) or scenario['times_replayed'] < 0:
                    print(f"  ✗ Scenario {scenario_id}: Invalid times_replayed value")
                    all_valid = False
                    continue

                print(f"  ✓ Scenario {scenario_id} ({scenario['event_id']}): Valid")

        if all_valid:
            print(f"\n✓ All scenarios passed schema validation")
        else:
            print(f"\n✗ Some scenarios failed schema validation")

        return all_valid

    def simulate_out_of_order_scenarios(self) -> None:
        """Simulate OUT_OF_ORDER exception scenarios."""
        print("\n=== Simulating OUT_OF_ORDER Scenarios ===")

        scenarios = next((cat['scenarios'] for cat in self.test_data['exceptions']
                         if cat['category'] == 'OUT_OF_ORDER'), [])

        for scenario in scenarios:
            self.results['total'] += 1
            scenario_id = scenario['id']
            event_id = scenario['event_id']

            try:
                # Simulate checking for out of order conditions
                error_msg = scenario['error_message'].lower()

                # Validate typical out-of-order patterns
                valid_patterns = ['cancel before new', 'version', 'not found', 'non-existent', 'before']
                has_valid_pattern = any(pattern in error_msg for pattern in valid_patterns)

                if has_valid_pattern:
                    print(f"  ✓ Scenario {scenario_id} ({event_id}): OUT_OF_ORDER pattern validated")
                    print(f"    Status: {scenario['status']}, Replays: {scenario['times_replayed']}")
                    self.results['passed'] += 1
                    self.results['details'].append({
                        'scenario_id': scenario_id,
                        'category': 'OUT_OF_ORDER',
                        'status': 'PASSED'
                    })
                else:
                    raise ValueError(f"No valid OUT_OF_ORDER pattern found in error message")

            except Exception as e:
                print(f"  ✗ Scenario {scenario_id} ({event_id}): Failed - {str(e)}")
                self.results['failed'] += 1
                self.results['details'].append({
                    'scenario_id': scenario_id,
                    'category': 'OUT_OF_ORDER',
                    'status': 'FAILED',
                    'error': str(e)
                })

    def simulate_invalid_event_scenarios(self) -> None:
        """Simulate INVALID_EVENT exception scenarios."""
        print("\n=== Simulating INVALID_EVENT Scenarios ===")

        scenarios = next((cat['scenarios'] for cat in self.test_data['exceptions']
                         if cat['category'] == 'INVALID_EVENT'), [])

        for scenario in scenarios:
            self.results['total'] += 1
            scenario_id = scenario['id']
            event_id = scenario['event_id']

            try:
                # Simulate checking for invalid event conditions
                error_msg = scenario['error_message'].lower()

                # Validate typical invalid event patterns
                valid_patterns = ['unsupported', 'invalid', 'schema', 'missing', 'null', 'empty', 'unexpected']
                has_valid_pattern = any(pattern in error_msg for pattern in valid_patterns)

                if has_valid_pattern:
                    print(f"  ✓ Scenario {scenario_id} ({event_id}): INVALID_EVENT pattern validated")
                    print(f"    Status: {scenario['status']}, Replays: {scenario['times_replayed']}")
                    self.results['passed'] += 1
                    self.results['details'].append({
                        'scenario_id': scenario_id,
                        'category': 'INVALID_EVENT',
                        'status': 'PASSED'
                    })
                else:
                    raise ValueError(f"No valid INVALID_EVENT pattern found in error message")

            except Exception as e:
                print(f"  ✗ Scenario {scenario_id} ({event_id}): Failed - {str(e)}")
                self.results['failed'] += 1
                self.results['details'].append({
                    'scenario_id': scenario_id,
                    'category': 'INVALID_EVENT',
                    'status': 'FAILED',
                    'error': str(e)
                })

    def simulate_previously_processed_scenarios(self) -> None:
        """Simulate PREVIOUSLY_PROCESSED_MESSAGE exception scenarios."""
        print("\n=== Simulating PREVIOUSLY_PROCESSED_MESSAGE Scenarios ===")

        scenarios = next((cat['scenarios'] for cat in self.test_data['exceptions']
                         if cat['category'] == 'PREVIOUSLY_PROCESSED_MESSAGE'), [])

        for scenario in scenarios:
            self.results['total'] += 1
            scenario_id = scenario['id']
            event_id = scenario['event_id']

            try:
                # Simulate checking for duplicate message conditions
                error_msg = scenario['error_message'].lower()

                # Validate typical duplicate message patterns
                valid_patterns = ['duplicate', 'already processed', 'already exists', 'replay', 'idempotency']
                has_valid_pattern = any(pattern in error_msg for pattern in valid_patterns)

                if has_valid_pattern:
                    print(f"  ✓ Scenario {scenario_id} ({event_id}): PREVIOUSLY_PROCESSED pattern validated")
                    print(f"    Status: {scenario['status']}, Replays: {scenario['times_replayed']}")
                    self.results['passed'] += 1
                    self.results['details'].append({
                        'scenario_id': scenario_id,
                        'category': 'PREVIOUSLY_PROCESSED_MESSAGE',
                        'status': 'PASSED'
                    })
                else:
                    raise ValueError(f"No valid PREVIOUSLY_PROCESSED pattern found in error message")

            except Exception as e:
                print(f"  ✗ Scenario {scenario_id} ({event_id}): Failed - {str(e)}")
                self.results['failed'] += 1
                self.results['details'].append({
                    'scenario_id': scenario_id,
                    'category': 'PREVIOUSLY_PROCESSED_MESSAGE',
                    'status': 'FAILED',
                    'error': str(e)
                })

    def analyze_patterns(self) -> None:
        """Analyze patterns across all scenarios."""
        print("\n=== Pattern Analysis ===")

        status_counts = defaultdict(int)
        replay_stats = {'min': float('inf'), 'max': 0, 'total': 0, 'count': 0}

        for exception_category in self.test_data['exceptions']:
            for scenario in exception_category['scenarios']:
                status_counts[scenario['status']] += 1

                replays = scenario['times_replayed']
                replay_stats['min'] = min(replay_stats['min'], replays)
                replay_stats['max'] = max(replay_stats['max'], replays)
                replay_stats['total'] += replays
                replay_stats['count'] += 1

        print(f"\nStatus Distribution:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

        avg_replays = replay_stats['total'] / replay_stats['count'] if replay_stats['count'] > 0 else 0
        print(f"\nReplay Statistics:")
        print(f"  Min: {replay_stats['min']}")
        print(f"  Max: {replay_stats['max']}")
        print(f"  Average: {avg_replays:.2f}")

    def print_summary(self) -> None:
        """Print test execution summary."""
        print("\n" + "="*60)
        print("SIMULATION SUMMARY")
        print("="*60)
        print(f"Total Scenarios: {self.results['total']}")
        print(f"Passed: {self.results['passed']} ✓")
        print(f"Failed: {self.results['failed']} ✗")

        if self.results['total'] > 0:
            success_rate = (self.results['passed'] / self.results['total']) * 100
            print(f"Success Rate: {success_rate:.1f}%")

        print("="*60)

        # Show data summary
        summary = self.test_data.get('summary', {})
        print(f"\nTest Data Summary:")
        print(f"  Total Exceptions: {summary.get('total_exceptions', 0)}")
        print(f"  By Category: {summary.get('by_category', {})}")
        print(f"  By Status: {summary.get('by_status', {})}")

        if self.results['failed'] > 0:
            print("\n⚠ Some scenarios failed. Review the output above for details.")
            return False
        else:
            print("\n✓ All scenarios passed successfully!")
            return True

    def run(self) -> bool:
        """Run the complete simulation."""
        print("="*60)
        print("EXCEPTION MCP SERVER - TEST SIMULATION")
        print("="*60)

        # Load and validate test data
        if not self.load_test_data():
            return False

        if not self.validate_schema():
            return False

        # Run simulations for each category
        self.simulate_out_of_order_scenarios()
        self.simulate_invalid_event_scenarios()
        self.simulate_previously_processed_scenarios()

        # Analyze patterns
        self.analyze_patterns()

        # Print summary
        return self.print_summary()


def main():
    """Main entry point."""
    test_data_path = Path(__file__).parent.parent / "data" / "test_data.json"

    simulator = ExceptionSimulator(test_data_path)
    success = simulator.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
