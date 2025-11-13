"""
Exception Analysis MCP Server

Provides tools and resources for analyzing trade ingestion exceptions.
"""

import asyncio
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

from exception_db import ExceptionDB

# Constants
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
EXCEPTIONS_CSV = DATA_DIR / "exceptions.csv"
EXCEPTION_HISTORY_CSV = DATA_DIR / "exception_history.csv"
EXCEPTION_GUIDE = DOCS_DIR / "exception_guide.md"
EVENT_SCHEMA = DOCS_DIR / "event_schema.json"

app = Server("exception-analysis-server")

# Initialize Exception Database
exception_db = ExceptionDB()


def load_schema_from_csv() -> str:
    """
    Load exception schema from CSV file.

    Returns:
        Formatted schema string with table structure and valid values
    """
    try:
        # Read CSV to get column names
        with open(EXCEPTIONS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return "Error: CSV file is empty"

        # Build schema based on actual data
        schema = """Table: exception_events

Columns:
- id (BIGSERIAL, Primary Key)
- created_date (TIMESTAMP)
- destination (VARCHAR(255)) - Target topic/destination
- error_message (TEXT) - Detailed error message
- event_id (VARCHAR(255)) - Unique event identifier
- event_id_type (VARCHAR(50)) - Type of event ID (e.g., UUID)
- event_type (VARCHAR(255)) - Type of event (NEW, MODIFY, CANCEL, DELETE)
- event_version (INTEGER) - Version of the event
- exception_category (VARCHAR(255)) - High-level category
  Values: SEQUENCING, VALIDATION, DUPLICATE, BUSINESS_LOGIC, INFRASTRUCTURE
- exception_sub_category (VARCHAR(255)) - Specific sub-category
  Values: OUT_OF_ORDER, INVALID_EVENT, PREVIOUSLY_PROCESSED_MESSAGE, CALCULATION_ERROR, TIMEOUT
- exception_type (VARCHAR(255)) - Java exception class name
- host (VARCHAR(255)) - Host where exception occurred
- is_active (BOOLEAN) - Whether exception is still active
- messaging_platform_type (VARCHAR(255)) - Platform type (e.g., KAFKA)
- raising_system (VARCHAR(255)) - System that raised the exception
  Values: trade-ingestion-service, trade-consumer-service
- source_system (VARCHAR(255)) - Original source system
  Values: ATLAS, trade-ingestion-service
- status (VARCHAR(255)) - Current status
  Values: OPEN, CLOSED
- times_replayed (INTEGER) - Number of retry attempts
- updated_date (TIMESTAMP) - Last update timestamp
- updated_by (VARCHAR(255)) - User/system that updated
- comment (TEXT) - Additional comments
- trace (TEXT) - Stack trace
- payload (TEXT) - Message payload (JSON)
- exception_id (UUID) - Unique exception identifier
"""
        return schema.strip()

    except FileNotFoundError:
        return f"Error: Schema file not found at {EXCEPTIONS_CSV}"
    except Exception as e:
        return f"Error loading schema: {str(e)}"


def load_exception_history() -> None:
    """Load exception history into ChromaDB if not already loaded."""
    if exception_db.count() == 0 and EXCEPTION_HISTORY_CSV.exists():
        count = exception_db.load_from_csv(str(EXCEPTION_HISTORY_CSV))
        print(f"Loaded {count} historical exceptions into database")


def get_high_retry_exceptions(threshold: int = 5) -> List[Dict[str, Any]]:
    """Get exceptions with retry count above or equal to threshold."""
    exceptions = []
    try:
        with open(EXCEPTIONS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row.get('times_replayed', 0)) >= threshold:
                    exceptions.append(row)
    except Exception as e:
        print(f"Error reading exceptions: {e}")

    return exceptions


def analyze_exception_with_history(exception: Dict[str, Any]) -> str:
    """Analyze an exception using historical data and patterns."""
    error_message = exception.get('error_message', '')
    exception_type = exception.get('exception_type', '')
    exception_category = exception.get('exception_category', '')
    exception_sub_category = exception.get('exception_sub_category', '')
    stacktrace = exception.get('trace', '')
    times_replayed = int(exception.get('times_replayed', 0))

    # Find similar exceptions
    similar = exception_db.find_similar(
        error_message=error_message,
        exception_type=exception_type,
        exception_category=exception_category,
        exception_sub_category=exception_sub_category,
        stacktrace=stacktrace,
        n_results=3
    )

    # Build clean, production-grade analysis
    analysis = f"""### Root Cause Analysis

**Why it's failing after {times_replayed} retries:**

"""

    # Category-specific root cause
    if exception_category == "VALIDATION":
        analysis += "❌ **VALIDATION Error** - Data or schema issue that retries cannot fix.\n"
        analysis += "The incoming data is malformed or doesn't match the expected schema. "
        analysis += "Retrying will not resolve this - the source data or validation rules must be corrected.\n\n"
    elif exception_category == "SEQUENCING":
        analysis += "⚠️ **SEQUENCING Error** - Out-of-order message delivery.\n"
        analysis += "Messages are arriving in the wrong sequence (e.g., DELETE before NEW). "
        analysis += "Retries may not help if dependent messages haven't arrived. Consider temporal parking/delayed retry.\n\n"
    elif exception_category == "BUSINESS_LOGIC":
        analysis += "🔧 **BUSINESS LOGIC Error** - Configuration or reference data issue.\n"
        analysis += "Business rules are being violated due to missing configuration or stale reference data. "
        analysis += "Retries won't help - update configuration or refresh reference data.\n\n"
    else:
        analysis += f"Error Category: {exception_category}\n"
        analysis += "Investigate the specific error type and context for root cause.\n\n"

    # Similar cases with resolutions
    if similar:
        analysis += "### Similar Historical Cases & Resolutions\n\n"
        for i, sim in enumerate(similar, 1):
            metadata = sim.get('metadata', {})
            resolution = metadata.get('resolution', 'No resolution recorded')
            similarity = (1 - sim['distance']) * 100

            analysis += f"**{i}. {metadata.get('exception_type', 'N/A')}** ({similarity:.0f}% match)\n"
            analysis += f"**Resolution:** {resolution}\n\n"

        analysis += "\n### Recommended Action\n"
        analysis += "Stop retrying this exception. Apply the resolution from the most similar case above.\n"
    else:
        analysis += "### Similar Historical Cases\n"
        analysis += "No similar cases found. This appears to be a new type of exception.\n\n"
        analysis += "### Recommended Action\n"
        analysis += f"1. Investigate the {exception_category} error in detail\n"
        analysis += "2. Document the resolution for future reference\n"
        analysis += "3. Add to exception history once resolved\n"

    return analysis


def query_exceptions(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Query exceptions with optional filters."""
    exceptions = []
    try:
        with open(EXCEPTIONS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Apply filters
                if 'status' in filters and row.get('status') != filters['status']:
                    continue
                if 'exception_category' in filters and row.get('exception_category') != filters['exception_category']:
                    continue
                if 'exception_sub_category' in filters and row.get('exception_sub_category') != filters['exception_sub_category']:
                    continue
                if 'event_id' in filters and row.get('event_id') != filters['event_id']:
                    continue
                if 'min_replays' in filters and int(row.get('times_replayed', 0)) < filters['min_replays']:
                    continue

                exceptions.append(row)
    except Exception as e:
        print(f"Error querying exceptions: {e}")

    return exceptions


def get_exception_by_id(exception_id: str) -> Dict[str, Any] | None:
    """Get a specific exception by its ID."""
    try:
        with open(EXCEPTIONS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('exception_id') == exception_id:
                    return row
    except Exception as e:
        print(f"Error reading exception: {e}")

    return None


def get_valid_event_types() -> Dict[str, Any]:
    """Return valid event types and rules."""
    return {
        "valid_event_types": ["NEW", "MODIFY", "CANCEL", "DELETE"],
        "description": "These are the only supported event types for trade ingestion",
        "common_invalid_types": ["TRANSFER", "UPDATE", "CREATE", "REMOVE"],
        "event_type_rules": {
            "NEW": "Creates a new trade record - must be version 1",
            "MODIFY": "Updates an existing trade - requires existing trade, sequential version",
            "CANCEL": "Cancels an existing trade - requires existing trade",
            "DELETE": "Removes a trade record - requires existing trade"
        }
    }


def find_related_exceptions(search_term: str) -> List[Dict[str, Any]]:
    """Find exceptions related to a search term."""
    related = []
    try:
        with open(EXCEPTIONS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (search_term in row.get('event_id', '') or
                    search_term in row.get('error_message', '') or
                    search_term in row.get('exception_id', '')):
                    related.append(row)
    except Exception as e:
        print(f"Error searching exceptions: {e}")

    return related


# Tools
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="getExceptionTableSchema",
            description="Get the schema of exception_events table",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="getHighRetryExceptions",
            description="Get exceptions where times_replayed exceeds threshold (default: 5)",
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "integer",
                        "description": "Minimum number of retries to filter by",
                        "default": 5
                    }
                }
            }
        ),
        Tool(
            name="findSimilarExceptions",
            description="Find similar historical exceptions using semantic search based on stacktrace and exception metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "error_message": {
                        "type": "string",
                        "description": "Error message to search for"
                    },
                    "exception_type": {
                        "type": "string",
                        "description": "Exception type (optional)",
                        "default": ""
                    },
                    "exception_category": {
                        "type": "string",
                        "description": "Exception category (optional)",
                        "default": ""
                    },
                    "exception_sub_category": {
                        "type": "string",
                        "description": "Exception sub-category (optional)",
                        "default": ""
                    },
                    "stacktrace": {
                        "type": "string",
                        "description": "Full stacktrace for better similarity matching (highly recommended for accurate results)",
                        "default": ""
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    }
                },
                "required": ["error_message"]
            }
        ),
        Tool(
            name="analyzeException",
            description="Analyze a specific exception and form thesis on why it's failing",
            inputSchema={
                "type": "object",
                "properties": {
                    "exception_id": {
                        "type": "string",
                        "description": "Exception UUID to analyze"
                    }
                },
                "required": ["exception_id"]
            }
        ),
        Tool(
            name="queryExceptions",
            description="Query exceptions with flexible filters (status, category, sub_category, event_id, min_replays)",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["OPEN", "CLOSED"],
                        "description": "Filter by status"
                    },
                    "exception_category": {
                        "type": "string",
                        "enum": ["SEQUENCING", "VALIDATION", "DUPLICATE", "BUSINESS_LOGIC", "INFRASTRUCTURE"],
                        "description": "Filter by exception category"
                    },
                    "exception_sub_category": {
                        "type": "string",
                        "enum": ["OUT_OF_ORDER", "INVALID_EVENT", "PREVIOUSLY_PROCESSED_MESSAGE", "CALCULATION_ERROR", "TIMEOUT"],
                        "description": "Filter by exception sub-category"
                    },
                    "event_id": {
                        "type": "string",
                        "description": "Filter by specific event_id"
                    },
                    "min_replays": {
                        "type": "integer",
                        "description": "Filter by minimum times_replayed"
                    }
                }
            }
        ),
        Tool(
            name="getExceptionById",
            description="Get detailed information for a specific exception by its UUID",
            inputSchema={
                "type": "object",
                "properties": {
                    "exception_id": {
                        "type": "string",
                        "description": "The exception UUID"
                    }
                },
                "required": ["exception_id"]
            }
        ),
        Tool(
            name="getValidEventTypes",
            description="Get list of valid event types and rules (useful for INVALID_EVENT investigation)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="findRelatedExceptions",
            description="Find exceptions related to a search term (searches event_id, error_message, exception_id)",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Search term to find in event_id, error_message, or exception_id"
                    }
                },
                "required": ["search_term"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    # Load exception history on first use
    load_exception_history()

    if name == "getExceptionTableSchema":
        schema = load_schema_from_csv()
        return [TextContent(type="text", text=schema)]

    elif name == "getHighRetryExceptions":
        threshold = arguments.get('threshold', 5)
        exceptions = get_high_retry_exceptions(threshold)

        if not exceptions:
            result = f"No exceptions found with times_replayed > {threshold}"
        else:
            result = f"Found {len(exceptions)} exception(s) with times_replayed > {threshold}:\n\n"
            for exc in exceptions:
                result += f"### Exception ID: {exc['exception_id']}\n"
                result += f"- Event ID: {exc['event_id']}\n"
                result += f"- Error: {exc['error_message']}\n"
                result += f"- Type: {exc['exception_type']}\n"
                result += f"- Category: {exc['exception_category']}\n"
                result += f"- Times Replayed: {exc['times_replayed']}\n"
                result += f"- Status: {exc['status']}\n"
                result += f"- Source: {exc['source_system']} → {exc['raising_system']}\n"
                result += f"- Comment: {exc.get('comment', 'None')}\n\n"

        return [TextContent(type="text", text=result)]

    elif name == "findSimilarExceptions":
        error_message = arguments.get('error_message', '')
        exception_type = arguments.get('exception_type', '')
        exception_category = arguments.get('exception_category', '')
        exception_sub_category = arguments.get('exception_sub_category', '')
        stacktrace = arguments.get('stacktrace', '')
        n_results = arguments.get('n_results', 5)

        similar = exception_db.find_similar(
            error_message=error_message,
            exception_type=exception_type,
            exception_category=exception_category,
            exception_sub_category=exception_sub_category,
            stacktrace=stacktrace,
            n_results=n_results
        )

        if not similar:
            result = "No similar exceptions found in historical data."
        else:
            result = f"Found {len(similar)} similar exception(s) based on stacktrace and metadata:\n\n"
            for i, sim in enumerate(similar, 1):
                metadata = sim.get('metadata', {})
                similarity_score = (1 - sim['distance']) * 100
                result += f"### Similar Case {i} (Similarity: {similarity_score:.1f}%)\n"
                result += f"- Exception Type: {metadata.get('exception_type', 'N/A')}\n"
                result += f"- Category: {metadata.get('exception_category', 'N/A')}\n"
                result += f"- Sub-Category: {metadata.get('exception_sub_category', 'N/A')}\n"
                result += f"- Resolution: {metadata.get('resolution', 'No resolution recorded')}\n"
                result += f"- Event ID: {metadata.get('event_id', 'N/A')}\n\n"

        return [TextContent(type="text", text=result)]

    elif name == "analyzeException":
        exception_id = arguments.get('exception_id', '')

        # Find the exception in current data
        exception = None
        try:
            with open(EXCEPTIONS_CSV, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('exception_id') == exception_id:
                        exception = row
                        break
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading exception data: {e}")]

        if not exception:
            return [TextContent(type="text", text=f"Exception with ID {exception_id} not found")]

        # Analyze the exception
        analysis = analyze_exception_with_history(exception)
        return [TextContent(type="text", text=analysis)]

    elif name == "queryExceptions":
        filters = {}
        if 'status' in arguments:
            filters['status'] = arguments['status']
        if 'exception_category' in arguments:
            filters['exception_category'] = arguments['exception_category']
        if 'exception_sub_category' in arguments:
            filters['exception_sub_category'] = arguments['exception_sub_category']
        if 'event_id' in arguments:
            filters['event_id'] = arguments['event_id']
        if 'min_replays' in arguments:
            filters['min_replays'] = arguments['min_replays']

        exceptions = query_exceptions(filters)

        if not exceptions:
            result = "No exceptions found matching the specified filters."
        else:
            result = f"Found {len(exceptions)} exception(s):\n\n"
            result += json.dumps(exceptions, indent=2)

        return [TextContent(type="text", text=result)]

    elif name == "getExceptionById":
        exception_id = arguments.get('exception_id', '')
        exception = get_exception_by_id(exception_id)

        if not exception:
            result = f"Exception with ID {exception_id} not found"
        else:
            result = f"Exception details:\n\n{json.dumps(exception, indent=2)}"

        return [TextContent(type="text", text=result)]

    elif name == "getValidEventTypes":
        valid_types = get_valid_event_types()
        result = f"Valid Event Types:\n\n{json.dumps(valid_types, indent=2)}"
        return [TextContent(type="text", text=result)]

    elif name == "findRelatedExceptions":
        search_term = arguments.get('search_term', '')
        related = find_related_exceptions(search_term)

        if not related:
            result = f"No exceptions found related to search term: '{search_term}'"
        else:
            result = f"Found {len(related)} related exception(s) for search term '{search_term}':\n\n"
            result += json.dumps(related, indent=2)

        return [TextContent(type="text", text=result)]

    raise ValueError(f"Unknown tool: {name}")

# Resources
@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="file:///exception_guide.md",
            name="Exception Investigation Guide",
            mimeType="text/markdown",
            description="Guide for investigating trade ingestion exceptions"
        ),
        Resource(
            uri="file:///event_schema.json",
            name="Event Schema and Rules",
            mimeType="application/json",
            description="Valid event types, required fields, and sequencing rules for trade ingestion"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """
    Handle resource read requests.

    Args:
        uri: Resource URI to read

    Returns:
        Resource content as string

    Raises:
        ValueError: If resource not found or read error occurs
    """
    uri_str = str(uri)

    if uri_str == "file:///exception_guide.md":
        try:
            return EXCEPTION_GUIDE.read_text()
        except FileNotFoundError:
            raise ValueError(f"Resource file not found: {EXCEPTION_GUIDE}")
        except Exception as e:
            raise ValueError(f"Error reading resource: {e}")

    elif uri_str == "file:///event_schema.json":
        try:
            return EVENT_SCHEMA.read_text()
        except FileNotFoundError:
            raise ValueError(f"Resource file not found: {EVENT_SCHEMA}")
        except Exception as e:
            raise ValueError(f"Error reading resource: {e}")

    raise ValueError(f"Unknown resource: {uri_str}")

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
