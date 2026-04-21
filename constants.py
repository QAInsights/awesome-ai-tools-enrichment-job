GEMINI_MODEL = "gemini-3-flash-preview"

prompt = """
You are writing a tool profile for ai.dosa.dev,
a curated directory of AI coding tools for developers.

Tool name: %s
Company: %s

Use Google Search to find the latest information about this tool: pricing, features, recent updates.

You can also check the GitHub repository for the tool to find the latest information about the tool.

DO NOT hallucinate pricing, features, recent updates.

Return ONLY valid JSON, no markdown, no backticks:
{
    "slug": "%s",
    "name": "%s",
    "company": "%s",
    "pricing": "free|freemium|paid|open-source",
    "pricingDetail": "string",
    "description": "2-3 sentence plain English description",
    "keyFeatures": ["string", "string", "string"],
    "bestFor": "string",
    "notIdealFor": "string",
    "recentUpdates": "string",
    "verdict": "string",
    "tags": ["string"],
    "lastUpdated": "%s"
}
""" 
