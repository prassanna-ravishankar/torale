"""
Gemini grounded search approach (baseline).

This is the current production approach - uses Google Search via Gemini's
grounding feature to retrieve information and evaluate conditions.

Based on: torale.executors.grounded_search.GroundedSearchExecutor
"""

import json
import os
from datetime import datetime

from google import genai
from google.genai import types
from google.genai.types import GoogleSearch, Tool


def _get_client():
    """Initialize Gemini client with API key from environment."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in environment. "
            "Set it to use the Gemini grounded search approach."
        )
    return genai.Client(api_key=api_key)


def retrieve(query: str, model: str = "gemini-2.5-flash-lite") -> dict:
    """
    Retrieve information using Gemini with Google Search grounding.

    Args:
        query: The search query
        model: Gemini model to use (default: gemini-2.5-flash-lite)

    Returns:
        dict with keys:
            - answer: str - The synthesized answer from Gemini
            - sources: list[dict] - Grounding sources (URLs, titles)
            - usage: dict - Token usage details for Langfuse tracking
            - model: str - Actual model used
    """
    client = _get_client()
    search_tool = Tool(google_search=GoogleSearch())

    # Add current date/time context
    current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p %Z")
    contextualized_query = f"Current date and time: {current_datetime}. {query}"

    response = client.models.generate_content(
        model=model,
        contents=contextualized_query,
        config=types.GenerateContentConfig(
            tools=[search_tool],
            response_modalities=["TEXT"],
        ),
    )

    answer = response.text

    # Extract grounding sources
    grounding_sources = []
    if hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
            metadata = candidate.grounding_metadata
            if hasattr(metadata, "grounding_chunks") and metadata.grounding_chunks:
                for chunk in metadata.grounding_chunks:
                    if hasattr(chunk, "web") and chunk.web:
                        source = {
                            "url": getattr(chunk.web, "uri", ""),
                            "title": getattr(chunk.web, "title", ""),
                            "snippet": "",  # Gemini doesn't provide snippets in grounding metadata
                        }
                        grounding_sources.append(source)

    # Extract token usage for Langfuse tracking
    usage = {"input": 0, "output": 0, "total": 0}
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        usage_meta = response.usage_metadata
        usage = {
            "input": getattr(usage_meta, "prompt_token_count", 0),
            "output": getattr(usage_meta, "candidates_token_count", 0),
            "total": getattr(usage_meta, "total_token_count", 0),
        }

    return {
        "answer": answer,
        "sources": grounding_sources,
        "usage": usage,
        "model": model,  # Langfuse uses this for cost inference
    }


def evaluate(answer: str, condition: str, model: str = "gemini-2.5-flash-lite") -> dict:
    """
    Evaluate if a condition is met based on the retrieved answer.

    Args:
        answer: The answer from the retrieve step
        condition: The condition description to evaluate
        model: Gemini model to use (default: gemini-2.5-flash-lite)

    Returns:
        dict with keys:
            - condition_met: bool - Whether the condition is satisfied
            - reasoning: str - Explanation of the decision
            - current_state: dict - Extracted state information
            - usage: dict - Token usage details for Langfuse tracking
            - model: str - Actual model used
    """
    client = _get_client()

    evaluation_prompt = f"""Based on the search results below, determine if the following condition is met.

Search Results:
{answer}

Condition to Check: {condition}

Please respond in JSON format:
{{
    "condition_met": true/false,
    "explanation": "Brief explanation of why condition is/isn't met",
    "current_state": {{
        // Extract key facts as structured data
    }}
}}

Be precise - only set condition_met to true if the condition is definitively met based on the search results."""

    response = client.models.generate_content(
        model=model,
        contents=evaluation_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response from Gemini: {e}") from e

    # Extract token usage for Langfuse tracking
    usage = {"input": 0, "output": 0, "total": 0}
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        usage_meta = response.usage_metadata
        usage = {
            "input": getattr(usage_meta, "prompt_token_count", 0),
            "output": getattr(usage_meta, "candidates_token_count", 0),
            "total": getattr(usage_meta, "total_token_count", 0),
        }

    return {
        "condition_met": result.get("condition_met", False),
        "reasoning": result.get("explanation", ""),
        "current_state": result.get("current_state", {}),
        "usage": usage,
        "model": model,  # Langfuse uses this for cost inference
    }
