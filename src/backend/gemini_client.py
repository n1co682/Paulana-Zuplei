import json
import logging
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any

from dotenv import load_dotenv

logger = logging.getLogger("agnes.gemini")

load_dotenv()

class GeminiClient:
    """Encapsulates all google.genai / Vertex AI dependencies."""

    MODEL = "gemini-3-flash-preview"

    def __init__(
        self,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        base_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 8.0,
    ):
        from google import genai
        from google.genai import types

        self._types = types
        api_key = os.getenv("GOOGLE_API_KEY")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._base_backoff_seconds = base_backoff_seconds
        self._max_backoff_seconds = max_backoff_seconds

        self._client = genai.Client(vertexai=True, api_key=api_key)
        self._config_plain = types.GenerateContentConfig()
        self._config_search = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )

    def generate(self, prompt: str, web_search: bool = False) -> str:
        config = self._config_search if web_search else self._config_plain
        
        logger.debug(f"Attempting generation with model {self.MODEL}...")
        return self._generate_with_retry(prompt=prompt, config=config)

    def generate_json(self, prompt: str, response_schema: dict[str, Any], web_search: bool = False) -> dict | list:
        config_kwargs = {
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        }
        if web_search:
            config_kwargs["tools"] = [self._types.Tool(google_search=self._types.GoogleSearch())]
        config = self._types.GenerateContentConfig(**config_kwargs)
        text = self._generate_with_retry(prompt=prompt, config=config)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            preview = text[:400].replace("\n", " ")
            raise ValueError(f"Gemini returned non-JSON content: {preview}") from exc

    def _generate_with_retry(self, prompt: str, config: Any) -> str:
        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                prompt_snippet = (prompt[:100] + "...") if len(prompt) > 100 else prompt
                logger.info(f"Gemini attempt {attempt}/{self._max_retries} | Prompt: {prompt_snippet}")
                return self._generate_once(prompt=prompt, config=config)
            except Exception as exc:
                last_error = exc
                logger.warning(f"Attempt {attempt} failed: {exc}")
                if attempt >= self._max_retries:
                    break
                backoff = min(
                    self._max_backoff_seconds,
                    self._base_backoff_seconds * (2 ** (attempt - 1)),
                )
                jitter = random.uniform(0, backoff * 0.2)
                time.sleep(backoff + jitter)
        raise RuntimeError("Gemini request failed after retries") from last_error

    def _generate_once(self, prompt: str, config: Any) -> str:
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            future = pool.submit(
                self._client.models.generate_content,
                    model=self.MODEL,
                    contents=prompt,
                    config=config,
                )
            try:
                response = future.result(timeout=self._timeout_seconds)
            except FuturesTimeoutError as exc:
                future.cancel()
                raise TimeoutError(f"Gemini call timed out after {self._timeout_seconds}s") from exc
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        
        resp_text = response.text or ""
        logger.info(f"Gemini response received ({len(resp_text)} chars). Preview: {resp_text[:500]}...")
        return resp_text
