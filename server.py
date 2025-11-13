"""
Exception Analysis MCP Server

MCP server with AI-powered exception analysis tools.
"""

import asyncio
import csv
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from llm_client import AzureOpenAIClient
from vector_store import ExceptionVectorStore

# Constants
PROJECT_ROOT = Path(__file__).parent
CONFIG_FILE = PROJECT_ROOT / "config.yaml"
DATA_DIR = PROJECT_ROOT / "data"

# Global instances
app = Server("exception-analysis-server")
llm_client = None
vector_store = None
config = None


def load_config():
    """Load configuration from config.yaml."""
    global config

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

    with open(CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)

    return config


def initialize_clients():
    """Initialize LLM client and vector store."""
    global llm_client, vector_store

    # Load config
    cfg = load_config()

    # Get Azure OpenAI credentials
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")

    if not endpoint or not api_key:
        print("Warning: AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY not set")
        print("AI-powered tools will not work until credentials are provided")
        return

    # Initialize LLM client
    llm_client = AzureOpenAIClient(
        endpoint=endpoint,
        api_key=api_key,
        api_version=cfg['azure_openai']['api_version'],
        chat_deployment=cfg['azure_openai']['models']['chat'],
        embedding_deployment=cfg['azure_openai']['models']['embeddings']
    )

    # Initialize vector store
    vector_store = ExceptionVectorStore(
        llm_client=llm_client,
        persist_directory=cfg['vector_db']['persist_directory'],
        collection_name=cfg['vector_db']['collection_name']
    )

    print(f"✅ Initialized. Vector DB count: {vector_store.count()}")


def get_csv_path() -> Path:
    """Get path to exceptions CSV file."""
    return DATA_DIR / "exceptions.csv"


def load_exceptions_from_csv() -> List[Dict[str, Any]]:
    """Load all exceptions from CSV."""
    csv_path = get_csv_path()

    if not csv_path.exists():
        return []

    exceptions = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exceptions.append(row)

    return exceptions


def get_exception_by_id(exception_id: str) -> Dict[str, Any]:
    """Get exception by ID from CSV."""
    exceptions = load_exceptions_from_csv()

    for exc in exceptions:
        if exc.get('exception_id') == exception_id:
            return exc

    return None


