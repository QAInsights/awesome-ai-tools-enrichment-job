import json
import logging
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from providers import get_provider
from utils import strip_provenance, verify_profile

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
    url: str = "",
    category: str = "",
    previous: Optional[Dict[str, Any]] = None,
):
    """Store the first profile that passes verification; otherwise keep the published one."""
    names = [provider_name or "exa"]
    if fallback_provider_name and fallback_provider_name not in names:
        names.append(fallback_provider_name)
    for name in names:
        logging.info("Getting info for %s using provider %s", slug, name)
        try:
            data = get_provider(name).get_tool_profile(company_name, tool_name, slug, url, category)
        except Exception as e:
            logging.warning("Provider %s failed for %s: %s", name, slug, e)
            continue
        problem = verify_profile(data, url)
        if problem is None:
            prepare_enriched_data(strip_provenance(data), slug)
            return
        logging.warning("Rejected %s profile for %s: %s (sources: %s)", name, slug, problem, data.get("sources"))
    if previous:
        logging.warning("Keeping the published profile for %s", slug)
        prepare_enriched_data(previous, slug)
    else:
        logging.error("No trustworthy profile for %s; leaving it out", slug)


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
