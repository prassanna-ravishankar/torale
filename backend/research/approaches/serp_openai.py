"""
SERP API + OpenAI approach.

Uses SerpAPI (or similar) to get Google Search results, then uses OpenAI
to synthesize answers and evaluate conditions.

This is a practical alternative to Gemini's built-in grounding, allowing
comparison of different LLMs for the evaluation step.

Services:
    - SerpAPI: https://serpapi.com/ (Google Search API)
    - Alternatives: ScaleSerp, Zenserp, Google Custom Search API

Installation:
    Add to pyproject.toml research dependencies:
    "google-search-results>=2.4.2"  # SerpAPI SDK

Environment:
    SERPAPI_API_KEY - Your SerpAPI key
    OPENAI_API_KEY - Your OpenAI API key
"""

import os

# TODO: Uncomment when implementing
# import json
# from serpapi import GoogleSearch
# from openai import OpenAI


def retrieve(query: str, model: str = "gpt-4o") -> dict:
    """
    Retrieve information using SerpAPI + OpenAI.

    Process:
    1. Use SerpAPI to get Google Search results
    2. Extract organic results (title, snippet, URL)
    3. Use OpenAI to synthesize answer from search results

    Args:
        query: The search query
        model: OpenAI model for synthesis

    Returns:
        dict with keys:
            - answer: str - Synthesized answer from OpenAI
            - sources: list[dict] - Search results from SerpAPI
            - tokens: int - OpenAI tokens used
    """
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not serpapi_key:
        raise ValueError("SERPAPI_API_KEY not found. Set it to use SERP approach.")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY not found. Set it to use SERP approach.")

    # TODO: Implement SerpAPI search
    # search = GoogleSearch({
    #     "q": query,
    #     "api_key": serpapi_key,
    #     "num": 10,  # Number of results
    # })
    # results = search.get_dict()
    #
    # # Extract organic results
    # sources = []
    # search_context = ""
    # for result in results.get("organic_results", [])[:5]:
    #     sources.append({
    #         "url": result.get("link", ""),
    #         "title": result.get("title", ""),
    #         "snippet": result.get("snippet", ""),
    #     })
    #     search_context += f"\n\n{result['title']}\n{result['snippet']}"
    #
    # # Use OpenAI to synthesize answer
    # client = OpenAI(api_key=openai_key)
    # response = client.chat.completions.create(
    #     model=model,
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": "You synthesize answers from search results.",
    #         },
    #         {
    #             "role": "user",
    #             "content": f"Query: {query}\n\nSearch Results:{search_context}\n\n"
    #             "Provide a concise answer based on these results.",
    #         },
    #     ],
    # )
    #
    # return {
    #     "answer": response.choices[0].message.content,
    #     "sources": sources,
    #     "tokens": response.usage.total_tokens,
    # }

    raise NotImplementedError("SERP + OpenAI approach not yet implemented")


def evaluate(answer: str, condition: str, model: str = "gpt-4o") -> dict:
    """
    Evaluate if condition is met using OpenAI.

    Args:
        answer: The answer from retrieve step
        condition: The condition to evaluate

    Returns:
        dict with keys:
            - condition_met: bool
            - reasoning: str
            - tokens: int
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY not found. Set it to use SERP approach.")

    # TODO: Implement evaluation
    # client = OpenAI(api_key=openai_key)
    # response = client.chat.completions.create(
    #     model=model,
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": "You evaluate if conditions are met based on information provided.",
    #         },
    #         {
    #             "role": "user",
    #             "content": f"Information: {answer}\n\nCondition: {condition}\n\n"
    #             "Is this condition met? Respond with JSON: "
    #             '{"condition_met": true/false, "explanation": "...", "current_state": {}}',
    #         },
    #     ],
    #     response_format={"type": "json_object"},
    # )
    #
    # result = json.loads(response.choices[0].message.content)
    # return {
    #     "condition_met": result.get("condition_met", False),
    #     "reasoning": result.get("explanation", ""),
    #     "tokens": response.usage.total_tokens,
    # }

    raise NotImplementedError("SERP + OpenAI evaluation not yet implemented")
