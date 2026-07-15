import json
import tempfile
import unittest
from pathlib import Path

from applied_ai_rig.installer import (
    FileStatus,
    InstallationCancelled,
    build_plan,
    classify_file,
    install_plan,
    render_template,
)
from applied_ai_rig.manifest import Manifest
from applied_ai_rig.manifest import Profile


ROOT = Path(__file__).resolve().parents[1]


def core_profile() -> Profile:
    return Profile(1, "0.1.0", {}, (), (), {})


class RendererTests(unittest.TestCase):
    def test_renderer_replaces_documented_placeholders(self) -> None:
        rendered = render_template("Project: {{PROJECT_NAME}}\n", {"PROJECT_NAME": "Example"})

        self.assertEqual(rendered, "Project: Example\n")

    def test_renderer_rejects_unresolved_placeholder(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unresolved template placeholder"):
            render_template("{{MISSING}}", {})

    def test_renderer_normalizes_line_endings(self) -> None:
        rendered = render_template("one\r\ntwo\rthree", {})

        self.assertEqual(rendered, "one\ntwo\nthree")


class CoreTemplateTests(unittest.TestCase):
    def test_core_plan_contains_only_core_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = build_plan(Path(directory), core_profile(), ROOT / "templates")

        paths = {item.relative_path.as_posix() for item in plan.files}
        self.assertEqual(
            paths,
            {
                ".applied-ai-rig/profile.json",
                "APPLIED_AI_RIG_AGENT.md",
                "docs/applied-ai-rig/README.md",
                "docs/applied-ai-rig/OPERATING_PRINCIPLES.md",
                "docs/applied-ai-rig/DECISIONS.md",
                "docs/applied-ai-rig/DELIVERY_CHECKLIST.md",
                "docs/applied-ai-rig/EVIDENCE.md",
                "docs/applied-ai-rig/WORKLOG.md",
            },
        )

    def test_core_templates_use_stable_decision_and_evidence_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = build_plan(Path(directory), core_profile(), ROOT / "templates")

        content = "\n".join(item.content for item in plan.files)
        for field in ("Decision ID", "Status", "Supersedes", "Revision threshold", "Evidence ID"):
            self.assertIn(field, content)
        self.assertNotIn("OpenAI", content)
        self.assertNotIn("LangChain", content)

    def test_core_defines_the_full_work_cycle_and_handoff_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = build_plan(Path(directory), core_profile(), ROOT / "templates")

        content = "\n".join(item.content for item in plan.files).lower()
        for phrase in (
            "before implementation",
            "during implementation",
            "before delivery",
            "consequential decision",
            "failed attempts",
            "canonical source",
            "acceptance criteria",
            "residual risks",
        ):
            self.assertIn(phrase, content)


class ClassificationTests(unittest.TestCase):
    def test_missing_destination_is_new(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "README.md"

            self.assertEqual(classify_file(destination, b"new\n", None), FileStatus.NEW)

    def test_existing_untracked_destination_is_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "README.md"
            destination.write_text("existing\n", encoding="utf-8")

            self.assertEqual(classify_file(destination, b"new\n", None), FileStatus.CONFLICT)

    def test_existing_agent_file_becomes_manual_integration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "AGENTS.md").write_text("Existing instructions\n", encoding="utf-8")

            plan = build_plan(target, core_profile(), ROOT / "templates")

        self.assertIn("AGENTS.md", plan.manual_integrations)
        self.assertNotIn("AGENTS.md", {item.relative_path.as_posix() for item in plan.files})

    def test_profile_json_is_valid_and_contains_selected_modules(self) -> None:
        profile = Profile(1, "0.1.0", {}, ("data",), (), {})
        with tempfile.TemporaryDirectory() as directory:
            plan = build_plan(Path(directory), profile, ROOT / "templates")

        profile_file = next(
            item for item in plan.files if item.relative_path.as_posix() == ".applied-ai-rig/profile.json"
        )
        self.assertEqual(json.loads(profile_file.content)["selected_modules"], ["data"])


class AtomicInstallTests(unittest.TestCase):
    def test_existing_staging_directory_is_never_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            staging = target / ".applied-ai-rig/.staging"
            staging.mkdir(parents=True)
            marker = staging / "owned-by-project.txt"
            marker.write_text("keep", encoding="utf-8")
            plan = build_plan(target, core_profile(), ROOT / "templates")

            install_plan(plan, approve=lambda _: True, installed_at="2026-07-15T10:00:00Z")

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_fresh_install_writes_files_and_checksum_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plan = build_plan(target, core_profile(), ROOT / "templates")

            install_plan(plan, approve=lambda _: True, installed_at="2026-07-15T10:00:00Z")

            manifest = Manifest.from_json(
                (target / ".applied-ai-rig/manifest.json").read_text(encoding="utf-8")
            )
            self.assertTrue((target / "docs/applied-ai-rig/README.md").exists())
            self.assertEqual(len(manifest.files), len(plan.files))
            self.assertFalse((target / ".applied-ai-rig/.staging").exists())

    def test_failure_restores_existing_files_and_removes_new_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            existing = target / "docs/applied-ai-rig/README.md"
            existing.parent.mkdir(parents=True)
            existing.write_text("user content\n", encoding="utf-8")
            plan = build_plan(target, core_profile(), ROOT / "templates")

            with self.assertRaisesRegex(RuntimeError, "simulated write failure"):
                install_plan(
                    plan,
                    approve=lambda _: True,
                    installed_at="2026-07-15T10:00:00Z",
                    fail_after=2,
                )

            self.assertEqual(existing.read_text(encoding="utf-8"), "user content\n")
            self.assertFalse((target / "APPLIED_AI_RIG_AGENT.md").exists())
            self.assertFalse((target / ".applied-ai-rig/manifest.json").exists())

    def test_failure_never_removes_unrelated_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            unrelated = target / "user-empty-directory"
            unrelated.mkdir()
            plan = build_plan(target, core_profile(), ROOT / "templates")

            with self.assertRaises(RuntimeError):
                install_plan(
                    plan,
                    approve=lambda _: True,
                    installed_at="2026-07-15T10:00:00Z",
                    fail_after=1,
                )

            self.assertTrue(unrelated.is_dir())


class RerunTests(unittest.TestCase):
    def test_unchanged_rerun_has_only_unchanged_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first = build_plan(target, core_profile(), ROOT / "templates")
            install_plan(first, approve=lambda _: True, installed_at="2026-07-15T10:00:00Z")
            manifest = Manifest.from_json(
                (target / ".applied-ai-rig/manifest.json").read_text(encoding="utf-8")
            )
            checksums = {item.path: item.original_checksum for item in manifest.files}
            before = {
                path.relative_to(target): path.read_bytes()
                for path in target.rglob("*")
                if path.is_file()
            }

            second = build_plan(target, core_profile(), ROOT / "templates", checksums)
            install_plan(second, approve=lambda _: True, installed_at="2026-07-15T11:00:00Z")
            after = {
                path.relative_to(target): path.read_bytes()
                for path in target.rglob("*")
                if path.is_file()
            }

            self.assertTrue(all(item.status is FileStatus.UNCHANGED for item in second.files))
            self.assertEqual(after, before)

    def test_user_modified_generated_file_is_not_replaced_without_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first = build_plan(target, core_profile(), ROOT / "templates")
            install_plan(first, approve=lambda _: True, installed_at="2026-07-15T10:00:00Z")
            manifest = Manifest.from_json(
                (target / ".applied-ai-rig/manifest.json").read_text(encoding="utf-8")
            )
            checksums = {item.path: item.original_checksum for item in manifest.files}
            decision_file = target / "docs/applied-ai-rig/DECISIONS.md"
            decision_file.write_text("my decisions\n", encoding="utf-8")
            second = build_plan(target, core_profile(), ROOT / "templates", checksums)

            with self.assertRaises(InstallationCancelled):
                install_plan(second, approve=lambda _: False, installed_at="2026-07-15T11:00:00Z")

            self.assertEqual(decision_file.read_text(encoding="utf-8"), "my decisions\n")


if __name__ == "__main__":
    unittest.main()
