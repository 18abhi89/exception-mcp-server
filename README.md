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

## MCP Client Configuration

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
