import argparse
import json
import logging
import os
import time
from typing import Optional

from dotenv import load_dotenv
from ai_info import get_tool_info, is_valid_tool
from utils import download_json, download_previous_profiles, download_readme, parse_tool_urls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()


def _default_fallback(current_provider: str) -> Optional[str]:
    if current_provider == "gemini":
        return None
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return None


def parse_args():
    parser = argparse.ArgumentParser(description="Enrich AI tools data")
    parser.add_argument(
        "--provider",
        default=os.getenv("PROVIDER", "exa"),
        type=str.lower,
        choices=["exa", "gemini"],
        help="Primary provider (default: exa)",
    )
    env_fallback = os.getenv("FALLBACK_PROVIDER")
    parser.add_argument(
        "--fallback-provider",
        default=env_fallback if env_fallback in ("exa", "gemini") else None,
        type=str.lower,
        choices=["exa", "gemini"],
        help="Fallback provider if primary fails (default: gemini if GEMINI_API_KEY is set)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    fallback = args.fallback_provider or _default_fallback(args.provider)
    logging.info("Using provider: %s, fallback: %s", args.provider, fallback)

    download_json()
    tool_urls = parse_tool_urls(download_readme())
    previous_profiles = download_previous_profiles()
    with open("slugs.json", "r") as f:
        tools = json.load(f)
        tool_count: int = len(tools)
        logging.info(f"Total tools to process: {tool_count}")

        for idx, tool in enumerate(tools, 1):
            tool_name: str = tool.get("name")
            company_name: str = tool.get("company")
            slug: str = tool.get("slug")
            category: str = tool.get("category") or ""
            url: str = tool_urls.get((tool_name or "").strip().lower(), "")

            logging.info(f"Processing {idx}/{tool_count}: {tool_name}")

            # Skip invalid tool names (categories/placeholders)
            if not is_valid_tool(tool_name, company_name):
                logging.info(f"Skipping invalid tool name: {tool_name}")
                continue

            get_tool_info(
                company_name,
                tool_name,
                slug,
                provider_name=args.provider,
                fallback_provider_name=fallback,
                url=url,
                category=category,
                previous=previous_profiles.get(slug),
            )
            time.sleep(0.3)

        logging.info(f"{tool_count} tools processed successfully!")


if __name__ == "__main__":
    main()
