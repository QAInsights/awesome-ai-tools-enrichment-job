import json
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

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


def download_previous_profiles() -> Dict[str, Dict[str, Any]]:
    """Profiles currently published by the directory, keyed by slug, kept when a fresh one is rejected."""
    url = "https://raw.githubusercontent.com/QAInsights/awesome-ai-tools/refs/heads/main/public/data/enriched-tools.json"
    import requests

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return {p["slug"]: p for p in response.json() if isinstance(p, dict) and p.get("slug")}


def download_readme() -> str:
    url = "https://raw.githubusercontent.com/QAInsights/awesome-ai-tools/refs/heads/main/README.md"
    import requests

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


README_TOOL_LINK = re.compile(r"^\|\s*\*\*\[(.+?)\]\((https?://[^)\s]+)\)\*\*\s*\|", re.MULTILINE)


def parse_tool_urls(readme: str) -> Dict[str, str]:
    """Map lower-cased catalog tool names to the official URL linked in the README table."""
    urls: Dict[str, str] = {}
    for name, url in README_TOOL_LINK.findall(readme):
        urls.setdefault(name.strip().lower(), url)
    return urls


IDENTITY_RULE = (
    "Search results may include unrelated products, projects or domains that share this tool's name. "
    "Describe only the tool made by the named company"
)


def identity_rule(url: str = "") -> str:
    site = f" whose official site is {url}" if url else ""
    return (
        f"{IDENTITY_RULE}{site}. Ignore any result about a different product, and never describe "
        "a same-named website, domain registration or unrelated project."
    )


GROUNDING_RULES = """Accuracy rules:
- State only facts that a source you were given says explicitly. Never fill gaps from memory or general knowledge, and never guess plan names, prices, limits, numbers, dates, integrations or platforms.
- Prefer the official site, its docs, pricing page, changelog and GitHub repository. If sources disagree, trust the most recent official source.
- If no source states a value, return an empty string (or empty array). An empty field is always better than a plausible guess.
- recentUpdates must describe dated releases or announcements from the sources, newest first. If none are dated, return an empty string.
- bestFor, notIdealFor and verdict must follow from the facts you reported, not from assumptions about similar tools.
- Set identityMatch to true only if the sources clearly describe this exact tool from this company. If they describe a different product, a parked or same-named domain, or nothing relevant, set identityMatch to false.
- List in sources every URL you took a fact from."""


def grounding_rules(url: str = "") -> str:
    return f"{identity_rule(url)}\n\n{GROUNDING_RULES}"


PROVENANCE_FIELDS = ("identityMatch", "sources")
CODE_HOSTS = {"github.com", "gitlab.com", "bitbucket.org", "huggingface.co", "codeberg.org"}


def _host_and_owner(url: str) -> tuple:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    owner = parsed.path.strip("/").split("/")[0].lower()
    return host, owner


def is_official_source(source: str, official_url: str) -> bool:
    """True when source lives on the official site (or its subdomains), or in the same code-host account."""
    source_host, source_owner = _host_and_owner(source)
    official_host, official_owner = _host_and_owner(official_url)
    if not source_host or not official_host:
        return False
    if official_host in CODE_HOSTS:
        return source_host == official_host and bool(official_owner) and source_owner == official_owner
    return (
        source_host == official_host
        or source_host.endswith(f".{official_host}")
        or official_host.endswith(f".{source_host}")
    )


def collect_sources(*groups: Iterable[Any]) -> List[str]:
    seen: List[str] = []
    for group in groups:
        for item in group or []:
            if isinstance(item, str) and item.strip() and item.strip() not in seen:
                seen.append(item.strip())
    return seen


def retrieved_only(claimed: Any, retrieved: Iterable[str]) -> List[str]:
    """Drop model-reported sources whose site never appeared in the search results."""
    hosts = {_host_and_owner(r)[0] for r in retrieved if isinstance(r, str)}
    hosts.discard("")
    return [s for s in collect_sources(claimed if isinstance(claimed, list) else []) if _host_and_owner(s)[0] in hosts]


def verify_profile(data: Dict[str, Any], url: str = "") -> Optional[str]:
    """Return why a generated profile cannot be trusted, or None when it passes."""
    if data.get("identityMatch") is not True:
        return "the model could not confirm the sources describe this tool"
    sources = data.get("sources") if isinstance(data.get("sources"), list) else []
    if not sources:
        return "no sources were reported"
    if url and not any(is_official_source(s, url) for s in sources):
        return f"no source is on the official site {url}"
    if not data.get("description"):
        return "the description is empty"
    return None


def strip_provenance(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if k not in PROVENANCE_FIELDS}


def build_exa_query(company_name: str, tool_name: str, slug: str, url: str = "", category: str = "") -> str:
    subject = f"{tool_name} by {company_name}"
    if category:
        subject += f", listed as {category}"
    if url:
        subject += f", official site {url}"
    return (
        f"Find the latest information about {subject} (also known as {slug}). "
        f"What is its pricing model, key features, best use cases, not ideal use cases, "
        f"recent updates, and a short verdict?"
    )


def build_prompt(company_name: str, tool_name: str, slug: str, url: str = "", category: str = "") -> str:
    current_date = datetime.now().strftime("%Y-%m-%d")
    return f"""
        You are writing a tool profile for ai.dosa.dev,
        a curated directory of AI coding tools for developers.

        Tool name: {tool_name}
        Company: {company_name}
        Official site: {url or "unknown"}
        Category: {category or "unknown"}

        Today is {current_date}.

        Use Google Search to find the latest information about this tool: pricing, features, recent updates.
        Start from the official site and the tool's GitHub repository if it has one.

        {grounding_rules(url)}

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
            "lastUpdated": "{current_date}",
            "identityMatch": true,
            "sources": ["https://..."]
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
