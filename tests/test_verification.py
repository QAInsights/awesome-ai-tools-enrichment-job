import json
import os
import tempfile
import unittest
from unittest import mock

import ai_info
from utils import build_prompt, is_official_source, retrieved_only, strip_provenance, verify_profile


def profile(**overrides):
    data = {
        "slug": "nenva",
        "description": "Privacy-first personal AI assistant for macOS.",
        "identityMatch": True,
        "sources": ["https://nenva.co/", "https://github.com/Anjadhe/Anjadhe"],
    }
    data.update(overrides)
    return data


class OfficialSourceTest(unittest.TestCase):
    def test_matches_the_site_its_subdomains_and_bare_domains(self):
        self.assertTrue(is_official_source("https://www.nenva.co/pricing", "https://nenva.co"))
        self.assertTrue(is_official_source("https://docs.devin.ai/release-notes", "https://devin.ai"))
        self.assertTrue(is_official_source("devin.ai", "https://app.devin.ai"))

    def test_rejects_a_same_named_domain(self):
        self.assertFalse(is_official_source("https://nenva.com", "https://nenva.co"))
        self.assertFalse(is_official_source("https://notnenva.co", "https://nenva.co"))

    def test_code_hosts_must_share_the_account(self):
        official = "https://github.com/Anjadhe/Anjadhe"
        self.assertTrue(is_official_source("https://github.com/anjadhe/Anjadhe/releases", official))
        self.assertFalse(is_official_source("https://github.com/someone/nenva", official))


class VerifyProfileTest(unittest.TestCase):
    def test_accepts_a_grounded_profile(self):
        self.assertIsNone(verify_profile(profile(), "https://nenva.co"))

    def test_rejects_unconfirmed_identity(self):
        self.assertIn("confirm", verify_profile(profile(identityMatch=False), "https://nenva.co"))
        self.assertIn("confirm", verify_profile(profile(identityMatch="true"), "https://nenva.co"))

    def test_rejects_missing_or_unofficial_sources(self):
        self.assertIn("no sources", verify_profile(profile(sources=[]), "https://nenva.co"))
        self.assertIn("official site", verify_profile(profile(sources=["https://nenva.com"]), "https://nenva.co"))

    def test_without_an_official_url_any_source_is_enough(self):
        self.assertIsNone(verify_profile(profile(sources=["https://example.com"])))

    def test_sources_the_search_never_returned_are_dropped(self):
        claimed = ["https://nenva.co/", "https://github.com/Anjadhe/Anjadhe", "nenva.co"]
        self.assertEqual(retrieved_only(claimed, ["https://www.nenva.co/download"]), ["https://nenva.co/", "nenva.co"])
        self.assertEqual(retrieved_only("https://nenva.co", ["nenva.co"]), [])

    def test_strip_provenance_keeps_the_published_schema(self):
        self.assertEqual(set(strip_provenance(profile())), {"slug", "description"})

    def test_prompt_forbids_guessing(self):
        prompt = build_prompt("Anjadhe", "nenva", "nenva", "https://nenva.co")
        self.assertIn("An empty field is always better than a plausible guess", prompt)
        self.assertIn('"identityMatch": true', prompt)


class FakeProvider:
    def __init__(self, result):
        self.result = result

    def get_tool_profile(self, *args):
        if isinstance(self.result, Exception):
            raise self.result
        return dict(self.result)


class GetToolInfoTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        ai_info.enriched_data.clear()

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()
        ai_info.enriched_data.clear()

    def run_with(self, providers, previous=None):
        with mock.patch.object(ai_info, "get_provider", side_effect=lambda name: FakeProvider(providers[name])):
            ai_info.get_tool_info(
                "Anjadhe", "nenva", "nenva", "exa", "gemini", url="https://nenva.co", previous=previous
            )
        if not os.path.exists("enriched_data.json"):
            return []
        with open("enriched_data.json", encoding="utf-8") as f:
            return json.load(f)

    def test_stores_a_verified_profile_without_provenance_fields(self):
        stored = self.run_with({"exa": profile(), "gemini": RuntimeError("unused")})
        self.assertEqual(stored, [strip_provenance(profile())])

    def test_falls_back_when_the_primary_profile_is_rejected(self):
        gemini = profile(description="From Gemini.")
        stored = self.run_with({"exa": profile(sources=["https://nenva.com"]), "gemini": gemini})
        self.assertEqual(stored[0]["description"], "From Gemini.")

    def test_keeps_the_published_profile_when_every_provider_fails_verification(self):
        previous = {"slug": "nenva", "description": "Published."}
        stored = self.run_with(
            {"exa": profile(identityMatch=False), "gemini": RuntimeError("down")}, previous=previous
        )
        self.assertEqual(stored, [previous])

    def test_leaves_out_a_new_tool_with_no_trustworthy_profile(self):
        self.assertEqual(self.run_with({"exa": profile(sources=[]), "gemini": profile(sources=[])}), [])


if __name__ == "__main__":
    unittest.main()
