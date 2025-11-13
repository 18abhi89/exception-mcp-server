"""
Stack Trace Parser

Extracts method chains and metadata from Java stack traces.
"""

import re
from typing import List, Dict, Any, Optional


class StackTraceParser:
    """Parse Java stack traces to extract method chains and metadata."""

    @staticmethod
    def parse(stacktrace: str, max_depth: int = 10) -> Dict[str, Any]:
        """
        Parse Java stack trace and extract key information.

        Args:
            stacktrace: Full stack trace text
            max_depth: Maximum depth of call chain to extract

        Returns:
            Dict with parsed information:
            {
                "error_class": "java.lang.NullPointerException",
                "error_message": "Cannot invoke method on null object",
                "method_chain": ["Class.method", ...],
                "entry_point": "TopClass.method",
                "package_root": "com.trading",
                "file_locations": ["File.java:45", ...],
                "full_methods": ["com.trading.Class.method", ...]
            }

        Example:
            trace = '''
            java.lang.NullPointerException: Cannot invoke method
                at com.trading.service.TradeService.process(TradeService.java:45)
                at com.trading.handler.Handler.handle(Handler.java:23)
            '''
            result = StackTraceParser.parse(trace)
        """
        if not stacktrace or not stacktrace.strip():
            return {
                "error_class": "Unknown",
                "error_message": "",
                "method_chain": [],
                "entry_point": None,
                "package_root": None,
                "file_locations": [],
                "full_methods": []
            }

        lines = stacktrace.strip().split('\n')

        # Extract error class and message from first line
        first_line = lines[0].strip()
        error_class = "Unknown"
        error_message = ""

        if ':' in first_line:
            parts = first_line.split(':', 1)
            error_class = parts[0].strip()
            error_message = parts[1].strip() if len(parts) > 1 else ""
        else:
            error_class = first_line

        # Extract method calls from stack trace
        method_chain = []
        full_methods = []
        file_locations = []
        package_root = None

        # Regex to match Java stack trace lines:
        # at com.example.package.ClassName.methodName(FileName.java:123)
        stack_pattern = re.compile(
            r'\s*at\s+'                           # "at" keyword
            r'([\w.$]+)'                          # Full qualified method
            r'\('                                  # Opening parenthesis
            r'([^:)]+)'                           # File name
            r'(?::(\d+))?'                        # Optional line number
            r'\)'                                  # Closing parenthesis
        )

        for line in lines[1:]:  # Skip first line (error message)
            # Stop at "... N more" lines
            if '...' in line and 'more' in line.lower():
                break

            match = stack_pattern.match(line)
            if match and len(method_chain) < max_depth:
                full_method = match.group(1)
                file_name = match.group(2)
                line_number = match.group(3)

                full_methods.append(full_method)

                # Extract short method name (Class.method)
                parts = full_method.split('.')
                if len(parts) >= 2:
                    short_method = f"{parts[-2]}.{parts[-1]}"
                    method_chain.append(short_method)

                    # Extract package root from first method
                    if not package_root and len(parts) >= 3:
                        package_root = '.'.join(parts[:2])  # e.g., "com.trading"

                # Store file location
                if line_number:
                    file_locations.append(f"{file_name}:{line_number}")
                else:
                    file_locations.append(file_name)

        # Entry point is the first method in the chain
        entry_point = method_chain[0] if method_chain else None

        return {
            "error_class": error_class,
            "error_message": error_message,
            "method_chain": method_chain,
            "entry_point": entry_point,
            "package_root": package_root,
            "file_locations": file_locations,
            "full_methods": full_methods
        }

    @staticmethod
    def extract_method_names(stacktrace: str, max_depth: int = 10) -> List[str]:
        """
        Quick method to extract just the method names.

        Args:
            stacktrace: Stack trace text
            max_depth: Maximum methods to extract

        Returns:
            List of method names (e.g., ["Class.method", ...])
        """
        result = StackTraceParser.parse(stacktrace, max_depth)
        return result["method_chain"]

    @staticmethod
    def get_call_signature(stacktrace: str) -> str:
        """
        Get a unique signature for this call chain.

        Useful for grouping similar exceptions.

        Args:
            stacktrace: Stack trace text

        Returns:
            Call signature string (e.g., "ClassA.method1->ClassB.method2->ClassC.method3")
        """
        result = StackTraceParser.parse(stacktrace)
        if result["method_chain"]:
            return "->".join(result["method_chain"])
        return ""


def test_parser():
    """Test the stack trace parser."""

    # Test case 1: NullPointerException
    trace1 = """java.lang.NullPointerException: Cannot invoke getCounterparty() on null object
\tat com.trading.validation.TradeValidator.validateCounterparty(TradeValidator.java:112)
\tat com.trading.service.TradeService.processTrade(TradeService.java:67)
\tat com.trading.kafka.MessageHandler.handleMessage(MessageHandler.java:34)
\tat com.trading.kafka.KafkaConsumer.poll(KafkaConsumer.java:89)"""

    print("Test 1: NullPointerException")
    result1 = StackTraceParser.parse(trace1)
    print(f"Error Class: {result1['error_class']}")
    print(f"Error Message: {result1['error_message']}")
    print(f"Method Chain: {result1['method_chain']}")
    print(f"Entry Point: {result1['entry_point']}")
    print(f"Package Root: {result1['package_root']}")
    print(f"Call Signature: {StackTraceParser.get_call_signature(trace1)}")
    print()

    # Test case 2: Timeout exception
    trace2 = """java.sql.SQLTimeoutException: Connection timed out
\tat com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:197)
\tat com.trading.repository.TradeRepository.findById(TradeRepository.java:45)
\tat com.trading.service.TradeService.getTrade(TradeService.java:89)
\tat com.trading.controller.TradeController.getTradeById(TradeController.java:34)
... 15 more"""

    print("Test 2: SQLTimeoutException")
    result2 = StackTraceParser.parse(trace2, max_depth=5)
    print(f"Error Class: {result2['error_class']}")
    print(f"Method Chain: {result2['method_chain']}")
    print(f"File Locations: {result2['file_locations']}")
    print()

    # Test case 3: Empty trace
    trace3 = ""
    print("Test 3: Empty trace")
    result3 = StackTraceParser.parse(trace3)
    print(f"Error Class: {result3['error_class']}")
    print(f"Method Chain: {result3['method_chain']}")
    print()


if __name__ == "__main__":
    test_parser()
