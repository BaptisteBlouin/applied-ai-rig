import json
import re
import unittest
from pathlib import Path

import applied_ai_rig


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
PUBLIC_URL = re.compile(r"https://[^\s)\"']+")


class ProjectSurfaceTests(unittest.TestCase):
    def test_readme_local_links_resolve(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for raw in MARKDOWN_LINK.findall(readme):
            if "://" in raw or raw.startswith("mailto:") or raw.startswith("../../tree/"):
                continue
            path = raw.split("#", 1)[0]
            with self.subTest(link=raw):
                self.assertTrue((ROOT / path).exists())

        external = PUBLIC_URL.findall(readme)
        self.assertTrue(external)
        for raw in external:
            with self.subTest(public_link=raw):
                self.assertTrue(raw.startswith("https://"))
                self.assertNotIn("example.com", raw)

    def test_composite_action_runs_the_checker_from_its_own_checkout(self) -> None:
        action = (ROOT / "action.yml").read_text(encoding="utf-8")

        self.assertIn("using: composite", action)
        self.assertIn("$GITHUB_ACTION_PATH/init.py", action)
        self.assertIn("--check", action)
        self.assertIn("inputs.target", action)

    def test_json_schemas_document_the_existing_contracts(self) -> None:
        expected = {
            "profile.schema.json": {
                "schema_version",
                "rig_version",
                "answers",
                "selected_modules",
                "declined_modules",
                "recommendation_reasons",
            },
            "manifest.schema.json": {
                "schema_version",
                "rig_version",
                "installed_at",
                "selected_modules",
                "files",
                "manual_integrations",
            },
        }
        for filename, required in expected.items():
            with self.subTest(schema=filename):
                schema = json.loads((ROOT / "schemas" / filename).read_text(encoding="utf-8"))
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(set(schema["required"]), required)

        profile = json.loads((ROOT / "schemas/profile.schema.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "schemas/manifest.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(len(profile["allOf"]), 5)
        self.assertTrue(manifest["properties"]["files"]["uniqueItems"])
        self.assertIn("unique", manifest["properties"]["files"]["$comment"].lower())
        self.assertIn(
            "not",
            manifest["properties"]["manual_integrations"]["items"],
        )

    def test_private_launch_preparation_has_community_entry_points(self) -> None:
        paths = (
            "CHANGELOG.md",
            "CODE_OF_CONDUCT.md",
            "ROADMAP.md",
            "SUPPORT.md",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            ".github/ISSUE_TEMPLATE/module_proposal.yml",
        )

        for path in paths:
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())

    def test_release_uses_the_current_minor_version_without_changing_schema_version(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertEqual(applied_ai_rig.__version__, "0.2.0")
        self.assertIn("## [0.2.0] - 2026-07-16", changelog)
        self.assertIn("schema version remains 1", changelog.lower())


if __name__ == "__main__":
    unittest.main()
