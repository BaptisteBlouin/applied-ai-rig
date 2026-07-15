import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from applied_ai_rig.cli import InteractiveApprover
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

    def test_skip_all_rejects_following_conflicts_without_prompting(self) -> None:
        input_fn = Mock(return_value="s")
        output_fn = Mock()
        approver = InteractiveApprover(Path("/tmp/project"), input_fn, output_fn)
        item = PlannedFile(Path("one.md"), "new\n", FileStatus.CONFLICT)

        self.assertFalse(approver(item))
        self.assertFalse(approver(item))
        self.assertEqual(input_fn.call_count, 1)


if __name__ == "__main__":
    unittest.main()
