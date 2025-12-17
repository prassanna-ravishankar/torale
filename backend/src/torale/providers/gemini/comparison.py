import json
import logging

from google import genai
from google.genai import types

from torale.core.config import settings
from torale.core.models import StateChange
from torale.providers.comparison_provider import ComparisonProvider
from torale.providers.gemini.utils import format_schema_for_prompt

logger = logging.getLogger(__name__)


class GeminiComparisonProvider(ComparisonProvider):
    """
    Compares states semantically using Gemini.

    Handles semantic equivalence (e.g., "Sept 12" == "September 12")
    while working with structured data.
    """

    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("Google API key required for Gemini comparison provider")

        self.client = genai.Client(api_key=settings.google_api_key)

    async def compare(
        self,
        previous_state: dict | None,
        current_state: dict,
        schema: dict,
        model: str = "gemini-2.5-flash",
    ) -> dict:
        """
        Compare states semantically to detect meaningful changes.

        Returns StateChange with changed flag and explanation.

        Args:
            previous_state: Previous extracted state (None for first execution)
            current_state: Current extracted state
            schema: Schema defining the fields
            model: Gemini model to use (default: gemini-2.5-flash)
        """
        if previous_state is None:
            return {
                "changed": True,
                "explanation": "First execution - no previous state to compare",
            }

        # Build comparison prompt
        schema_context = format_schema_for_prompt(schema)

        prompt = f"""Compare these two states and determine if there's a MEANINGFUL change.

Schema Context:
{schema_context}

Previous State:
{json.dumps(previous_state, indent=2)}

Current State:
{json.dumps(current_state, indent=2)}

Rules:
1. Semantic equivalence: "Sept 12, 2024" == "September 12, 2024" (NOT a change)
2. Null to value: null → "2024-09-12" (IS a change)
3. Value change: "2024-09-12" → "2024-09-15" (IS a change)
4. Focus on MEANINGFUL changes that matter to the user
5. Ignore formatting differences, capitalization, etc.

Return JSON:
{{
  "changed": true/false,
  "explanation": "Brief explanation of what changed or why nothing changed"
}}"""

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StateChange,
            ),
        )

        result = json.loads(response.text)
        logger.info(f"State comparison: {result}")

        return result
