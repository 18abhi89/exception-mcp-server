#!/usr/bin/env python3
"""
MCP Client for Exception Analysis Server

This client demonstrates how to interact with the exception-analysis MCP server.
It can:
- List available tools and resources
- Call the getExceptionTableSchema tool
- Read the exception investigation guide resource
"""

import asyncio
import sys
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ExceptionAnalysisClient:
    """Client for interacting with the Exception Analysis MCP server."""

    def __init__(self, server_script_path: str = "server.py"):
        """
        Initialize the client.

        Args:
            server_script_path: Path to the server.py script
        """
        self.server_script_path = server_script_path
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """Connect to the MCP server."""
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        print("✓ Connected to Exception Analysis MCP Server")

    async def disconnect(self):
        """Disconnect from the MCP server."""
        await self.exit_stack.aclose()
        print("✓ Disconnected from server")

    async def list_tools(self):
        """List all available tools."""
        if not self.session:
            raise RuntimeError("Not connected to server")

        response = await self.session.list_tools()

        print("\n=== Available Tools ===")
        for tool in response.tools:
            print(f"\nTool: {tool.name}")
            print(f"Description: {tool.description}")
            if tool.inputSchema:
                print(f"Input Schema: {tool.inputSchema}")

        return response.tools

    async def list_resources(self):
        """List all available resources."""
        if not self.session:
            raise RuntimeError("Not connected to server")

        response = await self.session.list_resources()

        print("\n=== Available Resources ===")
        for resource in response.resources:
            print(f"\nResource: {resource.name}")
            print(f"URI: {resource.uri}")
            print(f"Description: {resource.description}")
            print(f"MIME Type: {resource.mimeType}")

        return response.resources

    async def get_exception_schema(self):
        """Call the getExceptionTableSchema tool."""
        if not self.session:
            raise RuntimeError("Not connected to server")

        print("\n=== Calling getExceptionTableSchema Tool ===")

        response = await self.session.call_tool("getExceptionTableSchema", {})

        for content in response.content:
            if hasattr(content, 'text'):
                print(content.text)

        return response

    async def read_exception_guide(self):
        """Read the exception investigation guide resource."""
        if not self.session:
            raise RuntimeError("Not connected to server")

        print("\n=== Reading Exception Investigation Guide ===")

        response = await self.session.read_resource("file:///exception_guide.md")

        for content in response.contents:
            if hasattr(content, 'text'):
                print(content.text)

        return response


async def main():
    """Main function demonstrating client usage."""

    # Create client instance
    client = ExceptionAnalysisClient()

    try:
        # Connect to server
        await client.connect()

        # List available tools
        await client.list_tools()

        # List available resources
        await client.list_resources()

        # Call the schema tool
        await client.get_exception_schema()

        # Read the exception guide
        await client.read_exception_guide()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Disconnect
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
