import json
import logging
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from providers import get_provider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()

enriched_data: list[dict] = []


def get_tool_info(
    company_name: str,
    tool_name: str,
    slug: str,
    provider_name: Optional[str] = None,
    fallback_provider_name: Optional[str] = None,
):
    """Fetch tool profile from the requested provider, falling back on failure."""
    primary_name = provider_name or "exa"
    logging.info("Getting info for %s using provider %s", slug, primary_name)
    primary = get_provider(primary_name)
    try:
        data = primary.get_tool_profile(company_name, tool_name, slug)
    except Exception as e:
        logging.warning("Primary provider %s failed for %s: %s", primary_name, slug, e)
        if not fallback_provider_name:
            raise
        fallback = get_provider(fallback_provider_name)
        logging.info("Falling back to %s for %s", fallback_provider_name, slug)
        data = fallback.get_tool_profile(company_name, tool_name, slug)
    prepare_enriched_data(data, slug)


def is_valid_tool(tool_name, company_name):
    """Check if tool name represents a valid tool (not a category/placeholder)."""
    invalid_names = {
        "open source", "opensource", "free", "paid", "freemium",
        "unknown", "n/a", "na", "", "none", "other"
    }
    return tool_name.lower().strip() not in invalid_names


def prepare_enriched_data(data: Dict[str, Any], slug: str):
    enriched_data.append(data)
    logging.info("Enriched %s items", len(enriched_data))
    with open("enriched_data.json", "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=2, ensure_ascii=False)
