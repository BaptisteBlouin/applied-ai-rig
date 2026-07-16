import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from applied_ai_rig.cli import InteractiveApprover, WebApprover, run_setup_wizard
from applied_ai_rig.installer import FileStatus, PlannedFile


ROOT = Path(__file__).resolve().parents[1]


class CliSmokeTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "init.py"), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_help_describes_installation_and_check_modes(self) -> None:
        result = self.run_cli("--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Applied AI Rig", result.stdout)
        self.assertIn("--dry-run", result.stdout)
        self.assertIn("--check", result.stdout)
        self.assertIn("--list-modules", result.stdout)
        self.assertIn("--explain", result.stdout)
        self.assertIn("--profile", result.stdout)
        self.assertIn("--terminal", result.stdout)
        self.assertIn("--no-browser", result.stdout)

    def test_list_modules_explains_triggers_and_generated_artifacts(self) -> None:
        result = self.run_cli("--list-modules")

        self.assertEqual(result.returncode, 0)
        for module_id in ("model-api", "data", "evaluation", "agentic-runtime", "operations"):
            self.assertIn(module_id, result.stdout)
        self.assertIn("Generated", result.stdout)

    def test_explain_prints_detailed_module_guidance(self) -> None:
        result = self.run_cli("--explain", "evaluation")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Evaluation", result.stdout)
        self.assertIn("Recommended when", result.stdout)
        self.assertIn("EVALUATION_PLAN.md", result.stdout)

    def test_named_profile_can_drive_a_non_interactive_preview(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(
                directory,
                "--profile",
                "api-rag",
                "--non-interactive",
                "--dry-run",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("modules/model-api/README.md", result.stdout)
        self.assertIn("modules/data/README.md", result.stdout)
        self.assertIn("modules/evaluation/README.md", result.stdout)

    def test_unknown_argument_returns_usage_error(self) -> None:
        result = self.run_cli("--does-not-exist")

        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_non_interactive_requires_explicit_modules_on_new_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(directory, "--non-interactive", "--dry-run")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--modules", result.stderr)

    def test_core_only_dry_run_lists_plan_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            result = self.run_cli(
                str(target),
                "--modules",
                "none",
                "--non-interactive",
                "--dry-run",
            )

            self.assertEqual(list(target.iterdir()), [])

        self.assertEqual(result.returncode, 0)
        self.assertIn("NEW", result.stdout)
        self.assertIn("docs/applied-ai-rig/README.md", result.stdout)

    def test_non_interactive_install_and_check_work_in_path_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project with spaces"
            install = self.run_cli(
                str(target), "--modules", "none", "--non-interactive"
            )
            check = self.run_cli(str(target), "--check")

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn("Structural check completed", check.stdout)
        self.assertIn("Next:", install.stdout)
        self.assertIn("status", install.stdout)

    def test_status_command_reports_health_records_and_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = self.run_cli(
                directory, "--modules", "evaluation", "--non-interactive"
            )
            status = self.run_cli("status", directory)

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn("Structural health: healthy", status.stdout)
        self.assertIn("decisions: 0", status.stdout)
        self.assertIn("experiments: 0", status.stdout)
        self.assertIn("add decision", status.stdout)

    def test_status_reports_a_broken_core_instead_of_aborting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = self.run_cli(directory, "--modules", "none", "--non-interactive")
            (Path(directory) / "docs/applied-ai-rig/DECISIONS.md").unlink()

            status = self.run_cli("status", directory)

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(status.returncode, 1, status.stderr)
        self.assertIn("Structural health: needs attention", status.stdout)
        self.assertIn("Generated file is missing", status.stdout)

    def test_status_on_a_missing_installation_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("status", directory)

        self.assertEqual(result.returncode, 2)
        self.assertIn("not installed", result.stderr)

    def test_status_reports_partial_metadata_as_structurally_broken(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            metadata = Path(directory) / ".applied-ai-rig"
            metadata.mkdir()
            (metadata / "profile.json").write_text("{}\n", encoding="utf-8")

            result = self.run_cli("status", directory)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("manifest.json is missing", result.stdout)
        self.assertIn("Modules: unknown", result.stdout)
        self.assertIn("decisions: unknown", result.stdout)

    def test_legacy_targets_named_status_or_add_still_install(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for target_name in ("status", "add"):
                with self.subTest(target=target_name):
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / "init.py"),
                            target_name,
                            "--modules",
                            "none",
                            "--non-interactive",
                        ],
                        cwd=directory,
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    installed = (
                        Path(directory) / target_name / ".applied-ai-rig/manifest.json"
                    ).is_file()

                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(installed)

    def test_status_without_target_uses_the_current_installed_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = self.run_cli(directory, "--modules", "none", "--non-interactive")
            status = subprocess.run(
                [sys.executable, str(ROOT / "init.py"), "status"],
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn("Applied AI Rig status", status.stdout)

    def test_status_without_target_never_falls_back_to_installation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            status = subprocess.run(
                [sys.executable, str(ROOT / "init.py"), "status"],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )

            entries = list(target.iterdir())

        self.assertEqual(status.returncode, 2)
        self.assertIn("not installed", status.stderr)
        self.assertNotIn("Traceback", status.stderr)
        self.assertEqual(entries, [])

    def test_status_recovers_modules_and_counts_when_manifest_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = self.run_cli(
                directory, "--modules", "evaluation", "--non-interactive"
            )
            decision = self.run_cli(
                "add",
                "decision",
                directory,
                "--id",
                "DEC-001",
                "--title",
                "Choose a model",
                "--yes",
            )
            experiment = self.run_cli(
                "add",
                "experiment",
                directory,
                "--run-id",
                "RUN-001",
                "--decision",
                "DEC-001",
                "--model",
                "model-a",
                "--metric",
                "accuracy",
                "--value",
                "0.91",
                "--yes",
            )
            (Path(directory) / ".applied-ai-rig/manifest.json").unlink()

            status = self.run_cli("status", directory)

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(decision.returncode, 0, decision.stderr)
        self.assertEqual(experiment.returncode, 0, experiment.stderr)
        self.assertEqual(status.returncode, 1, status.stderr)
        self.assertIn("Modules: evaluation", status.stdout)
        self.assertIn("decisions: 1", status.stdout)
        self.assertIn("experiments: 1", status.stdout)

    def test_add_decision_previews_by_default_and_writes_with_yes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = self.run_cli(directory, "--modules", "none", "--non-interactive")
            path = Path(directory) / "docs/applied-ai-rig/DECISIONS.md"
            before = path.read_text(encoding="utf-8")

            preview = self.run_cli(
                "add",
                "decision",
                directory,
                "--id",
                "DEC-20260716-model-choice",
                "--title",
                "Choose the initial model",
            )
            after_preview = path.read_text(encoding="utf-8")
            write = self.run_cli(
                "add",
                "decision",
                directory,
                "--id",
                "DEC-20260716-model-choice",
                "--title",
                "Choose the initial model",
                "--yes",
            )
            duplicate = self.run_cli(
                "add",
                "decision",
                directory,
                "--id",
                "DEC-20260716-model-choice",
                "--title",
                "Choose another model",
                "--yes",
            )
            final = path.read_text(encoding="utf-8")

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(after_preview, before)
        self.assertIn("Preview", preview.stdout)
        self.assertIn("--yes", preview.stdout)
        self.assertEqual(write.returncode, 0, write.stderr)
        self.assertIn("Added DEC-20260716-model-choice", write.stdout)
        self.assertIn("DEC-20260716-model-choice", final)
        self.assertEqual(duplicate.returncode, 2)
        self.assertIn("already exists", duplicate.stderr)

    def test_add_decision_cannot_create_an_accepted_empty_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = self.run_cli(directory, "--modules", "none", "--non-interactive")
            result = self.run_cli(
                "add",
                "decision",
                directory,
                "--id",
                "DEC-001",
                "--title",
                "Choose a model",
                "--status",
                "accepted",
                "--yes",
            )

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_add_evidence_and_experiment_write_the_reviewed_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = self.run_cli(directory, "--modules", "evaluation", "--non-interactive")
            decision = self.run_cli(
                "add", "decision", directory, "--id", "DEC-001", "--title", "Choose a model", "--yes"
            )
            evidence = self.run_cli(
                "add",
                "evidence",
                directory,
                "--id",
                "EVD-001",
                "--claim",
                "Candidate passed",
                "--decision",
                "DEC-001",
                "--status",
                "measured",
                "--yes",
            )
            experiment = self.run_cli(
                "add",
                "experiment",
                directory,
                "--run-id",
                "RUN-001",
                "--decision",
                "DEC-001",
                "--model",
                "model-a",
                "--metric",
                "accuracy",
                "--value",
                "0.91",
                "--yes",
            )
            evidence_content = (Path(directory) / "docs/applied-ai-rig/EVIDENCE.md").read_text(encoding="utf-8")
            experiment_content = (
                Path(directory) / "docs/applied-ai-rig/modules/evaluation/experiments.csv"
            ).read_text(encoding="utf-8")

        for result in (install, decision, evidence, experiment):
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("EVD-001", evidence_content)
        self.assertIn("RUN-001", experiment_content)

    def test_add_experiment_explains_when_module_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = self.run_cli(directory, "--modules", "none", "--non-interactive")
            result = self.run_cli(
                "add",
                "experiment",
                directory,
                "--run-id",
                "RUN-001",
                "--decision",
                "DEC-001",
                "--model",
                "model-a",
                "--metric",
                "accuracy",
                "--value",
                "0.91",
                "--yes",
            )

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(result.returncode, 2)
        self.assertIn("evaluation module", result.stderr)

    def test_non_interactive_install_works_with_non_ascii_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "projet-évaluation"

            result = self.run_cli(
                str(target), "--modules", "evaluation", "--non-interactive"
            )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_non_interactive_conflict_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first = self.run_cli(
                str(target), "--modules", "none", "--non-interactive"
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            decisions = target / "docs/applied-ai-rig/DECISIONS.md"
            decisions.write_text("user-owned content\n", encoding="utf-8")
            before = {path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()}

            second = self.run_cli(
                str(target), "--modules", "none", "--non-interactive"
            )
            after = {path.relative_to(target): path.read_bytes() for path in target.rglob("*") if path.is_file()}

        self.assertEqual(second.returncode, 3)
        self.assertEqual(after, before)


class InteractiveApprovalTests(unittest.TestCase):
    def test_apply_to_all_approves_following_conflicts_without_prompting(self) -> None:
        input_fn = Mock(return_value="a")
        output_fn = Mock()
        approver = InteractiveApprover(Path("/tmp/project"), input_fn, output_fn)
        first = PlannedFile(Path("one.md"), "new\n", FileStatus.CONFLICT)
        second = PlannedFile(Path("two.md"), "new\n", FileStatus.CONFLICT)

        self.assertTrue(approver(first))
        self.assertTrue(approver(second))
        self.assertEqual(input_fn.call_count, 1)

    def test_web_approver_accepts_only_paths_confirmed_in_the_browser(self) -> None:
        approver = WebApprover(frozenset({"approved.md"}))

        self.assertTrue(
            approver(PlannedFile(Path("approved.md"), "new\n", FileStatus.CONFLICT))
        )
        self.assertFalse(
            approver(PlannedFile(Path("other.md"), "new\n", FileStatus.CONFLICT))
        )

    def test_skip_all_rejects_following_conflicts_without_prompting(self) -> None:
        input_fn = Mock(return_value="s")
        output_fn = Mock()
        approver = InteractiveApprover(Path("/tmp/project"), input_fn, output_fn)
        item = PlannedFile(Path("one.md"), "new\n", FileStatus.CONFLICT)

        self.assertFalse(approver(item))
        self.assertFalse(approver(item))
        self.assertEqual(input_fn.call_count, 1)


class SetupWizardTests(unittest.TestCase):
    def test_question_help_and_back_are_supported_without_losing_answers(self) -> None:
        replies = iter(["5", "?", "y", "b", "n", "n", "n", "n", "n", "n", ""])
        output: list[str] = []

        profile = run_setup_wizard(
            input_fn=lambda _: next(replies),
            output_fn=output.append,
        )

        self.assertFalse(profile.answers["external_model_api"])
        self.assertTrue(any("Why this matters" in line for line in output))

    def test_recommended_modules_can_be_toggled_before_confirmation(self) -> None:
        replies = iter(["2", "4", ""])

        profile = run_setup_wizard(input_fn=lambda _: next(replies), output_fn=lambda _: None)

        self.assertEqual(
            profile.selected_modules,
            ("model-api", "data", "evaluation", "agentic-runtime"),
        )

    def test_quick_profile_does_not_invent_risk_answers(self) -> None:
        replies = iter(["4", ""])

        profile = run_setup_wizard(input_fn=lambda _: next(replies), output_fn=lambda _: None)

        self.assertEqual(dict(profile.answers), {})
        self.assertEqual(
            profile.selected_modules,
            ("model-api", "data", "evaluation", "operations"),
        )

if __name__ == "__main__":
    unittest.main()
