"""
Ingest CLOSED exceptions into vector database.

Loads exceptions with status='CLOSED' and remarks into ChromaDB for similarity search.
"""

import csv
import os
from pathlib import Path
from llm_client import AzureOpenAIClient
from vector_store import ExceptionVectorStore


def load_closed_exceptions(csv_path: str = "data/exceptions.csv"):
    """
    Load CLOSED exceptions from CSV.

    Args:
        csv_path: Path to exceptions CSV file

    Returns:
        List of CLOSED exception records
    """
    closed_exceptions = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only load CLOSED exceptions with remarks
            if row.get('status') == 'CLOSED' and row.get('remarks'):
                closed_exceptions.append(row)

    return closed_exceptions


def ingest_to_vector_db(
    csv_path: str = "data/exceptions.csv",
    persist_directory: str = "./chromadb_data"
):
    """
    Ingest CLOSED exceptions into vector database.

    Args:
        csv_path: Path to exceptions CSV
        persist_directory: ChromaDB persist directory
    """
    # Get Azure OpenAI credentials from environment
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")

    if not endpoint or not api_key:
        print("❌ Error: Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY environment variables")
        print("\nExample:")
        print("  export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("  export AZURE_OPENAI_KEY='your-api-key'")
        return

    print("Initializing Azure OpenAI client...")
    llm_client = AzureOpenAIClient(
        endpoint=endpoint,
        api_key=api_key
    )

    print("Initializing vector store...")
    vector_store = ExceptionVectorStore(
        llm_client=llm_client,
        persist_directory=persist_directory
    )

    print(f"\nLoading CLOSED exceptions from {csv_path}...")
    closed_exceptions = load_closed_exceptions(csv_path)

    print(f"Found {len(closed_exceptions)} CLOSED exceptions with remarks")

    if not closed_exceptions:
        print("❌ No CLOSED exceptions found. Nothing to ingest.")
        return

    print("\nIngesting into vector database...")
    print("This will take a few moments (generating embeddings)...")

    count = vector_store.add_exceptions_batch(closed_exceptions)

    print(f"\n✅ Successfully ingested {count} exceptions into vector database")
    print(f"   Vector store location: {persist_directory}")
    print(f"   Total records in vector DB: {vector_store.count()}")

    # Show some stats
    stats = vector_store.get_stats()
    print("\n📊 Vector Store Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


def clear_vector_db(persist_directory: str = "./chromadb_data"):
    """
    Clear all data from vector database.

    Args:
        persist_directory: ChromaDB persist directory
    """
    from llm_client import AzureOpenAIClient

    # Need a dummy client just to initialize the store
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "dummy")
    api_key = os.getenv("AZURE_OPENAI_KEY", "dummy")

    llm_client = AzureOpenAIClient(endpoint=endpoint, api_key=api_key)
    vector_store = ExceptionVectorStore(llm_client=llm_client, persist_directory=persist_directory)

    print(f"Clearing vector database at {persist_directory}...")
    vector_store.clear()
    print("✅ Vector database cleared")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_vector_db()
    else:
        ingest_to_vector_db()
