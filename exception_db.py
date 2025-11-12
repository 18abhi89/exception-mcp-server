"""
ChromaDB wrapper for exception similarity search.

Simple module for storing and querying exception history using semantic search.
"""

import chromadb
from pathlib import Path
from typing import List, Dict, Any, Optional


class ExceptionDB:
    """Manages exception history storage and similarity search using ChromaDB."""

    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB client.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        if persist_directory is None:
            persist_directory = str(Path(__file__).parent / "chromadb_data")

        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="exception_history",
            metadata={"description": "Historical exception data for similarity search"}
        )

    def add_exception(
        self,
        exception_id: str,
        error_message: str,
        exception_type: str,
        exception_category: str,
        exception_sub_category: Optional[str] = None,
        trace: Optional[str] = None,
        stacktrace: Optional[str] = None,
        resolution: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add an exception to the history database.

        Args:
            exception_id: Unique exception identifier
            error_message: The error message text
            exception_type: Type of exception
            exception_category: Category of exception
            exception_sub_category: Sub-category of exception (optional)
            trace: Brief trace (optional)
            stacktrace: Full stack trace (optional)
            resolution: How it was resolved (optional)
            metadata: Additional metadata (optional)
        """
        # Create searchable text from key fields - stacktrace is most important for similarity
        document = f"{error_message}\n{exception_type}\n{exception_category}"
        if exception_sub_category:
            document += f"\n{exception_sub_category}"
        if stacktrace:
            # Stacktrace is the most valuable signal for finding similar exceptions
            document += f"\n{stacktrace}"
        elif trace:
            document += f"\n{trace}"

        # Prepare metadata
        meta = {
            "exception_type": exception_type,
            "exception_category": exception_category,
            "exception_sub_category": exception_sub_category or "",
            "resolution": resolution or "unresolved"
        }
        if metadata:
            meta.update(metadata)

        # Add to collection
        self.collection.add(
            documents=[document],
            ids=[exception_id],
            metadatas=[meta]
        )

    def find_similar(
        self,
        error_message: str,
        exception_type: str = "",
        exception_category: str = "",
        exception_sub_category: str = "",
        stacktrace: str = "",
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar exceptions using semantic search based on stacktrace and metadata.

        Args:
            error_message: Error message to search for
            exception_type: Exception type (optional filter)
            exception_category: Exception category (optional filter)
            exception_sub_category: Exception sub-category (optional filter)
            stacktrace: Full stack trace for similarity matching (most important signal)
            n_results: Number of results to return

        Returns:
            List of similar exceptions with metadata
        """
        # Create query text - stacktrace is the most valuable signal for finding similar exceptions
        query = f"{error_message}\n{exception_type}\n{exception_category}"
        if exception_sub_category:
            query += f"\n{exception_sub_category}"
        if stacktrace:
            # Stacktrace provides the best semantic matching for similar root causes
            query += f"\n{stacktrace}"

        # Query ChromaDB
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        # Format results
        similar_exceptions = []
        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                similar_exceptions.append({
                    'id': results['ids'][0][i],
                    'distance': results['distances'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'document': results['documents'][0][i]
                })

        return similar_exceptions

    def load_from_csv(self, csv_path: str) -> int:
        """
        Load exception history from CSV file.

        Args:
            csv_path: Path to CSV file with exception history

        Returns:
            Number of records loaded
        """
        import csv

        count = 0
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.add_exception(
                    exception_id=row['exception_id'],
                    error_message=row['error_message'],
                    exception_type=row['exception_type'],
                    exception_category=row['exception_category'],
                    exception_sub_category=row.get('exception_sub_category', ''),
                    trace=row.get('trace', ''),
                    stacktrace=row.get('stacktrace', ''),
                    resolution=row.get('resolution', ''),
                    metadata={
                        'event_id': row.get('event_id', ''),
                        'source_system': row.get('source_system', ''),
                        'times_replayed': row.get('times_replayed', '0')
                    }
                )
                count += 1

        return count

    def count(self) -> int:
        """Get total number of exceptions in database."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear all exceptions from database."""
        self.client.delete_collection("exception_history")
        self.collection = self.client.get_or_create_collection(
            name="exception_history",
            metadata={"description": "Historical exception data for similarity search"}
        )
