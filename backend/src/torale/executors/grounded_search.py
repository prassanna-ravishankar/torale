import json

from torale.core.config import settings
from torale.executors import TaskExecutor


class GroundedSearchExecutor(TaskExecutor):
    """
    Executor for grounded search monitoring tasks.

    Uses Google Search via Gemini grounding to:
    1. Search for current information based on search_query
    2. Evaluate if condition_description is met
    3. Track state changes to prevent duplicate notifications
    4. Extract grounding sources for attribution
    """

    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("Google API key required for grounded search")

        from google import genai
        from google.genai.types import GoogleSearch, Tool

        self.client = genai.Client(api_key=settings.google_api_key)
        self.search_tool = Tool(google_search=GoogleSearch())

    def validate_config(self, config: dict) -> bool:
        """Validate configuration has required fields"""
        required_fields = ["search_query", "condition_description"]
        return all(field in config for field in required_fields)

    async def execute(self, config: dict) -> dict:
        """
        Execute grounded search and evaluate condition.

        Config format:
        {
            "search_query": "When is next iPhone release?",
            "condition_description": "A specific date has been announced",
            "model": "gemini-2.5-flash",  # optional
            "last_known_state": {...},  # optional, for state comparison
        }

        Returns:
        {
            "success": True,
            "answer": "The next iPhone will be released...",
            "condition_met": True,
            "change_summary": "Release date changed from unknown to September 12",
            "grounding_sources": [
                {
                    "url": "https://example.com",
                    "title": "Apple announces iPhone 15",
                    "snippet": "..."
                }
            ],
            "current_state": {
                "release_date": "September 12, 2024",
                "confirmed": true
            }
        }
        """
        if not self.validate_config(config):
            raise ValueError("Invalid configuration: missing search_query or condition_description")

        search_query = config["search_query"]
        condition_description = config["condition_description"]
        model = config.get("model", "gemini-2.5-flash")
        last_known_state = config.get("last_known_state")

        try:
            # Step 1: Perform grounded search
            search_result = await self._grounded_search(search_query=search_query, model=model)

            # Step 2: Evaluate if condition is met
            condition_result = await self._evaluate_condition(
                search_query=search_query,
                search_answer=search_result["answer"],
                condition_description=condition_description,
                model=model,
            )

            # Step 3: Compare with last known state (if provided)
            change_summary = None
            if last_known_state and condition_result["condition_met"]:
                change_summary = await self._compare_states(
                    previous_state=last_known_state,
                    current_state=condition_result["current_state"],
                    model=model,
                )

            return {
                "success": True,
                "answer": search_result["answer"],
                "condition_met": condition_result["condition_met"],
                "change_summary": change_summary,
                "grounding_sources": search_result["grounding_sources"],
                "current_state": condition_result["current_state"],
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "search_query": search_query,
                "condition_description": condition_description,
            }

    async def _grounded_search(self, search_query: str, model: str) -> dict:
        """
        Perform grounded search using Gemini with Google Search.

        Returns answer and grounding sources.
        """
        from datetime import datetime

        from google.genai import types

        # Add current date and time context to search query
        current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p %Z")
        contextualized_query = f"Current date and time: {current_datetime}. {search_query}"

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contextualized_query,
            config=types.GenerateContentConfig(
                tools=[self.search_tool],
                response_modalities=["TEXT"],
            ),
        )

        answer = response.text

        # Extract grounding sources from response
        grounding_sources = []
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata
                if hasattr(metadata, "search_entry_point") and metadata.search_entry_point:
                    # Extract web search queries used
                    pass

                if hasattr(metadata, "grounding_chunks") and metadata.grounding_chunks:
                    for chunk in metadata.grounding_chunks:
                        if hasattr(chunk, "web") and chunk.web:
                            source = {
                                "url": getattr(chunk.web, "uri", ""),
                                "title": getattr(chunk.web, "title", ""),
                            }
                            grounding_sources.append(source)

        return {"answer": answer, "grounding_sources": grounding_sources}

    async def _evaluate_condition(
        self, search_query: str, search_answer: str, condition_description: str, model: str
    ) -> dict:
        """
        Use LLM to evaluate if condition is met based on search results.

        Returns condition_met (bool) and extracted current_state (dict).
        """
        from google.genai import types

        evaluation_prompt = f"""Based on the search results below, determine if the following condition is met.

Search Query: {search_query}

Search Results:
{search_answer}

Condition to Check: {condition_description}

Please respond in JSON format:
{{
    "condition_met": true/false,
    "explanation": "Brief explanation of why condition is/isn't met",
    "current_state": {{
        // Extract key facts as structured data
        // For example: {{"release_date": "September 12", "confirmed": true}}
    }}
}}

Be precise - only set condition_met to true if the condition is definitively met based on the search results."""

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=evaluation_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        result = json.loads(response.text)

        return {
            "condition_met": result.get("condition_met", False),
            "explanation": result.get("explanation", ""),
            "current_state": result.get("current_state", {}),
        }

    async def _compare_states(self, previous_state: dict, current_state: dict, model: str) -> str:
        """
        Compare previous and current states to generate change summary.

        Returns human-readable summary of what changed.
        """
        from google.genai import types

        comparison_prompt = f"""Compare these two states and summarize what changed in 1-2 sentences.

Previous State:
{json.dumps(previous_state, indent=2)}

Current State:
{json.dumps(current_state, indent=2)}

Provide a concise summary of the key changes (e.g., "Release date changed from unknown to September 12, 2024")."""

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=comparison_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=200,
            ),
        )

        return response.text.strip()
