import json
import logging
import os
import time

from constants import GEMINI_MODEL
from dotenv import load_dotenv
from google import genai
from google.genai import types

from utils import build_prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()
client = genai.Client()

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool],
    http_options=types.HttpOptions(timeout=120000)  # 2 minute timeout
)

enriched_data = []

def get_tool_info(company_name, tool_name, slug):
    prompt = build_prompt(company_name, tool_name, slug)
    logging.info(prompt)

    max_retries = 3
    response = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=config,
            )
            break
        except Exception as e:
            logging.warning("Attempt %s/%s failed for %s: %s", attempt, max_retries, slug, e)
            if attempt == max_retries:
                logging.error("Max retries exceeded for %s", slug)
                raise
            time.sleep(2 ** attempt)

    logging.info(response.text)

    prepare_enriched_data(response.text, slug)

def is_valid_tool(tool_name, company_name):
    """Check if tool name represents a valid tool (not a category/placeholder)."""
    invalid_names = {
        "open source", "opensource", "free", "paid", "freemium",
        "unknown", "n/a", "na", "", "none", "other"
    }
    return tool_name.lower().strip() not in invalid_names

def prepare_enriched_data(response_text, slug):
    data = json.loads(response_text)
    enriched_data.append(data)
    logging.info("Enriched %s items", len(enriched_data))

    with open("enriched_data.json", "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=2, ensure_ascii=False)

