from typing import Any, Dict, List, Optional
import aiohttp
import json  # For potential JSON parsing errors
import logging  # Import logging

from app.services.ai_integrations.interface import AIModelInterface
from app.core.config import get_settings

# Potentially import openai library here if you install it
# import openai

settings = get_settings()
logger = logging.getLogger(__name__)  # Get logger instance

# OpenAI API constants (replace with actual or make configurable)
OPENAI_API_URL_EMBEDDINGS = "https://api.openai.com/v1/embeddings"
OPENAI_API_URL_CHAT_COMPLETIONS = "https://api.openai.com/v1/chat/completions"

DEFAULT_EMBEDDING_MODEL = (
    "text-embedding-ada-002"  # Or a newer model like text-embedding-3-small
)
DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"  # Or a newer/more capable model


class OpenAIClient(AIModelInterface):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            logger.critical(
                "OpenAI API key is required but not found. Set OPENAI_API_KEY in environment."
            )
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY in environment."
            )
        # Initialize the OpenAI client library here if needed
        # openai.api_key = self.api_key
        self.model_name = (
            "openai"  # Generic identifier, specific models used in methods
        )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        logger.info("OpenAIClient initialized.")

    async def _make_openai_request(self, url: str, payload: Dict) -> Dict:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                logger.debug(
                    f"Sending request to OpenAI API: {url} with payload: {json.dumps(payload)[:200]}..."
                )
                response = await session.post(url, json=payload)  # Await first
                response.raise_for_status()  # Then check
                return await response.json()
            except aiohttp.ClientError as e:
                logger.error(
                    f"AIOHTTP client error with OpenAI API ({url}): {e}", exc_info=True
                )
                raise ConnectionError(f"Failed to connect to OpenAI API: {e}") from e
            except json.JSONDecodeError as e:
                logger.error(
                    f"JSON decode error from OpenAI API ({url}): {e}. Status: {response.status if 'response' in locals() else 'N/A'}",
                    exc_info=True,
                )
                raise ValueError(
                    f"Failed to parse JSON response from OpenAI API: {e}"
                ) from e

    async def refine_query(self, raw_query: str, **kwargs) -> str:
        model_to_use = kwargs.get("model", DEFAULT_CHAT_MODEL)
        logger.warning(
            f"OpenAIClient.refine_query called for '{raw_query[:50]}...' with model {model_to_use} but is not primary. kwargs: {kwargs}"
        )
        raise NotImplementedError(
            "OpenAIClient.refine_query is not the primary task for this client as per current plan."
        )

    async def identify_sources(self, refined_query: str, **kwargs) -> List[str]:
        logger.warning(
            f"OpenAIClient.identify_sources called for '{refined_query[:50]}...' but is not suitable. kwargs: {kwargs}"
        )
        raise NotImplementedError(
            "OpenAIClient.identify_sources is not suitable for this client."
        )

    async def generate_embeddings(
        self, texts: List[str], **kwargs
    ) -> List[List[float]]:
        model_to_use = kwargs.get("model", DEFAULT_EMBEDDING_MODEL)
        payload = {
            "input": texts,
            "model": model_to_use,
            **kwargs.get(
                "api_params", {}
            ),  # For other params like encoding_format, dimensions
        }

        logger.info(
            f"Generating {len(texts)} embeddings with OpenAI model: {model_to_use}."
        )
        response_data = await self._make_openai_request(
            OPENAI_API_URL_EMBEDDINGS, payload
        )

        try:
            embeddings = [item["embedding"] for item in response_data["data"]]
            if not embeddings or len(embeddings) != len(texts):
                logger.error(
                    f"Mismatch in number of embeddings returned ({len(embeddings)}) vs texts ({len(texts)}) from OpenAI or empty list."
                )
                raise ValueError(
                    "Mismatch in number of embeddings returned or empty embeddings list."
                )
            logger.info(f"Successfully generated {len(embeddings)} embeddings.")
            return embeddings
        except (KeyError, IndexError, TypeError) as e:
            logger.error(
                f"Error parsing embeddings from OpenAI response. Response: {response_data}",
                exc_info=True,
            )
            raise ValueError(
                "Invalid response structure from OpenAI API for generate_embeddings."
            ) from e

    async def analyze_diff(
        self, old_representation: Any, new_representation: Any, **kwargs
    ) -> Dict:
        model_to_use = kwargs.get("model", DEFAULT_CHAT_MODEL)
        system_prompt = kwargs.get(
            "system_prompt",
            "You are a content change analysis assistant. Analyze the key differences between the old and new content provided. "
            "Respond with a JSON object containing two keys: 'summary' (a brief text summary of changes) and 'details' (a more structured object or text detailing specific changes if possible).",
        )
        user_prompt = f"Old content:\n```\n{str(old_representation)}\n```\n\nNew content:\n```\n{str(new_representation)}\n```"

        payload = {
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs.get("api_params", {}),
        }

        logger.info(f"Analyzing diff with OpenAI model: {model_to_use}.")
        response_data = await self._make_openai_request(
            OPENAI_API_URL_CHAT_COMPLETIONS, payload
        )

        try:
            assistant_response_content = response_data["choices"][0]["message"][
                "content"
            ].strip()
            # Check if JSON was requested in the actual payload sent
            if payload.get("response_format") == {"type": "json_object"}:
                try:
                    analysis_dict = json.loads(assistant_response_content)
                    if (
                        not isinstance(analysis_dict, dict)
                        or "summary" not in analysis_dict
                    ):
                        logger.warning(
                            f"OpenAI diff analysis JSON missing 'summary' key or not a dict. Content: {assistant_response_content}"
                        )
                        return {
                            "summary": "Failed to parse structured JSON from AI.",
                            "raw_response": assistant_response_content,
                            "details": {},
                        }
                    logger.info("Successfully parsed JSON diff analysis from OpenAI.")
                    return analysis_dict
                except json.JSONDecodeError as json_e:
                    logger.error(
                        f"Failed to parse analyze_diff response as JSON from OpenAI. Raw: {assistant_response_content}",
                        exc_info=True,
                    )
                    return {
                        "summary": "AI response was not valid JSON.",
                        "raw_response": assistant_response_content,
                        "details": {},
                    }
            else:
                # If JSON not requested, return the raw text as summary
                logger.info(
                    "OpenAI diff analysis returned raw text (JSON not explicitly requested)."
                )
                return {"summary": assistant_response_content, "details": {}}

        except (KeyError, IndexError, TypeError) as e:
            logger.error(
                f"Error parsing diff analysis from OpenAI response. Response: {response_data}",
                exc_info=True,
            )
            raise ValueError(
                "Invalid response structure from OpenAI API for analyze_diff."
            ) from e
