import logging
from datetime import UTC, datetime

from google import genai
from google.genai import types
from google.genai.types import GoogleSearch, Tool

from torale.core.config import settings

logger = logging.getLogger(__name__)


class GeminiSearchProvider:
    """
    Performs grounded search using Gemini with Google Search.

    Extracted from GroundedSearchExecutor to be used independently
    in the pipeline architecture.
    """

    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("Google API key required for Gemini search provider")

        self.client = genai.Client(api_key=settings.google_api_key)
        self.search_tool = Tool(google_search=GoogleSearch())

    async def search(
        self,
        query: str,
        temporal_context: dict | None = None,
        model: str = "gemini-2.5-flash",
    ) -> dict:
        """
        Perform grounded search with temporal context.

        Args:
            query: Search query
            temporal_context: Optional dict with last_execution_datetime
            model: Gemini model to use

        Returns:
            Dict with:
                - answer: Search result answer
                - sources: List of grounding sources
                - temporal_note: Note about temporal filtering (if applicable)
        """
        last_execution_datetime = (
            temporal_context.get("last_execution_datetime") if temporal_context else None
        )

        # Build temporal context
        current_datetime = datetime.now(UTC).strftime("%B %d, %Y at %I:%M %p UTC")

        if last_execution_datetime:
            # Format last execution time consistently
            last_execution_formatted = last_execution_datetime.strftime("%B %d, %Y at %I:%M %p UTC")
            last_date = last_execution_datetime.strftime("%B %d, %Y")

            # Subsequent runs: prioritize information published since last check
            temporal_instruction = f"""CRITICAL TEMPORAL REQUIREMENT - YOU MUST FOLLOW THIS:
- Current date and time: {current_datetime}
- Last checked: {last_execution_formatted}
- YOU MUST ONLY report information that was published, announced, or updated AFTER {last_execution_formatted}
- IGNORE all information from before {last_execution_formatted}, even if it seems relevant
- If the search returns results from BEFORE {last_execution_formatted}, you must respond: "No new updates since last check on {last_execution_formatted}"
- DO NOT report events from August 2025 if we already checked in November 2025
- Focus your search specifically on: news after:{last_date}"""

            # Modify search query to include date filter
            modified_query = f"{query} (published after {last_date} OR announced after {last_date} OR news after {last_date})"
        else:
            # First run: prioritize most recent information
            temporal_instruction = f"""IMPORTANT TEMPORAL CONTEXT:
- Current date and time: {current_datetime}
- This is the FIRST check
- Search for and prioritize the most RECENT and UP-TO-DATE information available
- Focus on latest news, announcements, and current status"""

            modified_query = query

        # Add compression instruction
        compression_instruction = "Provide a CONCISE summary (2-4 sentences). Focus ONLY on key facts and recent developments."

        contextualized_query = (
            f"{temporal_instruction}\n\nQuery: {modified_query}\n\n{compression_instruction}"
        )

        # Log for debugging
        logger.info(f"Sending to Gemini - Last execution: {last_execution_datetime}")
        logger.debug(f"Full query: {contextualized_query[:500]}...")

        # Execute search
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contextualized_query,
            config=types.GenerateContentConfig(
                tools=[self.search_tool],
                response_modalities=["TEXT"],
            ),
        )

        answer = response.text

        # Extract grounding sources
        grounding_sources = self._extract_sources(response)

        return {
            "answer": answer,
            "sources": grounding_sources,
            "temporal_note": "No new updates" if "No new updates" in answer else None,
        }

    def _extract_sources(self, response) -> list[dict]:
        """Extract grounding sources from Gemini response."""
        sources = []

        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata

                if hasattr(metadata, "grounding_chunks") and metadata.grounding_chunks:
                    for chunk in metadata.grounding_chunks:
                        if hasattr(chunk, "web") and chunk.web:
                            uri = getattr(chunk.web, "uri", "")
                            title = getattr(chunk.web, "title", "")

                            source = {
                                "url": uri,
                                "title": title or self._extract_domain_from_uri(uri),
                            }
                            sources.append(source)

        return sources

    def _extract_domain_from_uri(self, uri: str) -> str:
        """Extract clean domain name from URI by removing common subdomains."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(uri)
            domain = parsed.netloc or uri

            # Remove common subdomains for cleaner display
            # This includes mobile (m.), www, blog, shop, news, and other common prefixes
            common_subdomains = [
                "www.",
                "m.",
                "mobile.",
                "blog.",
                "shop.",
                "news.",
                "api.",
                "docs.",
                "support.",
            ]

            for subdomain in common_subdomains:
                if domain.startswith(subdomain):
                    domain = domain[len(subdomain) :]
                    break  # Only remove first matching subdomain

            return domain
        except Exception:
            return uri
