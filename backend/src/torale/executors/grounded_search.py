import json
import logging
from datetime import UTC, datetime

from torale.core.config import settings
from torale.executors import TaskExecutor

logger = logging.getLogger(__name__)


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
            "last_execution_datetime": datetime,  # optional, datetime object for temporal context
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
        last_execution_datetime = config.get("last_execution_datetime")

        try:
            # Step 1: Perform grounded search with temporal context
            search_result = await self._grounded_search(
                search_query=search_query,
                model=model,
                last_execution_datetime=last_execution_datetime,
            )

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

    async def _grounded_search(
        self, search_query: str, model: str, last_execution_datetime: datetime | None = None
    ) -> dict:
        """
        Perform grounded search using Gemini with Google Search.

        Args:
            search_query: The search query
            model: Gemini model to use
            last_execution_datetime: Timezone-aware datetime of last successful execution (optional)

        Returns answer and grounding sources.
        """
        from google.genai import types

        # Add temporal context to search query
        current_datetime = datetime.now(UTC).strftime("%B %d, %Y at %I:%M %p UTC")

        if last_execution_datetime:
            # Format last execution time consistently
            last_execution_formatted = last_execution_datetime.strftime("%B %d, %Y at %I:%M %p UTC")
            last_date = last_execution_datetime.strftime("%B %d, %Y")  # Robust date extraction

            # Subsequent runs: prioritize information published since last check
            temporal_context = f"""CRITICAL TEMPORAL REQUIREMENT - YOU MUST FOLLOW THIS:
- Current date and time: {current_datetime}
- Last checked: {last_execution_formatted}
- YOU MUST ONLY report information that was published, announced, or updated AFTER {last_execution_formatted}
- IGNORE all information from before {last_execution_formatted}, even if it seems relevant
- If the search returns results from BEFORE {last_execution_formatted}, you must respond: "No new updates since last check on {last_execution_formatted}"
- DO NOT report events from August 2025 if we already checked in November 2025
- Focus your search specifically on: news after:{last_date}"""
        else:
            # First run: prioritize most recent information
            temporal_context = f"""IMPORTANT TEMPORAL CONTEXT:
- Current date and time: {current_datetime}
- This is the FIRST check
- Search for and prioritize the most RECENT and UP-TO-DATE information available
- Focus on latest news, announcements, and current status"""

        # Add instruction to be concise for email consumption
        compression_instruction = "Provide a CONCISE summary (2-4 sentences). Focus ONLY on key facts and recent developments."

        # Modify search query to include date filter for subsequent runs
        if last_execution_datetime:
            last_date = last_execution_datetime.strftime("%B %d, %Y")
            modified_query = f"{search_query} (published after {last_date} OR announced after {last_date} OR news after {last_date})"
        else:
            modified_query = search_query

        contextualized_query = (
            f"{temporal_context}\n\nQuery: {modified_query}\n\n{compression_instruction}"
        )

        # Log the query being sent to Gemini for debugging
        logger.info(
            f"Sending to Gemini with temporal context - Last execution: {last_execution_datetime}"
        )
        logger.info(f"Full query: {contextualized_query[:500]}...")  # Log first 500 chars

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
                            uri = getattr(chunk.web, "uri", "")
                            title = getattr(chunk.web, "title", "")

                            # Keep all grounding sources including Vertex AI redirect URLs
                            # The title from Gemini is just the domain (e.g., "britannica.com")
                            source = {
                                "url": uri,
                                "title": title or self._extract_domain_from_uri(uri),
                            }
                            grounding_sources.append(source)

        return {"answer": answer, "grounding_sources": grounding_sources}

    def _extract_domain_from_uri(self, uri: str) -> str:
        """
        Extract a clean domain name from a URI for display purposes.

        Handles Vertex AI redirect URLs like:
        https://vertexaisearch.cloud.google.com/grounding-api-redirect/...
        """
        try:
            from urllib.parse import urlparse

            parsed = urlparse(uri)
            domain = parsed.netloc or uri

            # Remove common prefixes
            for prefix in ["www.", "m."]:
                if domain.startswith(prefix):
                    domain = domain[len(prefix) :]

            return domain
        except Exception:
            return uri

    async def _evaluate_condition(
        self, search_query: str, search_answer: str, condition_description: str, model: str
    ) -> dict:
        """
        Use LLM to evaluate if condition is met based on search results.

        Returns condition_met (bool) and extracted current_state (dict) with timestamps.
        """
        from datetime import datetime

        from google.genai import types

        current_date = datetime.now(UTC).strftime("%Y-%m-%d")

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
        "_metadata": {{
            "captured_at": "{current_date}",
            "state_hash": "hash_of_key_fields"  // Simple hash/concat of main state fields for change detection
        }}
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

        Returns human-readable summary of what changed, or None if no meaningful changes detected.
        """
        from google.genai import types

        # Quick check: if state hashes match, no change
        prev_hash = previous_state.get("_metadata", {}).get("state_hash", "")
        curr_hash = current_state.get("_metadata", {}).get("state_hash", "")

        if prev_hash and curr_hash and prev_hash == curr_hash:
            # States are identical
            return None

        # Get previous capture date for temporal context
        prev_date = previous_state.get("_metadata", {}).get("captured_at", "unknown date")

        comparison_prompt = f"""Compare these two states and identify what factual information has CHANGED.

Previous State (from {prev_date}):
{json.dumps(previous_state, indent=2)}

Current State:
{json.dumps(current_state, indent=2)}

Has any factual information actually changed? Focus on:
- New announcements or confirmations that didn't exist before
- Changed dates, prices, specifications, or status
- Information that represents a REAL UPDATE, not just rephrasing

If NOTHING has meaningfully changed (just rephrased or still same info), respond with exactly: "No new changes detected."

Otherwise, provide a concise 1-2 sentence summary of what changed."""

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=comparison_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=200,
            ),
        )

        change_text = response.text.strip()

        # If LLM says no changes, return None
        if "no new changes" in change_text.lower() or "nothing has changed" in change_text.lower():
            return None

        return change_text
