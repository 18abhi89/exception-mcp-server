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
    """Get exceptions with retry count above threshold."""
    exceptions = []
    try:
        with open(EXCEPTIONS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row.get('times_replayed', 0)) > threshold:
                    exceptions.append(row)
    except Exception as e:
        print(f"Error reading exceptions: {e}")

    return exceptions


def analyze_exception_with_history(exception: Dict[str, Any]) -> str:
    """Analyze an exception using historical data and patterns."""
    error_message = exception.get('error_message', '')
    exception_type = exception.get('exception_type', '')
    exception_category = exception.get('exception_category', '')
    times_replayed = exception.get('times_replayed', 0)

    # Find similar exceptions
    similar = exception_db.find_similar(
        error_message=error_message,
        exception_type=exception_type,
        exception_category=exception_category,
        n_results=3
    )

    # Build analysis
    analysis = f"""## Exception Analysis

**Current Exception:**
- Event ID: {exception.get('event_id', 'N/A')}
- Error: {error_message}
- Type: {exception_type}
- Category: {exception_category}
- Times Replayed: {times_replayed}
- Source System: {exception.get('source_system', 'N/A')}
- Raising System: {exception.get('raising_system', 'N/A')}

**Why It's Failing After {times_replayed} Retries:**

"""

    if similar:
        analysis += "Based on similar historical cases:\n\n"
        for i, sim in enumerate(similar, 1):
            metadata = sim.get('metadata', {})
            resolution = metadata.get('resolution', 'No resolution recorded')
            analysis += f"### Similar Case {i} (Similarity: {1 - sim['distance']:.2%})\n"
            analysis += f"- **Exception Type:** {metadata.get('exception_type', 'N/A')}\n"
            analysis += f"- **Resolution:** {resolution}\n\n"

        # Form thesis
        analysis += "\n**Thesis:**\n"
        analysis += f"This exception has been retried {times_replayed} times without success. "

        if exception_category == "VALIDATION":
            analysis += "This is a VALIDATION error, which typically requires data or schema fixes rather than retries. "
            analysis += "Retrying won't help unless the underlying data issue is corrected.\n"
        elif exception_category == "SEQUENCING":
            analysis += "This is a SEQUENCING error indicating out-of-order message delivery. "
            analysis += "Retries may not help if the dependent message hasn't arrived yet. Consider implementing temporal parking.\n"
        elif exception_category == "BUSINESS_LOGIC":
            analysis += "This is a BUSINESS_LOGIC error that likely requires configuration or reference data updates. "
            analysis += "Simple retries won't resolve the underlying business rule violation.\n"

        if similar:
            analysis += f"\nBased on {len(similar)} similar historical case(s), recommended actions are listed above.\n"
    else:
        analysis += "No similar historical cases found. This may be a new type of exception.\n"
        analysis += f"\n**General Guidance for {exception_category} errors:**\n"
        analysis += "Check the exception guide resource for investigation steps.\n"

    return analysis


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
            description="Find similar historical exceptions using semantic search",
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
        n_results = arguments.get('n_results', 5)

        similar = exception_db.find_similar(
            error_message=error_message,
            exception_type=exception_type,
            exception_category=exception_category,
            n_results=n_results
        )

        if not similar:
            result = "No similar exceptions found in historical data."
        else:
            result = f"Found {len(similar)} similar exception(s):\n\n"
            for i, sim in enumerate(similar, 1):
                metadata = sim.get('metadata', {})
                similarity_score = (1 - sim['distance']) * 100
                result += f"### Similar Case {i} (Similarity: {similarity_score:.1f}%)\n"
                result += f"- Exception Type: {metadata.get('exception_type', 'N/A')}\n"
                result += f"- Category: {metadata.get('exception_category', 'N/A')}\n"
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

    raise ValueError(f"Unknown resource: {uri_str}")

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
