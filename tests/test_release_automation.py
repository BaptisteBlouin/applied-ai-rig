import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FULL_SHA_ACTION = re.compile(r"uses:\s+[\w.-]+/[\w.-]+@([0-9a-f]{40})(?:\s+#\s+\S+)?$")


class ReleaseAutomationTests(unittest.TestCase):
    def test_ci_external_actions_are_immutable(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        self._assert_external_actions_are_immutable(workflow)

    def test_secret_scan_covers_history_with_immutable_actions(self) -> None:
        workflow = (ROOT / ".github/workflows/security.yml").read_text(encoding="utf-8")

        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn('GITLEAKS_VERSION: "8.30.1"', workflow)
        self.assertIn(
            'GITLEAKS_LINUX_X64_SHA256: "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"',
            workflow,
        )
        self.assertIn("sha256sum --check --strict", workflow)
        self.assertIn("gitleaks\" git . --log-opts=--all --redact --verbose", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("GITLEAKS_LICENSE", workflow)
        self._assert_external_actions_are_immutable(workflow)

    def test_release_requires_a_published_release_and_matching_version(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

        self.assertIn("release:\n    types: [published]", workflow)
        self.assertNotIn("workflow_dispatch", workflow)
        self.assertNotRegex(workflow, r"(?m)^\s+push:")
        self.assertIn("ref: ${{ github.event.release.tag_name }}", workflow)
        self.assertIn("RELEASE_TAG: ${{ github.event.release.tag_name }}", workflow)
        self.assertIn("Release tag must equal v<package-version>", workflow)
        self.assertIn("python -m build --no-isolation", workflow)
        self.assertIn("python tools/verify_package.py dist", workflow)
        self.assertIn("needs: build", workflow)
        self.assertIn("environment:\n      name: pypi", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("pypa/gh-action-pypi-publish@", workflow)
        self.assertNotIn("PYPI_TOKEN", workflow)
        self.assertNotIn("secrets.", workflow)
        self._assert_external_actions_are_immutable(workflow)

    def test_publish_job_only_downloads_and_publishes(self) -> None:
        workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        publish_job = workflow.split("\n  publish:\n", maxsplit=1)[1]

        self.assertEqual(publish_job.count("      - name:"), 2)
        self.assertIn("Download verified distributions", publish_job)
        self.assertIn("Publish distributions with Trusted Publishing", publish_job)
        self.assertNotIn("run:", publish_job)

    def test_dependabot_tracks_actions_and_pinned_python_tools(self) -> None:
        config = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
        requirements = (ROOT / "requirements/release.txt").read_text(encoding="utf-8")

        self.assertIn('package-ecosystem: "github-actions"', config)
        self.assertIn('package-ecosystem: "pip"', config)
        self.assertIn('- "/requirements"', config)
        self.assertGreaterEqual(config.count('interval: "weekly"'), 2)
        self.assertRegex(requirements, r"(?m)^build==\d+\.\d+\.\d+$")
        self.assertRegex(requirements, r"(?m)^twine==\d+\.\d+\.\d+$")
        self.assertRegex(requirements, r"(?m)^ruff==\d+\.\d+\.\d+$")
        self.assertRegex(requirements, r"(?m)^mypy==\d+\.\d+\.\d+$")
        self.assertRegex(requirements, r"(?m)^setuptools==\d+\.\d+\.\d+$")

    def test_release_runbook_covers_setup_and_non_destructive_rollback(self) -> None:
        runbook = (ROOT / "docs/releasing.md").read_text(encoding="utf-8")

        self.assertIn("BaptisteBlouin/applied-ai-rig", runbook)
        self.assertIn(".github/workflows/release.yml", runbook)
        self.assertIn("environment named `pypi`", runbook)
        self.assertIn("required reviewer", runbook.lower())
        self.assertIn("yank", runbook.lower())
        self.assertIn("never reuse", runbook.lower())
        self.assertIn("gitleaks git . --log-opts=--all --redact", runbook)

    def _assert_external_actions_are_immutable(self, workflow: str) -> None:
        action_lines = [
            line.strip()
            for line in workflow.splitlines()
            if "uses:" in line and not line.strip().startswith("uses: ./")
        ]
        self.assertTrue(action_lines)
        for line in action_lines:
            with self.subTest(action=line):
                self.assertRegex(line, FULL_SHA_ACTION)


if __name__ == "__main__":
    unittest.main()
