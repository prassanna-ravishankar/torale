"""
OpenAI with web search approach.

Uses OpenAI's Responses API with web_search tool for real-time web information.

API Docs: https://platform.openai.com/docs/guides/tools-web-search
Models: gpt-5, gpt-5-mini, o4-mini, gpt-4.1, gpt-4.1-mini

Environment:
    OPENAI_API_KEY - Your OpenAI API key from https://platform.openai.com/account/api-keys
"""

import json
import os
from datetime import datetime

from openai import OpenAI


def _extract_usage(response) -> dict:
    """
    Extract token usage from OpenAI response with detailed breakdown.

    Handles both Responses API (input_tokens/output_tokens) and
    Chat Completions API (prompt_tokens/completion_tokens).
    """
    usage_obj = response.usage

    # Responses API uses input_tokens/output_tokens
    # Chat Completions API uses prompt_tokens/completion_tokens
    usage = {
        "input": getattr(usage_obj, "input_tokens", None) or getattr(usage_obj, "prompt_tokens", 0),
        "output": getattr(usage_obj, "output_tokens", None)
        or getattr(usage_obj, "completion_tokens", 0),
        "total": usage_obj.total_tokens,
    }

    # Add detailed token breakdown if available
    # Try Responses API field names first, then Chat Completions API
    input_details = getattr(usage_obj, "input_tokens_details", None) or getattr(
        usage_obj, "prompt_tokens_details", None
    )
    if input_details and hasattr(input_details, "cached_tokens"):
        usage["cache_read_input_tokens"] = input_details.cached_tokens

    output_details = getattr(usage_obj, "output_tokens_details", None) or getattr(
        usage_obj, "completion_tokens_details", None
    )
    if output_details and hasattr(output_details, "reasoning_tokens"):
        usage["reasoning_tokens"] = output_details.reasoning_tokens

    return usage


def _get_client():
    """Initialize OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Get one at https://platform.openai.com/account/api-keys"
        )
    return OpenAI(api_key=api_key)


def retrieve(query: str, model: str = "gpt-5-mini") -> dict:
    """
    Retrieve information using OpenAI Responses API with web search.

    Args:
        query: The search query
        model: OpenAI model (gpt-5-mini, gpt-5, o4-mini, gpt-4.1-mini)

    Returns:
        dict with keys:
            - answer: str - The answer from OpenAI with web search
            - sources: list[dict] - Web sources used
            - usage: dict - Token usage details for Langfuse tracking
    """
    client = _get_client()

    # Add current date/time context
    current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p %Z")
    contextualized_query = f"Current date and time: {current_datetime}. {query}"

    # Use Responses API with web_search tool
    response = client.responses.create(
        model=model,
        tools=[{"type": "web_search"}],
        input=contextualized_query,
        include=["web_search_call.action.sources"],  # Include all sources
    )

    # Extract answer from output
    answer = response.output_text

    # Extract sources - combine URLs from web_search_call with titles from annotations
    sources_map = {}  # url -> {url, title}

    # First pass: get URLs from web_search_call
    for item in response.output:
        if item.type == "web_search_call" and hasattr(item, "action"):
            if hasattr(item.action, "sources") and item.action.sources:
                for source in item.action.sources:
                    url = source.url
                    sources_map[url] = {"url": url, "title": ""}

    # Second pass: enrich with titles from message annotations
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if hasattr(content, "annotations") and content.annotations:
                    for annotation in content.annotations:
                        if annotation.type == "url_citation":
                            url = annotation.url
                            if url in sources_map:
                                sources_map[url]["title"] = annotation.title
                            else:
                                sources_map[url] = {
                                    "url": url,
                                    "title": annotation.title,
                                }

    sources = list(sources_map.values())

    # Extract token usage for Langfuse tracking
    usage = _extract_usage(response)

    return {
        "answer": answer,
        "sources": sources,
        "usage": usage,
        "model": response.model,  # Langfuse uses this for cost inference
    }


def evaluate(answer: str, condition: str, model: str = "gpt-4o") -> dict:
    """
    Evaluate if condition is met using OpenAI.

    Args:
        answer: The answer from retrieve step
        condition: The condition to evaluate
        model: OpenAI model to use

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
                "content": "You are an evaluator that determines if conditions are met. Always respond with valid JSON.",
            },
            {"role": "user", "content": evaluation_prompt},
        ],
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    # Extract token usage for Langfuse tracking
    usage = _extract_usage(response)

    return {
        "condition_met": result.get("condition_met", False),
        "reasoning": result.get("explanation", ""),
        "current_state": result.get("current_state", {}),
        "usage": usage,
        "model": model,  # Langfuse uses this for cost inference
    }
