# Exception Analysis MCP Server

MCP server for analyzing trade ingestion exceptions.

## Features

**Tools:**
- `getExceptionTableSchema` - Get database schema for exception table

**Resources:**
- `exception_guide.md` - Investigation guide for common exceptions

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python server.py
```

## Using the Python MCP Client

### Quick Start

Run the included client to interact with the server:

```bash
# Basic usage - demonstrates all features
python client.py

# Run example scenarios
python example_usage.py
```

### Programmatic Usage

Use the client in your own Python code:

```python
from client import ExceptionAnalysisClient

async def main():
    client = ExceptionAnalysisClient()

    try:
        # Connect to server
        await client.connect()

        # List available tools
        tools = await client.list_tools()

        # Get exception table schema
        schema = await client.get_exception_schema()

        # Read investigation guide
        guide = await client.read_exception_guide()

    finally:
        await client.disconnect()

asyncio.run(main())
```

### Client Features

The Python client (`client.py`) provides:
- **connect()** - Connect to the MCP server
- **list_tools()** - List all available tools
- **list_resources()** - List all available resources
- **get_exception_schema()** - Get the database table schema
- **read_exception_guide()** - Read the exception investigation guide
- **disconnect()** - Disconnect from the server

See `example_usage.py` for more detailed usage patterns.

## MCP Client Configuration (Claude Desktop)

Add to your MCP client config (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "exception-analysis": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```
