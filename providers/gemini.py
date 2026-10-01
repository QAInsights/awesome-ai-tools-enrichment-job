import logging
import os
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from constants import GEMINI_MODEL, GEMINI_MODEL_BACKUP
from providers.base import ToolInfoProvider
from utils import build_prompt, extract_json, normalize_tool_profile

load_dotenv()
logger = logging.getLogger(__name__)


class GeminiProvider(ToolInfoProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.grounding_tool = types.Tool(google_search=types.GoogleSearch())
        self.config = types.GenerateContentConfig(
            tools=[self.grounding_tool],
            http_options=types.HttpOptions(timeout=120000),
        )

    def get_tool_profile(
        self, company_name: str, tool_name: str, slug: str, url: str = "", category: str = ""
    ) -> Dict[str, Any]:
        prompt = build_prompt(company_name, tool_name, slug, url, category)
        logger.info(prompt)
        response_text: Optional[str] = None
        for model in [GEMINI_MODEL, GEMINI_MODEL_BACKUP]:
            for attempt in range(1, 4):
                try:
                    logger.info("Using model: %s (attempt %s/3)", model, attempt)
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=self.config,
                    )
                    response_text = response.text
                    break
                except Exception as e:
                    error_str = str(e)
                    if "400" in error_str or "401" in error_str or "403" in error_str:
                        raise
                    if "503" in error_str or "UNAVAILABLE" in error_str:
                        logger.warning("Model %s unavailable (attempt %s/3): %s", model, attempt, e)
                        if attempt == 3:
                            if model == GEMINI_MODEL:
                                logger.info("Switching to backup model: %s", GEMINI_MODEL_BACKUP)
                                break
                            else:
                                raise
                        time.sleep(2 ** attempt)
                    else:
                        logger.warning("Attempt %s/3 failed for %s: %s", attempt, slug, e)
                        if attempt == 3:
                            raise
                        time.sleep(2 ** attempt)
            if response_text:
                break
        if not response_text:
            raise RuntimeError(f"Gemini failed to produce a response for {slug}")
        data = extract_json(response_text, slug)
        return normalize_tool_profile(data, slug, tool_name, company_name)
