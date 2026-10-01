import unittest

from utils import normalize_tool_profile, strip_citations


class StripCitationsTest(unittest.TestCase):
    def test_removes_markers_before_punctuation(self):
        text = "Devin plans and tests complex tasks [5][2][4][6]. It returns PRs [5][2]."
        self.assertEqual(strip_citations(text), "Devin plans and tests complex tasks. It returns PRs.")

    def test_removes_list_and_range_markers(self):
        self.assertEqual(strip_citations("Pro is $20/month [1, 3] or more [2-4]"), "Pro is $20/month or more")

    def test_keeps_other_brackets(self):
        self.assertEqual(strip_citations("Supports [beta] mode"), "Supports [beta] mode")

    def test_cleans_lists(self):
        self.assertEqual(strip_citations(["Cloud sandbox [5][2]", "PR generation [4]"]), ["Cloud sandbox", "PR generation"])


class NormalizeToolProfileTest(unittest.TestCase):
    def test_strips_citations_from_all_text_fields(self):
        profile = normalize_tool_profile(
            {
                "pricing": "freemium",
                "pricingDetail": "Free tier [1][2].",
                "description": "Autonomous engineer [5][2].",
                "keyFeatures": ["Cloud sandbox [5]"],
                "bestFor": "Migrations [3].",
                "notIdealFor": "Prototyping [2][6].",
                "recentUpdates": "New model [9][10].",
                "verdict": "Powerful [4].",
                "tags": ["AI Agent"],
            },
            "devin",
            "Devin",
            "Cognition",
            "2026-10-01",
        )
        text = " ".join(str(profile[k]) for k in profile)
        self.assertNotRegex(text, r"\[\d+\]")
        self.assertEqual(profile["description"], "Autonomous engineer.")
        self.assertEqual(profile["keyFeatures"], ["Cloud sandbox"])


if __name__ == "__main__":
    unittest.main()
