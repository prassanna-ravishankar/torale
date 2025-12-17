import json
import logging

from google import genai
from google.genai import types

from torale.core.config import settings
from torale.providers.extraction_provider import ExtractionProvider
from torale.providers.gemini.utils import format_schema_for_prompt

logger = logging.getLogger(__name__)


class GeminiExtractionProvider(ExtractionProvider):
    """
    Extracts structured data from search results using Gemini.

    Uses the schema to guide extraction, ensuring consistent structure
    across executions.
    """

    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("Google API key required for Gemini extraction provider")

        self.client = genai.Client(api_key=settings.google_api_key)

    async def extract(
        self, search_result: dict, schema: dict, model: str = "gemini-2.5-flash"
    ) -> dict:
        """
        Extract structured data from search result according to schema.

        Uses Gemini to parse the search answer into the defined schema fields.

        Args:
            search_result: Search result containing answer field
            schema: Schema defining fields to extract
            model: Gemini model to use (default: gemini-2.5-flash)
        """
        answer = search_result.get("answer", "")

        # Build prompt with schema
        schema_description = format_schema_for_prompt(schema)

        prompt = f"""Extract structured data from the search result below.

Search Result:
{answer}

Extraction Schema:
{schema_description}

Extract the data according to the schema. If a field cannot be determined from the search result, set it to null.
Return ONLY valid JSON matching the schema fields. Do not include any explanation."""

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        extracted_data = json.loads(response.text)
        logger.info(f"Extracted data: {extracted_data}")

        return extracted_data
