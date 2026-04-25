import json
import logging
import time

from dotenv import load_dotenv
from ai_info import get_tool_info, is_valid_tool
from utils import download_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()

def main():
    download_json()
    with open("slugs.json", "r") as f:
        tools = json.load(f)
        tool_count: int = len(tools)

        for idx, tool in enumerate(tools, 1):
            tool_name: str = tool.get("name")
            company_name: str = tool.get("company")
            slug: str = tool.get("slug")
            
            logging.info(f"Processing {idx}/{tool_count}: {tool_name}")
            
            # Skip invalid tool names (categories/placeholders)
            if not is_valid_tool(tool_name, company_name):
                logging.info(f"Skipping invalid tool name: {tool_name}")
                continue

            get_tool_info(company_name, tool_name, slug)
            time.sleep(5)

if __name__ == "__main__":
    main()

