"""
Perplexity API approach.

Perplexity provides a search-focused LLM API that returns answers with citations.
This approach uses Perplexity's API to both retrieve and evaluate conditions.

API Docs: https://docs.perplexity.ai/
Models: sonar, sonar-pro, sonar-reasoning (all have online search)

Environment:
    PERPLEXITY_API_KEY - Your Perplexity API key from https://www.perplexity.ai/settings/api
"""

import json
import os
from datetime import datetime

from openai import OpenAI


def _get_client():
    """Initialize Perplexity client (OpenAI-compatible)."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise ValueError(
            "PERPLEXITY_API_KEY not found. Get one at https://www.perplexity.ai/settings/api"
        )
    return OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")


def retrieve(query: str, model: str = "sonar") -> dict:
    """
    Retrieve information using Perplexity's search API.

    Args:
        query: The search query
        model: Perplexity model (sonar, sonar-pro, sonar-reasoning)

    Returns:
        dict with keys:
            - answer: str - The answer from Perplexity
            - sources: list[dict] - Citations from Perplexity
            - usage: dict - Token usage details for Langfuse tracking
    """
    client = _get_client()

    # Add current date/time context
    current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p %Z")
    contextualized_query = f"Current date and time: {current_datetime}. {query}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that provides accurate, concise answers based on web search results.",
            },
            {"role": "user", "content": contextualized_query},
        ],
        extra_body={"return_citations": True},  # Request citations
    )

    # Extract citations from response (Perplexity format)
    sources = []
    # Try to get citations from different possible locations
    if hasattr(response, "citations") and response.citations:
        for i, citation in enumerate(response.citations):
            sources.append(
                {
                    "url": citation if isinstance(citation, str) else citation.get("url", ""),
                    "title": f"Citation {i + 1}",
                    "snippet": "",
                }
            )
    # Check if citations are in the response data
    elif hasattr(response, "model_extra") and response.model_extra:
        citations = response.model_extra.get("citations", [])
        for i, citation in enumerate(citations):
            sources.append({"url": citation, "title": f"Citation {i + 1}", "snippet": ""})

    # Extract token usage for Langfuse tracking
    usage = {
        "input": response.usage.prompt_tokens,
        "output": response.usage.completion_tokens,
        "total": response.usage.total_tokens,
    }

    return {
        "answer": response.choices[0].message.content,
        "sources": sources,
        "usage": usage,
        "model": model,  # Perplexity not in Langfuse, but track anyway
    }


def evaluate(answer: str, condition: str, model: str = "sonar") -> dict:
    """
    Evaluate if condition is met using Perplexity.

    Args:
        answer: The answer from retrieve step
        condition: The condition to evaluate
        model: Perplexity model to use

    Returns:
        dict with keys:
            - condition_met: bool
            - reasoning: str
            - current_state: dict
            - usage: dict - Token usage details for Langfuse tracking
    """
    client = _get_client()

    evaluation_prompt = f"""Based on the information below, determine if the following condition is met.

Information:
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

Be precise - only set condition_met to true if the condition is definitively met based on the information."""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an evaluator that determines if conditions are met. Always respond with valid JSON only, no markdown formatting.",
            },
            {"role": "user", "content": evaluation_prompt},
        ],
    )

    # Parse JSON from response (Perplexity doesn't support response_format)
    content = response.choices[0].message.content.strip()
    # Remove markdown code blocks if present
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    elif content.startswith("```"):
        content = content.replace("```", "").strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON response from Perplexity. Content: {content[:200]}"
        ) from e

    # Extract token usage for Langfuse tracking
    usage = {
        "input": response.usage.prompt_tokens,
        "output": response.usage.completion_tokens,
        "total": response.usage.total_tokens,
    }

    return {
        "condition_met": result.get("condition_met", False),
        "reasoning": result.get("explanation", ""),
        "current_state": result.get("current_state", {}),
        "usage": usage,
        "model": model,  # Perplexity not in Langfuse, but track anyway
    }
