import json
import tempfile
import unittest
from pathlib import Path

from applied_ai_rig.checker import Severity, check_project
from applied_ai_rig.installer import build_plan, install_plan
from applied_ai_rig.manifest import Profile


ROOT = Path(__file__).resolve().parents[1]


def install_fixture(target: Path, *modules: str) -> None:
    profile = Profile(1, "0.1.0", {}, tuple(modules), (), {})
    plan = build_plan(target, profile, ROOT / "applied_ai_rig" / "templates")
    install_plan(plan, approve=lambda _: True, installed_at="2026-07-15T10:00:00Z")


class ManifestCheckTests(unittest.TestCase):
    def test_valid_generated_harness_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target, "model-api", "evaluation")

            result = check_project(target)

        self.assertEqual(result.errors, ())

    def test_missing_manifest_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = check_project(Path(directory))

        self.assertTrue(any("manifest.json is missing" in item.message for item in result.errors))

    def test_missing_generated_file_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            (target / "docs/applied-ai-rig/README.md").unlink()

            result = check_project(target)

        self.assertTrue(any("Generated file is missing" in item.message for item in result.errors))

    def test_manifest_cannot_hide_a_missing_selected_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            manifest_path = target / ".applied-ai-rig/manifest.json"
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            hidden = data["files"].pop(0)["path"]
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            result = check_project(target)

        self.assertTrue(any(item.path == hidden for item in result.errors))

    def test_missing_manual_integration_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            manifest_path = target / ".applied-ai-rig/manifest.json"
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            data["manual_integrations"] = ["APPLIED_AI_RIG_AGENT.project.md"]
            data["manual_integration_statuses"] = {
                "APPLIED_AI_RIG_AGENT.project.md": "proposed"
            }
            manifest_path.write_text(json.dumps(data), encoding="utf-8")

            result = check_project(target)

        self.assertTrue(
            any(
                item.path == "APPLIED_AI_RIG_AGENT.project.md"
                and "Manual integration path is missing" in item.message
                for item in result.errors
            )
        )

    def test_user_modified_generated_file_is_expected_local_customization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            (target / "docs/applied-ai-rig/DECISIONS.md").write_text(
                "# Decisions\n\n## DEC-001\n", encoding="utf-8"
            )

            result = check_project(target)

        self.assertFalse(any(item.path.endswith("DECISIONS.md") for item in result.errors))
        self.assertFalse(any(item.path.endswith("DECISIONS.md") for item in result.warnings))
        customized = [
            item for item in result.findings if item.path.endswith("DECISIONS.md")
        ]
        self.assertEqual([item.severity.value for item in customized], ["info"])
        self.assertIn("expected after authoring", customized[0].message)


class ContentCheckTests(unittest.TestCase):
    def test_unresolved_placeholder_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            path = target / "docs/applied-ai-rig/EVIDENCE.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n{{MISSING}}\n", encoding="utf-8")

            result = check_project(target)

        self.assertTrue(any("Unresolved template placeholder" in item.message for item in result.errors))

    def test_broken_internal_markdown_link_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            path = target / "docs/applied-ai-rig/README.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n[Missing](missing.md)\n", encoding="utf-8")

            result = check_project(target)

        self.assertTrue(any("Broken internal link" in item.message for item in result.errors))

    def test_incorrect_csv_header_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target, "evaluation")
            path = target / "docs/applied-ai-rig/modules/evaluation/experiments.csv"
            path.write_text("wrong,header\n", encoding="utf-8")

            result = check_project(target)

        self.assertTrue(any("CSV header" in item.message for item in result.errors))

    def test_new_module_register_schema_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target, "model-api")
            path = target / "docs/applied-ai-rig/modules/model-api/model_register.csv"
            path.write_text("owner,model\n", encoding="utf-8")

            result = check_project(target)

        self.assertTrue(any(item.path.endswith("model_register.csv") for item in result.errors))

    def test_new_core_record_heading_is_checked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            path = target / "docs/applied-ai-rig/WORKLOG.md"
            path.write_text("Material notes without the required heading.\n", encoding="utf-8")

            result = check_project(target)

        self.assertTrue(any(item.path.endswith("WORKLOG.md") for item in result.errors))

    def test_findings_never_claim_compliance_or_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = check_project(Path(directory))

        output = " ".join(item.message for item in result.findings).lower()
        for forbidden in ("compliant", "production-ready", "certified"):
            self.assertNotIn(forbidden, output)
        self.assertTrue(all(item.severity in (Severity.ERROR, Severity.WARNING) for item in result.findings))


if __name__ == "__main__":
    unittest.main()
