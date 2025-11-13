"""
Simple request/response functions for Azure OpenAI API.

No classes, no wrappers - just direct HTTP requests using requests library.
"""

import requests
import time
from typing import List, Dict, Any, Optional


def _make_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    json_data: Dict[str, Any],
    timeout: int = 60,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Make HTTP request with retry logic.

    Args:
        method: HTTP method (POST, GET, etc.)
        url: Full URL
        headers: Request headers
        json_data: JSON payload
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        Response JSON

    Raises:
        Exception: If request fails after retries
    """
    for attempt in range(max_retries):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                timeout=timeout
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


def call_chat_completion(
    endpoint: str,
    api_key: str,
    api_version: str,
    deployment: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    """
    Call Azure OpenAI chat completion API.

    Args:
        endpoint: Azure OpenAI endpoint URL
        api_key: API key for authentication
        api_version: API version (e.g., "2024-02-15-preview")
        deployment: Deployment name (e.g., "gpt-4")
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens in response

    Returns:
        Response text content

    Example:
        response = call_chat_completion(
            endpoint="https://your-resource.openai.azure.com/",
            api_key="your-key",
            api_version="2024-02-15-preview",
            deployment="gpt-4",
            messages=[{"role": "user", "content": "Hello"}]
        )
    """
    endpoint = endpoint.rstrip('/')
    url = (
        f"{endpoint}/openai/deployments/{deployment}"
        f"/chat/completions?api-version={api_version}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    payload = {
        "messages": messages,
        "temperature": temperature
    }

    if max_tokens:
        payload["max_tokens"] = max_tokens

    result = _make_request("POST", url, headers, payload)
    return result["choices"][0]["message"]["content"]


def generate_embedding(
    endpoint: str,
    api_key: str,
    api_version: str,
    deployment: str,
    text: str
) -> List[float]:
    """
    Generate embedding for text using Azure OpenAI.

    Args:
        endpoint: Azure OpenAI endpoint URL
        api_key: API key for authentication
        api_version: API version
        deployment: Embedding deployment name (e.g., "text-embedding-ada-002")
        text: Text to embed

    Returns:
        Embedding vector (list of floats)

    Example:
        embedding = generate_embedding(
            endpoint="https://your-resource.openai.azure.com/",
            api_key="your-key",
            api_version="2024-02-15-preview",
            deployment="text-embedding-ada-002",
            text="Hello world"
        )
    """
    endpoint = endpoint.rstrip('/')
    url = (
        f"{endpoint}/openai/deployments/{deployment}"
        f"/embeddings?api-version={api_version}"
    )

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    payload = {
        "input": text
    }

    result = _make_request("POST", url, headers, payload)
    return result["data"][0]["embedding"]


def analyze_exception(
    endpoint: str,
    api_key: str,
    api_version: str,
    deployment: str,
    exception_data: Dict[str, Any],
    similar_cases: List[Dict[str, Any]],
    schema: str
) -> str:
    """
    Generate AI-powered exception analysis using chat completion.

    Args:
        endpoint: Azure OpenAI endpoint URL
        api_key: API key for authentication
        api_version: API version
        deployment: Chat deployment name (e.g., "gpt-4")
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
        f"Error: {case.get('metadata', {}).get('error_message', 'N/A')[:200]}\n"
        f"Type: {case.get('metadata', {}).get('exception_type', 'N/A')}\n"
        f"Resolution: {case.get('metadata', {}).get('remarks', 'No remarks available')}"
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

    return call_chat_completion(
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        deployment=deployment,
        messages=messages,
        temperature=0.3,
        max_tokens=800
    )
