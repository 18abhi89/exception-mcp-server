import asyncio
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

app = Server("exception-analysis-server")

# Tool: Exception Schema
@app.list_tools()
async def list_tools() -> list[Tool]:
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
    if name == "getExceptionTableSchema":
        schema = """
Table: trade_ingestion_exception

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
        return [TextContent(type="text", text=schema)]
    
    raise ValueError(f"Unknown tool: {name}")

# Resource: Exception Guide
@app.list_resources()
async def list_resources() -> list[Resource]:
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
    # Convert URI to string (it comes as a Pydantic AnyUrl object)
    uri_str = str(uri)

    if uri_str == "file:///exception_guide.md":
        guide_path = Path(__file__).parent / "docs" / "exception_guide.md"
        try:
            return guide_path.read_text()
        except FileNotFoundError:
            raise ValueError(f"Resource file not found: {guide_path}")
        except Exception as e:
            raise ValueError(f"Error reading resource: {e}")

    raise ValueError(f"Unknown resource: {uri_str}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
