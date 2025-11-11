# Exception Analysis MCP Server

MCP server for analyzing trade ingestion exceptions.

## Project Structure

```
exception-mcp-server/
├── server.py                  # MCP server (main entry point)
├── exception_db.py            # ChromaDB wrapper for similarity search
├── streamlit_app.py           # Web-based dashboard UI
├── requirements.txt           # Python dependencies
│
├── data/                      # Data files
│   ├── exceptions.csv         # Current exceptions (real schema)
│   ├── exception_history.csv  # Historical exceptions with resolutions
│   └── test_data.json         # Test scenarios
│
├── examples/                  # Example code
│   ├── client_example.py      # MCP client example
│   ├── usage_demo.py          # Usage demonstrations
│   └── simulation.py          # Test data simulator
│
├── docs/                      # Documentation
│   └── exception_guide.md     # Exception investigation guide
│
└── test_simple.py             # Core functionality tests
```

## Features

### MCP Tools
- **`getExceptionTableSchema`** - Get full exception_events table schema
- **`getHighRetryExceptions`** - Find exceptions with retry count > threshold (default: 5)
- **`findSimilarExceptions`** - Semantic similarity search using ChromaDB
- **`analyzeException`** - AI-powered analysis with historical context and thesis

### Resources
- **`exception_guide.md`** - Comprehensive investigation guide for all exception categories

### Streamlit Dashboard
- Visual interface for exception analysis
- High retry exception monitoring
- Similarity search with confidence scores
- Historical resolution database browser

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Option 1: Visual Dashboard (Recommended for Exploration)

Launch the Streamlit web interface:

```bash
streamlit run streamlit_app.py
```

This opens a browser-based dashboard with:
- **High Retry Exceptions Tab**: View all exceptions with > 5 retries (configurable threshold)
- **Analyze Exception Tab**: Deep dive analysis with similarity search and confidence scores
- **Historical Database Tab**: Browse resolved exceptions and try similarity searches

Perfect for:
- Quick investigation of current issues
- Visualizing exception patterns
- Exploring historical resolutions with confidence scores

### Option 2: MCP Server (For Tool Integration)

Run as an MCP server for integration with Claude Desktop or other MCP clients:

```bash
python server.py
```

## Using the Python MCP Client

### Quick Start

Run the included client to interact with the server:

```bash
# Basic usage - demonstrates all features
python examples/client_example.py

# Run example scenarios
python examples/usage_demo.py
```

### Programmatic Usage

Use the client in your own Python code:

```python
import sys
sys.path.append('examples')
from client_example import ExceptionAnalysisClient

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

The Python client (`examples/client_example.py`) provides:
- **connect()** - Connect to the MCP server
- **list_tools()** - List all available tools
- **list_resources()** - List all available resources
- **get_exception_schema()** - Get the database table schema
- **read_exception_guide()** - Read the exception investigation guide
- **disconnect()** - Disconnect from the server

See `examples/usage_demo.py` for more detailed usage patterns.

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
