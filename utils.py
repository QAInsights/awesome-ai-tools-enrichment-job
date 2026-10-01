import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from constants import REQUIRED_PROFILE_FIELDS, VALID_PRICING

CITATION_MARKER = re.compile(r"\s*\[\d+(?:\s*[,\u2013-]\s*\d+)*\]")


def strip_citations(value: Any) -> Any:
    """Remove search-result citation markers such as "[5][2]" from profile text."""
    if isinstance(value, str):
        return CITATION_MARKER.sub("", value).strip()
    if isinstance(value, list):
        return [strip_citations(item) for item in value]
    return value


def download_json():
    url = "https://raw.githubusercontent.com/QAInsights/awesome-ai-tools/refs/heads/main/data/slugs.json"
    import requests

    response = requests.get(url)
    with open("slugs.json", "w") as f:
        f.write(response.text)


def build_prompt(company_name: str, tool_name: str, slug: str) -> str:
    current_date = datetime.now().strftime("%Y-%m-%d")
    return f"""
        You are writing a tool profile for ai.dosa.dev,
        a curated directory of AI coding tools for developers.

        Tool name: {tool_name}
        Company: {company_name}

        Use Google Search to find the latest information about this tool: pricing, features, recent updates.

        You can also check the GitHub repository for the tool to find the latest information about the tool.

        DO NOT hallucinate pricing, features, recent updates.

        Return ONLY valid JSON, no markdown, no backticks:
        {{
            "slug": "{slug}",
            "name": "{tool_name}",
            "company": "{company_name}",
            "pricing": "free|freemium|paid|open-source",
            "pricingDetail": "string",
            "description": "2-3 sentence plain English description",
            "keyFeatures": ["string", "string", "string"],
            "bestFor": "string",
            "notIdealFor": "string",
            "recentUpdates": "string",
            "verdict": "string",
            "tags": ["string"],
            "lastUpdated": "{current_date}"
        }}
"""


def extract_json(text: Any, slug: str) -> Dict[str, Any]:
    """Extract the first JSON object from a text block, tolerating markdown fences."""
    if isinstance(text, dict):
        return text
    if not isinstance(text, str):
        text = str(text)
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in output for {slug}")
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in output for {slug}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"Output for {slug} is not a JSON object")
    return data


def normalize_tool_profile(
    data: Dict[str, Any],
    slug: str,
    tool_name: str,
    company_name: str,
    current_date: Optional[str] = None,
) -> Dict[str, Any]:
    if current_date is None:
        current_date = datetime.now().strftime("%Y-%m-%d")
    data["slug"] = slug
    data["name"] = data.get("name") or tool_name
    data["company"] = data.get("company") or company_name
    data["lastUpdated"] = current_date
    for field in REQUIRED_PROFILE_FIELDS:
        if field not in data:
            data[field] = [] if field in ("keyFeatures", "tags") else ""
    if not isinstance(data["keyFeatures"], list):
        data["keyFeatures"] = []
    if not isinstance(data["tags"], list):
        data["tags"] = []
    for field in REQUIRED_PROFILE_FIELDS:
        data[field] = strip_citations(data[field])
    pricing = str(data.get("pricing", "")).lower().strip()
    data["pricing"] = pricing if pricing in VALID_PRICING else "unknown"
    return data
