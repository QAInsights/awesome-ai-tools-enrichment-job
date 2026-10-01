import unittest

from utils import build_exa_query, build_prompt, identity_rule, parse_tool_urls

README = """
| Tool | Company | Notes |
|------|---------|-------|
| **[nenva](https://nenva.co)** | Anjadhe | Personal AI for macOS; [GitHub](https://github.com/Anjadhe/Anjadhe) |
| **[Devin](https://devin.ai)** | Cognition | Autonomous AI software engineer |
| **Corust** | Corust | Site unreachable; link removed |
"""


class ParseToolUrlsTest(unittest.TestCase):
    def test_maps_lower_cased_names_to_the_tool_link_only(self):
        self.assertEqual(parse_tool_urls(README), {"nenva": "https://nenva.co", "devin": "https://devin.ai"})

    def test_keeps_the_first_link_for_a_repeated_name(self):
        readme = README + "| **[Devin](https://example.com)** | Other | Duplicate |\n"
        self.assertEqual(parse_tool_urls(readme)["devin"], "https://devin.ai")


class IdentityGroundingTest(unittest.TestCase):
    def test_exa_query_names_the_official_site_and_category(self):
        query = build_exa_query("Anjadhe", "nenva", "nenva", "https://nenva.co", "General-Purpose AI Assistants")
        self.assertIn("nenva by Anjadhe, listed as General-Purpose AI Assistants, official site https://nenva.co", query)

    def test_exa_query_without_url_or_category(self):
        query = build_exa_query("Cognition", "Devin", "devin")
        self.assertTrue(query.startswith("Find the latest information about Devin by Cognition (also known as devin)."))

    def test_identity_rule_pins_the_official_site(self):
        self.assertIn("whose official site is https://nenva.co", identity_rule("https://nenva.co"))
        self.assertNotIn("official site", identity_rule(""))

    def test_gemini_prompt_carries_site_category_and_rule(self):
        prompt = build_prompt("Anjadhe", "nenva", "nenva", "https://nenva.co", "General-Purpose AI Assistants")
        self.assertIn("Official site: https://nenva.co", prompt)
        self.assertIn("Category: General-Purpose AI Assistants", prompt)
        self.assertIn("never describe a same-named website", prompt)


if __name__ == "__main__":
    unittest.main()
