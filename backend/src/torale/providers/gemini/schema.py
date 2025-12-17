import json
import logging

from google import genai
from google.genai import types

from torale.core.config import settings
from torale.providers.schema_provider import SchemaProvider

logger = logging.getLogger(__name__)


class GeminiSchemaProvider(SchemaProvider):
    """
    Generates task-specific extraction schemas using Gemini.

    The schema defines what structured data to extract from search results
    for a specific monitoring task.
    """

    def __init__(self):
        if not settings.google_api_key:
            raise ValueError("Google API key required for Gemini schema provider")

        self.client = genai.Client(api_key=settings.google_api_key)
        # Note: Caching removed as providers are instantiated per-execution in distributed workers.
        # Consider adding Redis caching or singleton pattern if schema generation becomes a bottleneck.

    async def generate_schema(self, task: dict, model: str = "gemini-2.5-flash") -> dict:
        """
        Generate extraction schema for a monitoring task.

        Uses Gemini to analyze the task and determine what fields
        should be tracked.

        Args:
            task: Task configuration with search_query and condition_description
            model: Gemini model to use (default: gemini-2.5-flash)
        """
        search_query = task.get("search_query", "")
        condition_description = task.get("condition_description", "")

        prompt = f"""You are designing an extraction schema for a monitoring task.

Task Details:
- Search Query: {search_query}
- Condition: {condition_description}

Design a JSON schema that defines what structured fields to extract from search results.
The schema should capture the key facts needed to monitor this task over time.

Requirements:
1. Keep it simple - only 3-5 key fields
2. Each field should have: name, type (string|number|date|bool|enum), description
3. Fields should be deterministic and extractable from search results
4. Focus on facts that can change over time (dates, status, prices, etc.)

Example for "Monitor iPhone 16 release date":
{{
  "release_date": {{
    "type": "date",
    "description": "Official release date if announced"
  }},
  "confirmed": {{
    "type": "bool",
    "description": "Whether release date is officially confirmed by Apple"
  }},
  "product_name": {{
    "type": "string",
    "description": "Full product name"
  }}
}}

Design the schema for this task. Return ONLY the JSON schema, no other text."""

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        schema = json.loads(response.text)
        logger.info(f"Generated schema for task: {schema}")
        return schema

    async def get_or_create_schema(self, task: dict) -> dict:
        """
        Get or generate schema for task.

        In the future, this could check for persisted schemas in the database
        (task.extraction_schema field) before generating new ones.
        """
        # TODO: Check database for persisted schema (task.extraction_schema)
        # For now, generate fresh each time
        schema = await self.generate_schema(task)
        return schema
