from datetime import datetime

def download_json():
    # TODO: Download the JSON file from the URL
    url = "https://raw.githubusercontent.com/QAInsights/awesome-ai-tools/refs/heads/main/src/data/tools.json"
    
    import requests
    response = requests.get(url)
    with open("tools.json", "w") as f:
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