from google import genai
from dotenv import load_dotenv
import json
from constants import GEMINI_MODEL, prompt
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()

client = genai.Client()

def main():
    # read json file
    with open("tools.json", "r") as f:
        tools = json.load(f)
        tool_count = len(tools)

        for tool in tools:
            tool_name = tool.get("companyName")
            company_name = tool.get("companyName")
            logging.info(f"Tool name: {tool_name}")
            logging.info(f"Company name: {company_name}")

            # get_tool_info(company_name, tool_name)

if __name__ == "__main__":
    main()

