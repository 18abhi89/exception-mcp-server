#!/usr/bin/env python3
"""
Example usage scenarios for the Exception Analysis MCP Client.

This script demonstrates various ways to use the client programmatically.
"""

import asyncio
from client_example import ExceptionAnalysisClient


async def example_1_basic_usage():
    """Example 1: Basic usage - list everything and get schema."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Usage")
    print("="*60)

    client = ExceptionAnalysisClient()

    try:
        await client.connect()
        await client.list_tools()
        await client.list_resources()
        await client.get_exception_schema()
    finally:
        await client.disconnect()


async def example_2_read_guide():
    """Example 2: Read the exception guide for investigation help."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Reading Exception Guide")
    print("="*60)

    client = ExceptionAnalysisClient()

    try:
        await client.connect()
        await client.read_exception_guide()
    finally:
        await client.disconnect()


async def example_3_schema_only():
    """Example 3: Just get the database schema."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Get Schema Only")
    print("="*60)

    client = ExceptionAnalysisClient()

    try:
        await client.connect()
        response = await client.get_exception_schema()

        # Process the response
        for content in response.content:
            if hasattr(content, 'text'):
                # You could parse this and use it in your application
                schema_text = content.text
                print(f"\nProcessing schema: {len(schema_text)} characters")

    finally:
        await client.disconnect()


async def example_4_custom_workflow():
    """Example 4: Custom workflow - get schema then guide."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Custom Workflow")
    print("="*60)

    client = ExceptionAnalysisClient()

    try:
        await client.connect()

        # First, understand the data structure
        print("\nStep 1: Understanding the data structure...")
        await client.get_exception_schema()

        # Then, get guidance on how to investigate
        print("\nStep 2: Getting investigation guidance...")
        await client.read_exception_guide()

        print("\n✓ Workflow completed!")

    finally:
        await client.disconnect()


async def example_5_programmatic_usage():
    """Example 5: Using the client in your application."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Programmatic Usage")
    print("="*60)

    client = ExceptionAnalysisClient()

    try:
        await client.connect()

        # Get tools list
        tools = await client.list_tools()
        print(f"\n✓ Found {len(tools)} tools available")

        # Get resources list
        resources = await client.list_resources()
        print(f"✓ Found {len(resources)} resources available")

        # Get schema and parse it
        schema_response = await client.get_exception_schema()
        for content in schema_response.content:
            if hasattr(content, 'text'):
                # In a real application, you might parse this into a data structure
                lines = content.text.strip().split('\n')
                print(f"✓ Schema has {len(lines)} lines")

                # Example: extract column names
                columns = [line.strip() for line in lines if line.strip().startswith('- ')]
                print(f"✓ Found {len(columns)} columns in schema")

        # Read guide
        guide_response = await client.read_exception_guide()
        for content in guide_response.contents:
            if hasattr(content, 'text'):
                # In a real application, you might parse this for specific patterns
                guide_text = content.text
                exception_types = guide_text.count('###')
                print(f"✓ Guide covers {exception_types} exception types")

    finally:
        await client.disconnect()


async def run_all_examples():
    """Run all example scenarios."""
    examples = [
        example_1_basic_usage,
        example_2_read_guide,
        example_3_schema_only,
        example_4_custom_workflow,
        example_5_programmatic_usage,
    ]

    for example in examples:
        try:
            await example()
            await asyncio.sleep(1)  # Small delay between examples
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")


if __name__ == "__main__":
    print("Exception Analysis MCP Client - Example Usage Scenarios")
    print("This will demonstrate various ways to use the client.\n")

    asyncio.run(run_all_examples())

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)
