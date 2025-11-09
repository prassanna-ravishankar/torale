"""
Stub approach for testing the harness.

This approach returns dummy data without making any API calls.
Useful for verifying the harness works correctly before implementing real approaches.
"""


def retrieve(query: str) -> dict:
    """
    Stub retrieval function - returns dummy answer and sources.

    Args:
        query: The search query

    Returns:
        dict with keys:
            - answer: str - The synthesized answer
            - sources: list[dict] - List of source URLs and metadata
            - usage: dict - Token usage details for Langfuse tracking
    """
    return {
        "answer": f"This is a stub answer for query: '{query}'. "
        "In a real implementation, this would contain information "
        "retrieved from Google Search, Perplexity, or other sources.",
        "sources": [
            {
                "url": "https://example.com/article1",
                "title": "Example Article 1",
                "snippet": "Relevant information from article 1...",
            },
            {
                "url": "https://example.com/article2",
                "title": "Example Article 2",
                "snippet": "Relevant information from article 2...",
            },
        ],
        "usage": {"input": 50, "output": 100, "total": 150},
        "model": "stub-model",  # Dummy model for testing
    }


def evaluate(answer: str, condition: str) -> dict:
    """
    Stub evaluation function - returns dummy condition assessment.

    Args:
        answer: The answer from the retrieve step
        condition: The condition to evaluate

    Returns:
        dict with keys:
            - condition_met: bool - Whether the condition is satisfied
            - reasoning: str - Explanation of the decision
            - current_state: dict - Extracted state information
            - usage: dict - Token usage details for Langfuse tracking
    """
    # Simple heuristic for stub: return False for questions about future events,
    # True for past events. This is just to create some variation in results.
    future_keywords = ["next", "will", "going to", "future", "upcoming", "2025", "2026"]
    has_future_keyword = any(keyword in condition.lower() for keyword in future_keywords)

    return {
        "condition_met": not has_future_keyword,  # Inverse of future detection
        "reasoning": (
            f"Stub evaluation: Detected {'future' if has_future_keyword else 'current/past'} "
            f"condition. In a real implementation, this would analyze the answer against "
            f"the condition using an LLM."
        ),
        "current_state": {},
        "usage": {"input": 30, "output": 70, "total": 100},
        "model": "stub-model",  # Dummy model for testing
    }
