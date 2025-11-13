#!/usr/bin/env python3
"""
Comprehensive framework tests.

Tests all components to ensure framework works correctly.
"""

import os
import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def print_test(name, passed, message=""):
    """Print test result."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if message:
        print(f"      {message}")


def test_file_structure():
    """Test that all required files exist."""
    print("\n" + "=" * 80)
    print("TEST: File Structure")
    print("=" * 80)

    required_files = [
        "config.yaml",
        "llm_client.py",
        "stacktrace_parser.py",
        "vector_store.py",
        "server_new.py",
        "streamlit_app_new.py",
        "ingest.py",
        "generate_sample_data.py",
        "requirements.txt",
        "data/exceptions.csv"
    ]

    all_exist = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        print_test(f"File exists: {file_path}", exists)
        all_exist = all_exist and exists

    return all_exist


def test_config_loading():
    """Test configuration loading."""
    print("\n" + "=" * 80)
    print("TEST: Configuration Loading")
    print("=" * 80)

    try:
        import yaml
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        # Check required keys
        required_keys = ['project', 'database', 'azure_openai', 'vector_db', 'schema']
        all_keys_present = all(key in config for key in required_keys)

        print_test("Config file loads", True)
        print_test("Required keys present", all_keys_present,
                  f"Keys: {', '.join(required_keys)}")

        # Check schema
        has_schema = 'trade_ingestion_exception' in config['schema']
        print_test("Schema defined", has_schema)

        return all_keys_present and has_schema

    except Exception as e:
        print_test("Config file loads", False, str(e))
        return False


def test_csv_data():
    """Test CSV data loading."""
    print("\n" + "=" * 80)
    print("TEST: CSV Data")
    print("=" * 80)

    try:
        import csv

        csv_path = Path("data/exceptions.csv")
        if not csv_path.exists():
            print_test("CSV file exists", False)
            return False

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        total_count = len(rows)
        closed_count = sum(1 for row in rows if row.get('status') == 'CLOSED')
        open_count = sum(1 for row in rows if row.get('status') == 'OPEN')
        with_remarks = sum(1 for row in rows if row.get('remarks'))

        print_test("CSV file loads", True, f"{total_count} records")
        print_test("Has CLOSED exceptions", closed_count > 0, f"{closed_count} CLOSED")
        print_test("Has OPEN exceptions", open_count > 0, f"{open_count} OPEN")
        print_test("Has remarks", with_remarks > 0, f"{with_remarks} with remarks")

        # Check required fields
        required_fields = [
            'exception_id', 'error_message', 'exception_type',
            'exception_category', 'status', 'trace'
        ]

        if rows:
            first_row = rows[0]
            all_fields = all(field in first_row for field in required_fields)
            print_test("Required fields present", all_fields,
                      f"Fields: {', '.join(required_fields)}")
        else:
            print_test("CSV has data", False)
            return False

        return total_count > 0 and closed_count > 0

    except Exception as e:
        print_test("CSV data loads", False, str(e))
        return False


def test_stacktrace_parser():
    """Test stacktrace parser."""
    print("\n" + "=" * 80)
    print("TEST: Stacktrace Parser")
    print("=" * 80)

    try:
        from stacktrace_parser import StackTraceParser

        # Test case
        trace = """java.lang.NullPointerException: Cannot invoke method
\tat com.trading.service.TradeService.process(TradeService.java:45)
\tat com.trading.handler.Handler.handle(Handler.java:23)"""

        result = StackTraceParser.parse(trace)

        print_test("Parser imports", True)
        print_test("Parses error class", result['error_class'] == 'java.lang.NullPointerException')
        print_test("Extracts method chain", len(result['method_chain']) > 0,
                  f"Found {len(result['method_chain'])} methods")
        print_test("Identifies entry point", result['entry_point'] is not None,
                  f"Entry: {result['entry_point']}")

        return True

    except Exception as e:
        print_test("Stacktrace parser", False, str(e))
        return False


def test_llm_client_structure():
    """Test LLM client structure (without making actual API calls)."""
    print("\n" + "=" * 80)
    print("TEST: LLM Client Structure")
    print("=" * 80)

    try:
        from llm_client import AzureOpenAIClient

        # Check class exists and has required methods
        required_methods = [
            'chat_completion',
            'generate_embedding',
            'generate_embeddings_batch',
            'analyze_exception'
        ]

        all_methods_exist = all(hasattr(AzureOpenAIClient, method) for method in required_methods)

        print_test("LLM client imports", True)
        print_test("Has required methods", all_methods_exist,
                  f"Methods: {', '.join(required_methods)}")

        # Check initialization works
        client = AzureOpenAIClient(
            endpoint="https://test.openai.azure.com/",
            api_key="test-key"
        )
        print_test("Client initializes", True)

        return all_methods_exist

    except Exception as e:
        print_test("LLM client structure", False, str(e))
        return False


def test_vector_store_structure():
    """Test vector store structure (without vector DB)."""
    print("\n" + "=" * 80)
    print("TEST: Vector Store Structure")
    print("=" * 80)

    try:
        from vector_store import ExceptionVectorStore

        required_methods = [
            'add_exception',
            'add_exceptions_batch',
            'find_similar',
            'count',
            'clear'
        ]

        all_methods_exist = all(hasattr(ExceptionVectorStore, method) for method in required_methods)

        print_test("Vector store imports", True)
        print_test("Has required methods", all_methods_exist,
                  f"Methods: {', '.join(required_methods)}")

        return all_methods_exist

    except Exception as e:
        print_test("Vector store structure", False, str(e))
        return False


def test_environment_variables():
    """Test environment variables."""
    print("\n" + "=" * 80)
    print("TEST: Environment Variables")
    print("=" * 80)

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")

    print_test("AZURE_OPENAI_ENDPOINT set", endpoint is not None,
              f"Value: {endpoint[:30]}..." if endpoint else "Not set")
    print_test("AZURE_OPENAI_KEY set", api_key is not None,
              "Value: ****" if api_key else "Not set")

    if not endpoint or not api_key:
        print(f"\n{YELLOW}⚠ WARNING: Azure OpenAI credentials not set{RESET}")
        print("  AI features will not work until you set:")
        print("    export AZURE_OPENAI_ENDPOINT='your-endpoint'")
        print("    export AZURE_OPENAI_KEY='your-key'")

    return endpoint is not None and api_key is not None


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("EXCEPTION ANALYSIS FRAMEWORK - TEST SUITE")
    print("=" * 80)

    results = {}

    # Run tests
    results['file_structure'] = test_file_structure()
    results['config_loading'] = test_config_loading()
    results['csv_data'] = test_csv_data()
    results['stacktrace_parser'] = test_stacktrace_parser()
    results['llm_client_structure'] = test_llm_client_structure()
    results['vector_store_structure'] = test_vector_store_structure()
    results['environment_variables'] = test_environment_variables()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{status} - {test_name}")

    print("=" * 80)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print(f"{GREEN}✓ All tests passed!{RESET}")
        return 0
    else:
        print(f"{RED}✗ Some tests failed{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