def format_schema() -> str:
    """Format database schema for display."""
    cfg = load_config()

    schema_text = "# Database Schema\n\n"

    for table_name, table_sql in cfg['schema'].items():
        schema_text += f"## Table: {table_name}\n\n"
        schema_text += "```sql\n"
        schema_text += table_sql.strip()
        schema_text += "\n```\n\n"

    return schema_text


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate SQL query for safety.

    Rules:
    - Must start with SELECT (case-insensitive)
    - No semicolons allowed (prevents multiple statements)
    - No comments allowed

    Returns:
        (is_valid, error_message)
    """
    sql_stripped = sql.strip()

    if not sql_stripped:
        return False, "Empty query"

    # Must be SELECT
    if not sql_stripped.upper().startswith("SELECT"):
        return False, "Only SELECT queries allowed"

    # No semicolons (prevents statement chaining)
    if ';' in sql_stripped:
        return False, "Semicolons not allowed"

    # No SQL comments
    if '--' in sql_stripped or '/*' in sql_stripped:
        return False, "Comments not allowed"

    return True, ""


def execute_query_on_csv(sql: str) -> str:
    """
    Execute SQL-like query on CSV data.

    Note: This is a simple implementation for testing with CSV.
    In production, this would execute against actual PostgreSQL database.

    Currently supports:
    - Simple filtering by showing all records (no actual SQL execution)
    - Returns formatted results

    Args:
        sql: SQL query string

    Returns:
        Formatted query results
    """
    # Validate SQL
    is_valid, error = validate_sql(sql)
    if not is_valid:
        return f"❌ Query validation failed: {error}"

    # Load data from CSV
    exceptions = load_exceptions_from_csv()

    if not exceptions:
        return "No data found in CSV"

    # Simple implementation: return all records as formatted text
    # In production, this would execute actual SQL against PostgreSQL
    result = f"Query: {sql}\n\n"
    result += f"Found {len(exceptions)} total records\n\n"
    result += "Sample records (first 5):\n"
    result += "=" * 80 + "\n\n"

    for i, exc in enumerate(exceptions[:5], 1):
        result += f"Record {i}:\n"
        result += f"  Exception ID: {exc.get('exception_id')}\n"
        result += f"  Event ID: {exc.get('event_id')}\n"
        result += f"  Error: {exc.get('error_message', '')[:100]}...\n"
        result += f"  Type: {exc.get('exception_type')}\n"
        result += f"  Category: {exc.get('exception_category')}\n"
        result += f"  Status: {exc.get('status')}\n"
        result += f"  Retries: {exc.get('times_replayed')}\n"
        result += "\n"

    return result


# MCP Tools
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="getSchema",
            description="Get the database schema for trade_ingestion_exception table",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="querySafeSQL",
            description="Execute a safe SELECT-only SQL query (for testing with CSV data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SELECT SQL query to execute"
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="findSimilarExceptions",
            description="Find similar exceptions using AI vector similarity search",
            inputSchema={
                "type": "object",
                "properties": {
                    "exception_id": {
                        "type": "string",
                        "description": "The exception ID to find similar cases for"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of similar cases to return (default: 3)",
                        "default": 3
                    }
                },
                "required": ["exception_id"]
            }
        ),
        Tool(
            name="analyzeExceptionWithAI",
            description="Analyze exception with AI - provides root cause analysis and recommendations based on similar historical cases",
            inputSchema={
                "type": "object",
                "properties": {
                    "exception_id": {
                        "type": "string",
                        "description": "The exception ID to analyze"
                    }
                },
                "required": ["exception_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if name == "getSchema":
        schema = format_schema()
        return [TextContent(type="text", text=schema)]

    elif name == "querySafeSQL":
        sql = arguments.get('sql', '')
        result = execute_query_on_csv(sql)
        return [TextContent(type="text", text=result)]

    elif name == "findSimilarExceptions":
        exception_id = arguments.get('exception_id')
        top_k = arguments.get('top_k', 3)

        # Check if vector store is initialized
        if not vector_store or not llm_client:
            return [TextContent(
                type="text",
                text="❌ Vector store not initialized. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY environment variables and restart."
            )]

        # Get exception
        exception = get_exception_by_id(exception_id)
        if not exception:
            return [TextContent(
                type="text",
                text=f"❌ Exception not found: {exception_id}"
            )]

        # Find similar
        similar = vector_store.find_similar(exception_id, exception, top_k=top_k)

        if not similar:
            return [TextContent(
                type="text",
                text=f"No similar exceptions found for {exception_id}"
            )]

        # Format results
        result = f"Found {len(similar)} similar exceptions:\n\n"
        for i, sim in enumerate(similar, 1):
            metadata = sim.get('metadata', {})
            similarity = sim.get('similarity', 0) * 100

            result += f"## Similar Case {i} ({similarity:.1f}% match)\n\n"
            result += f"**Exception ID:** {sim.get('exception_id')}\n"
            result += f"**Type:** {metadata.get('exception_type', 'N/A')}\n"
            result += f"**Category:** {metadata.get('exception_category', 'N/A')}\n"
            result += f"**Error:** {metadata.get('error_message', 'N/A')[:200]}...\n"
            result += f"**Resolution:** {metadata.get('remarks', 'No remarks')}\n\n"

        return [TextContent(type="text", text=result)]

    elif name == "analyzeExceptionWithAI":
        exception_id = arguments.get('exception_id')

        # Check if LLM client is initialized
        if not llm_client or not vector_store:
            return [TextContent(
                type="text",
                text="❌ AI client not initialized. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY environment variables and restart."
            )]

        # Get exception
        exception = get_exception_by_id(exception_id)
        if not exception:
            return [TextContent(
                type="text",
                text=f"❌ Exception not found: {exception_id}"
            )]

        # Find similar cases
        similar = vector_store.find_similar(exception_id, exception, top_k=3)

        # Get schema
        schema = format_schema()

        # Generate AI analysis
        analysis = llm_client.analyze_exception(exception, similar, schema)

        return [TextContent(type="text", text=analysis)]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    # Initialize clients
    try:
        initialize_clients()
    except Exception as e:
        print(f"Warning: Failed to initialize AI clients: {e}")
        print("Server will start but AI tools will not work")

    # Start server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
