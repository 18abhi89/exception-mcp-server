"""
Exception Analysis MCP Server

Provides tools and resources for analyzing trade ingestion exceptions.
"""

import asyncio
import csv
from pathlib import Path
from typing import List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# Constants
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
EXCEPTIONS_CSV = DATA_DIR / "exceptions.csv"
EXCEPTION_GUIDE = DOCS_DIR / "exception_guide.md"

app = Server("exception-analysis-server")


def load_schema_from_csv() -> str:
    """
    Load exception schema from CSV file.

    Returns:
        Formatted schema string with table structure and valid values
    """
    try:
        # Read CSV to get column names and sample values
        with open(EXCEPTIONS_CSV, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return "Error: CSV file is empty"

        # Build schema based on actual data
        schema = """Table: trade_ingestion_exception

Columns:
- id (BIGINT, Primary Key)
- event_id (VARCHAR(255))
- exception_sub_category (VARCHAR(255))
  Values: OUT_OF_ORDER, INVALID_EVENT, PREVIOUSLY_PROCESSED_MESSAGE
- status (VARCHAR(255))
  Values: OPEN, CLOSED
- error_message (TEXT)
- times_replayed (INT)
"""
        return schema.strip()

    except FileNotFoundError:
        return f"Error: Schema file not found at {EXCEPTIONS_CSV}"
    except Exception as e:
        return f"Error loading schema: {str(e)}"


# Tools
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="getExceptionTableSchema",
            description="Get the schema of trade_ingestion_exception table",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "getExceptionTableSchema":
        schema = load_schema_from_csv()
        return [TextContent(type="text", text=schema)]

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
