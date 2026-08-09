import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, Optional

from exa_py import Exa

from constants import DEFAULT_EXA_MAX_RETRIES, DEFAULT_EXA_MODEL, DEFAULT_EXA_NUM_RESULTS
from providers.base import ToolInfoProvider
from utils import extract_json, normalize_tool_profile

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_SCHEMA = {
    "type": "text",
    "description": (
        "Return a single valid JSON object for the tool profile, with no markdown, "
        "no code fences, and no commentary."
    ),
}

DEFAULT_SYSTEM_PROMPT = (
    "You are a precise data extraction assistant. Given the search results, return ONLY "
    "a valid JSON object for the AI coding tool with exactly these fields:\n"
    "- slug (string)\n"
    "- name (string)\n"
    "- company (string)\n"
    "- pricing (one of: free, freemium, paid, open-source)\n"
    "- pricingDetail (string)\n"
    "- description (2-3 sentence plain English)\n"
    "- keyFeatures (array of strings, up to 5)\n"
    "- bestFor (string)\n"
    "- notIdealFor (string)\n"
    "- recentUpdates (string)\n"
    "- verdict (string)\n"
    "- tags (array of strings)\n"
    "- lastUpdated (string YYYY-MM-DD)\n\n"
    "Use only information from the search results. Do not hallucinate pricing or features. "
    "If a value is unknown, use an empty string or empty array. "
    "Do not include markdown, backticks, or any explanation outside the JSON."
)


class ExaProvider(ToolInfoProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_EXA_MODEL,
        num_results: int = DEFAULT_EXA_NUM_RESULTS,
        max_retries: int = DEFAULT_EXA_MAX_RETRIES,
    ):
        self.api_key = api_key or os.getenv("EXA_API_KEY")
        self.model = model
        self.num_results = num_results
        self.max_retries = max_retries
        self._client: Optional[Exa] = None

    @property
    def client(self) -> Exa:
        if self._client is None:
            self._client = Exa(api_key=self.api_key)
        return self._client

    def get_tool_profile(self, company_name: str, tool_name: str, slug: str) -> Dict[str, Any]:
        query = self._build_query(company_name, tool_name, slug)
        logger.info("Exa query for %s: %s", slug, query)
        last_exception: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.search(
                    query=query,
                    type=self.model,
                    num_results=self.num_results,
                    contents={"highlights": True},
                    output_schema=DEFAULT_OUTPUT_SCHEMA,
                    system_prompt=DEFAULT_SYSTEM_PROMPT,
                )
                if response.cost_dollars:
                    logger.info("Exa cost for %s: $%.6f", slug, response.cost_dollars.total)
                raw = response.output.content if (response.output and response.output.content is not None) else ""
                logger.debug("Exa raw output for %s:\n%s", slug, raw)
                if isinstance(raw, dict):
                    data = raw
                else:
                    data = extract_json(raw, slug)
                current_date = datetime.now().strftime("%Y-%m-%d")
                return normalize_tool_profile(data, slug, tool_name, company_name, current_date)
            except Exception as e:
                last_exception = e
                logger.warning("Exa attempt %s/%s failed for %s: %s", attempt, self.max_retries, slug, e)
                if not self._should_retry(e, attempt):
                    raise
                time.sleep(2 ** attempt)
        raise last_exception or RuntimeError(f"Exa failed for {slug}")

    def _should_retry(self, e: Exception, attempt: int) -> bool:
        msg = str(e)
        if "NO_MORE_CREDITS" in msg or "API_KEY_BUDGET_EXCEEDED" in msg or "TEAM_BUDGET_EXCEEDED" in msg:
            return False
        match = re.search(r"Request failed with status code (\d{3})", msg)
        if match:
            status = int(match.group(1))
            if status == 429:
                return True
            if 400 <= status < 500:
                return False
            return True
        # JSON parsing or transient errors may be worth one retry.
        return attempt < self.max_retries

    def _build_query(self, company_name: str, tool_name: str, slug: str) -> str:
        return (
            f"Find the latest information about {tool_name} by {company_name} "
            f"(also known as {slug}). What is its pricing model, key features, "
            f"best use cases, not ideal use cases, recent updates, and a short verdict?"
        )
