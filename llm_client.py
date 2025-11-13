"""
Azure OpenAI Client using requests library.

Simple client for chat completions and embeddings without SDK dependencies.
"""

import requests
import time
from typing import List, Dict, Any, Optional


class AzureOpenAIClient:
    """Client for Azure OpenAI API using requests."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str = "2024-02-15-preview",
        chat_deployment: str = "gpt-4",
        embedding_deployment: str = "text-embedding-ada-002",
        timeout: int = 60
    ):
        """
        Initialize Azure OpenAI client.

        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: API key for authentication
            api_version: API version
            chat_deployment: Deployment name for chat model
            embedding_deployment: Deployment name for embedding model
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.api_version = api_version
        self.chat_deployment = chat_deployment
        self.embedding_deployment = embedding_deployment
        self.timeout = timeout

    def _make_request(
        self,
        method: str,
        url: str,
        json_data: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (POST, GET, etc.)
            url: Full URL
            json_data: JSON payload
            max_retries: Maximum retry attempts

        Returns:
            Response JSON

        Raises:
            Exception: If request fails after retries
        """
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return response.json()

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    print(f"Rate limited. Retrying after {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                # Other errors
                response.raise_for_status()

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Timeout. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Request timed out after {max_retries} attempts")

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Request failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Request failed after {max_retries} attempts: {e}")

        raise Exception("Max retries exceeded")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Get chat completion from Azure OpenAI.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters

        Returns:
            Response text content

        Example:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is 2+2?"}
            ]
            response = client.chat_completion(messages)
        """
        url = (
            f"{self.endpoint}/openai/deployments/{self.chat_deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )

        payload = {
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        result = self._make_request("POST", url, payload)
        return result["choices"][0]["message"]["content"]

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Ada model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (list of floats)

        Example:
            embedding = client.generate_embedding("Hello world")
            print(len(embedding))  # 1536 for Ada-002
        """
        url = (
            f"{self.endpoint}/openai/deployments/{self.embedding_deployment}"
            f"/embeddings?api-version={self.api_version}"
        )

        payload = {
            "input": text
        }

        result = self._make_request("POST", url, payload)
        return result["data"][0]["embedding"]

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single request.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Example:
            texts = ["Hello", "World"]
            embeddings = client.generate_embeddings_batch(texts)
        """
        url = (
            f"{self.endpoint}/openai/deployments/{self.embedding_deployment}"
            f"/embeddings?api-version={self.api_version}"
        )

        payload = {
            "input": texts
        }

        result = self._make_request("POST", url, payload)
        # Sort by index to maintain order
        sorted_data = sorted(result["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]

    def analyze_exception(
        self,
        exception_data: Dict[str, Any],
        similar_cases: List[Dict[str, Any]],
        schema: str
    ) -> str:
        """
        Generate AI-powered exception analysis.

        Args:
            exception_data: Current exception details
            similar_cases: List of similar resolved exceptions
            schema: Database schema for context

        Returns:
            Analysis text with root cause and recommendations
        """
        system_prompt = """You are an expert system reliability engineer analyzing production exceptions.
Your task is to provide clear, actionable root cause analysis and recommendations.

Focus on:
1. Root cause (why retries won't help)
2. Similar historical cases and their resolutions
3. Specific actionable recommendations
4. Whether immediate action is needed

Be concise and technical."""

        similar_text = "\n\n".join([
            f"**Similar Case {i+1}** (Similarity: {case.get('similarity', 0)*100:.0f}%)\n"
            f"Error: {case.get('error_message', 'N/A')[:200]}\n"
            f"Type: {case.get('exception_type', 'N/A')}\n"
            f"Resolution: {case.get('remarks', 'No remarks available')}"
            for i, case in enumerate(similar_cases[:3])
        ]) if similar_cases else "No similar cases found in history."

        user_prompt = f"""Analyze this exception:

**Current Exception:**
- Event ID: {exception_data.get('event_id')}
- Error: {exception_data.get('error_message')}
- Type: {exception_data.get('exception_type')}
- Category: {exception_data.get('exception_category')}
- Times Retried: {exception_data.get('times_replayed', 0)}
- Source: {exception_data.get('source_system')} → {exception_data.get('raising_system')}

**Stack Trace:**
{exception_data.get('trace', 'No trace available')[:1000]}

**Similar Historical Cases:**
{similar_text}

Provide:
1. Root cause analysis
2. Why retries are failing
3. Recommended resolution based on similar cases
4. Priority (High/Medium/Low)"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self.chat_completion(messages, temperature=0.3, max_tokens=800)


def test_client():
    """Test the Azure OpenAI client."""
    import os

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")

    if not endpoint or not api_key:
        print("Error: Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY environment variables")
        return

    client = AzureOpenAIClient(
        endpoint=endpoint,
        api_key=api_key
    )

    # Test chat completion
    print("Testing chat completion...")
    response = client.chat_completion([
        {"role": "user", "content": "Say 'Hello, World!' in one sentence."}
    ])
    print(f"Response: {response}\n")

    # Test embedding
    print("Testing embedding generation...")
    embedding = client.generate_embedding("Test text for embedding")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    test_client()
