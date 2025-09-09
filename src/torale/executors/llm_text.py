import asyncio
from typing import Any

import anthropic
import openai

from torale.core.config import settings
from torale.executors import TaskExecutor


class LLMTextExecutor(TaskExecutor):
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.google_client = None
        
        if settings.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        
        if settings.google_api_key:
            from google import genai
            self.google_client = genai.Client(api_key=settings.google_api_key)
    
    def validate_config(self, config: dict) -> bool:
        required_fields = ["prompt", "model"]
        return all(field in config for field in required_fields)
    
    async def execute(self, config: dict) -> dict:
        if not self.validate_config(config):
            raise ValueError("Invalid configuration: missing required fields")
        
        prompt = config["prompt"]
        model = config["model"]
        max_tokens = config.get("max_tokens", 1000)
        temperature = config.get("temperature", 0.7)
        
        try:
            if model.startswith("gpt"):
                if not self.openai_client:
                    raise ValueError("OpenAI API key not configured")
                result = await self._execute_openai(prompt, model, max_tokens, temperature)
            elif model.startswith("claude"):
                if not self.anthropic_client:
                    raise ValueError("Anthropic API key not configured")
                result = await self._execute_anthropic(prompt, model, max_tokens, temperature)
            elif model.startswith("gemini"):
                if not self.google_client:
                    raise ValueError("Google API key not configured")
                result = await self._execute_gemini(prompt, model, max_tokens, temperature)
            else:
                raise ValueError(f"Unsupported model: {model}")
            
            return {
                "success": True,
                "content": result,
                "model": model,
                "prompt": prompt,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": model,
                "prompt": prompt,
            }
    
    async def _execute_openai(
        self, prompt: str, model: str, max_tokens: int, temperature: float
    ) -> str:
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content
    
    async def _execute_anthropic(
        self, prompt: str, model: str, max_tokens: int, temperature: float
    ) -> str:
        response = await self.anthropic_client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.content[0].text
    
    async def _execute_gemini(
        self, prompt: str, model: str, max_tokens: int, temperature: float
    ) -> str:
        from google.genai import types
        
        response = await self.google_client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
        )
        return response.text