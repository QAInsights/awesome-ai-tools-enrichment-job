import json
import logging
import os
import time

from dotenv import load_dotenv
from ai_info import get_tool_info
from utils import download_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()

def main():
    if os.path.exists("enriched_data.json"):
        os.remove("enriched_data.json")
        logging.info("Removed stale enriched_data.json")

    download_json()
    with open("tools.json", "r") as f:
        tools = json.load(f)
        tool_count: int = len(tools)

        for tool in tools:
            tool_name: str = tool.get("companyName")
            company_name: str = tool.get("companyName")
            slug: str = tool_name.lower().replace(" ", "-")
            
            logging.info(f"Tool count: {tool_count}")
            
            logging.info(f"Tool name: {tool_name}")
            logging.info(f"Company name: {company_name}")
            logging.info(f"Slug: {slug}")

            get_tool_info(company_name, tool_name, slug)
            time.sleep(5)

if __name__ == "__main__":
    main()

