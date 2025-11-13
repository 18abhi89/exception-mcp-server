"""
Vector Store for Exception Similarity Search

Uses ChromaDB with Azure OpenAI embeddings for finding similar exceptions.
"""

import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional
from stacktrace_parser import StackTraceParser
import llm_client


class ExceptionVectorStore:
    """Vector store for exception similarity search using ChromaDB."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str,
        embedding_deployment: str,
        persist_directory: str = "./chromadb_data",
        collection_name: str = "resolved_exceptions"
    ):
        """
        Initialize vector store.

        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: API key for authentication
            api_version: API version
            embedding_deployment: Embedding deployment name
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version
        self.embedding_deployment = embedding_deployment
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Initialize ChromaDB client
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Resolved exceptions for similarity search"}
        )

    def _prepare_text_for_embedding(self, record: Dict[str, Any]) -> str:
        """
        Combine relevant fields into text for embedding.

        Args:
            record: Exception record

        Returns:
            Combined text for embedding
        """
        parts = []

        # Error message (important)
        if record.get('error_message'):
            parts.append(f"Error: {record['error_message']}")

        # Exception type (important)
        if record.get('exception_type'):
            parts.append(f"Type: {record['exception_type']}")

        # Stack trace (most important for similarity)
        if record.get('trace'):
            parts.append(f"Trace: {record['trace']}")

        return "\n".join(parts)

    def _prepare_metadata(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare metadata for ChromaDB (no None values allowed).

        Args:
            record: Exception record

        Returns:
            Cleaned metadata dict
        """
        # Parse stacktrace to get method chain
        trace = record.get('trace', '')
        parsed = StackTraceParser.parse(trace)

        metadata = {}

        # Basic fields
        if record.get('exception_type'):
            metadata['exception_type'] = str(record['exception_type'])

        if record.get('exception_category'):
            metadata['exception_category'] = str(record['exception_category'])

        if record.get('exception_sub_category'):
            metadata['exception_sub_category'] = str(record['exception_sub_category'])

        if record.get('source_system'):
            metadata['source_system'] = str(record['source_system'])

        if record.get('raising_system'):
            metadata['raising_system'] = str(record['raising_system'])

        if record.get('event_id'):
            metadata['event_id'] = str(record['event_id'])

        # Remarks (resolution) - important!
        if record.get('remarks'):
            metadata['remarks'] = str(record['remarks'])

        # Error message (truncated)
        if record.get('error_message'):
            metadata['error_message'] = str(record['error_message'])[:500]

        # Parsed stacktrace info
        if parsed['entry_point']:
            metadata['entry_point'] = str(parsed['entry_point'])

        if parsed['package_root']:
            metadata['package_root'] = str(parsed['package_root'])

        # Method chain as comma-separated string
        if parsed['method_chain']:
            metadata['method_chain'] = ','.join(parsed['method_chain'][:10])

        # Call signature
        if parsed['method_chain']:
            metadata['call_signature'] = '->'.join(parsed['method_chain'][:5])

        return metadata

    def add_exception(self, exception_id: str, record: Dict[str, Any]) -> None:
        """
        Add exception to vector store.

        Args:
            exception_id: Unique exception ID
            record: Exception record with fields
        """
        # Prepare text for embedding
        text = self._prepare_text_for_embedding(record)

        # Generate embedding using simple request/response call
        embedding = llm_client.generate_embedding(
            endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment=self.embedding_deployment,
            text=text
        )

        # Prepare metadata
        metadata = self._prepare_metadata(record)

        # Add to ChromaDB
        self.collection.add(
            ids=[exception_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )

    def add_exceptions_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Add multiple exceptions in batch.

        Args:
            records: List of exception records (must have 'exception_id' field)

        Returns:
            Number of records added
        """
        if not records:
            return 0

        ids = []
        texts = []
        metadatas = []

        for record in records:
            exception_id = record.get('exception_id')
            if not exception_id:
                continue

            ids.append(str(exception_id))
            texts.append(self._prepare_text_for_embedding(record))
            metadatas.append(self._prepare_metadata(record))

        # Generate embeddings one by one
        print(f"Generating embeddings for {len(texts)} exceptions...")
        embeddings = []
        for text in texts:
            embedding = llm_client.generate_embedding(
                endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version,
                deployment=self.embedding_deployment,
                text=text
            )
            embeddings.append(embedding)

        # Add to ChromaDB
        print(f"Adding {len(ids)} exceptions to vector store...")
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        return len(ids)

    def find_similar(
        self,
        exception_id: str,
        exception_record: Dict[str, Any],
        top_k: int = 3,
        filter_category: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find similar exceptions using vector similarity.

        Args:
            exception_id: ID of exception to find similar cases for
            exception_record: The exception record
            top_k: Number of similar cases to return
            filter_category: Filter by same exception_category

        Returns:
            List of similar exceptions with metadata and similarity scores
        """
        # Prepare text for embedding
        text = self._prepare_text_for_embedding(exception_record)

        # Generate embedding using simple request/response call
        embedding = llm_client.generate_embedding(
            endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment=self.embedding_deployment,
            text=text
        )

        # Build where filter
        where_filter = None
        if filter_category and exception_record.get('exception_category'):
            where_filter = {
                "exception_category": exception_record['exception_category']
            }

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k + 1,  # +1 because it might include itself
            where=where_filter
        )

        # Format results
        similar = []
        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                result_id = results['ids'][0][i]

                # Skip if it's the same exception
                if result_id == str(exception_id):
                    continue

                # Calculate similarity (1 - distance)
                distance = results['distances'][0][i]
                similarity = 1 - distance

                similar.append({
                    'exception_id': result_id,
                    'distance': distance,
                    'similarity': similarity,
                    'metadata': results['metadatas'][0][i],
                    'document': results['documents'][0][i] if results.get('documents') else None
                })

                if len(similar) >= top_k:
                    break

        return similar

    def count(self) -> int:
        """Get total number of exceptions in vector store."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear all exceptions from vector store."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Resolved exceptions for similarity search"}
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "total_exceptions": self.count(),
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory
        }


def test_vector_store():
    """Test the vector store."""
    from llm_client import AzureOpenAIClient
    import os

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")

    if not endpoint or not api_key:
        print("Error: Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY")
        return

    # Initialize LLM client
    llm_client = AzureOpenAIClient(endpoint=endpoint, api_key=api_key)

    # Initialize vector store
    store = ExceptionVectorStore(
        llm_client=llm_client,
        persist_directory="./test_chromadb"
    )

    print(f"Vector store initialized. Count: {store.count()}")

    # Test adding an exception
    test_exception = {
        'exception_id': 'test-001',
        'error_message': 'Connection timeout',
        'exception_type': 'java.sql.SQLTimeoutException',
        'exception_category': 'INFRASTRUCTURE',
        'trace': 'java.sql.SQLTimeoutException\n\tat com.test.Service.query(Service.java:45)',
        'remarks': 'Increased connection timeout'
    }

    store.add_exception('test-001', test_exception)
    print(f"Added test exception. Count: {store.count()}")


if __name__ == "__main__":
    test_vector_store()
