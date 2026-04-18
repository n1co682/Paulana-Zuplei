import os

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_API_KEY = "AQ.Ab8RN6J02bBr8NIcgiTcxaNh0lC6G_n7mAI2cLCkJbIwaY_QMA"


class GeminiClient:
    """Encapsulates all google.genai / Vertex AI dependencies."""

    MODEL = "gemini-3.1-pro-preview"

    def __init__(self):
        from google import genai
        from google.genai import types

        self._types = types
        api_key = os.getenv("GOOGLE_API_KEY", _DEFAULT_API_KEY)

        self._client = genai.Client(vertexai=True, api_key=api_key)
        self._config_plain = types.GenerateContentConfig()
        self._config_search = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )

    def generate(self, prompt: str, web_search: bool = False) -> str:
        import logging
        logger = logging.getLogger("agnes.gemini")
        config = self._config_search if web_search else self._config_plain
        
        logger.debug(f"Attempting generation with model {self.MODEL}...")
        try:
            response = self._client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"Generation error in GeminiClient: {e}")
            raise
