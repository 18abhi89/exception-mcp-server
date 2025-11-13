"""
Ingest CLOSED exceptions into vector database.

Loads exceptions with status='CLOSED' and remarks into ChromaDB for similarity search.
"""

import csv
import os
import yaml
from pathlib import Path
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


def get_config_value(config_value: str, env_fallback: str = None) -> str:
    """Get configuration value, supporting both direct values and ${ENV_VAR} substitution."""
    if config_value:
        if config_value.startswith("${") and config_value.endswith("}"):
            env_var = config_value[2:-1]
            if ':' in env_var:
                var_name, default = env_var.split(':', 1)
                return os.getenv(var_name, default)
            return os.getenv(env_var)
        return config_value

    if env_fallback:
        return os.getenv(env_fallback)

    return None


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
    # Load config from config.yaml
    config_file = Path(__file__).parent / "config.yaml"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        endpoint = get_config_value(
            config['azure_openai'].get('endpoint'),
            'AZURE_OPENAI_ENDPOINT'
        )
        api_key = get_config_value(
            config['azure_openai'].get('api_key'),
            'AZURE_OPENAI_KEY'
        )
        api_version = config['azure_openai'].get('api_version', '2024-02-15-preview')
        embedding_deployment = config['azure_openai']['models'].get('embeddings', 'text-embedding-ada-002')
    else:
        # Fallback to environment variables
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")
        api_version = '2024-02-15-preview'
        embedding_deployment = 'text-embedding-ada-002'

    if not endpoint or not api_key:
        print("❌ Error: Azure OpenAI credentials not configured")
        print("\nEdit config.yaml and paste your credentials:")
        print("  azure_openai:")
        print("    endpoint: 'https://your-resource.openai.azure.com/'")
        print("    api_key: 'your-api-key'")
        return

    print("Initializing vector store...")
    vector_store = ExceptionVectorStore(
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        embedding_deployment=embedding_deployment,
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
    # Need dummy config just to initialize the store
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "dummy")
    api_key = os.getenv("AZURE_OPENAI_KEY", "dummy")
    api_version = "2024-02-15-preview"
    embedding_deployment = "text-embedding-ada-002"

    vector_store = ExceptionVectorStore(
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        embedding_deployment=embedding_deployment,
        persist_directory=persist_directory
    )

    print(f"Clearing vector database at {persist_directory}...")
    vector_store.clear()
    print("✅ Vector database cleared")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_vector_db()
    else:
        ingest_to_vector_db()
