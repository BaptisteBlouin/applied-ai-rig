import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PilotProgramTests(unittest.TestCase):
    def test_playbook_defines_private_pilot_evidence_without_telemetry(self) -> None:
        playbook = (ROOT / "docs" / "pilot-playbook.md").read_text(encoding="utf-8")
        normalized = " ".join(playbook.lower().split())

        required_phrases = (
            "five genuine external pilots",
            "No telemetry",
            "Rehearsals are not external evidence",
            "Installation elapsed time",
            "First-real-record elapsed time",
            "Later pull-request update",
            "median installation time is under five minutes",
            "at least three of five pilots",
            "Go",
            "Hold",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), normalized)

    def test_playbook_protects_pilot_data_and_keeps_failures_in_results(self) -> None:
        playbook = (ROOT / "docs" / "pilot-playbook.md").read_text(encoding="utf-8")
        normalized = " ".join(playbook.lower().split())

        for phrase in (
            "participation is voluntary",
            "withdraw",
            "Do not collect",
            "secrets",
            "private project content",
            "Do not discard failed or abandoned attempts",
            "aggregate",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), normalized)

    def test_pilot_feedback_issue_form_collects_structured_safe_feedback(self) -> None:
        form = (
            ROOT / ".github" / "ISSUE_TEMPLATE" / "pilot_feedback.yml"
        ).read_text(encoding="utf-8")

        for field_id in (
            "pilot_kind",
            "install_seconds",
            "record_seconds",
            "later_update",
            "followup_elapsed_days",
            "friction",
            "unused",
            "privacy",
        ):
            with self.subTest(field_id=field_id):
                self.assertIn(f"id: {field_id}", form)
        self.assertIn("Do not include secrets", form)
        self.assertIn("rehearsal", form.lower())
        self.assertIn("14 days or later", form)

    def test_roadmap_links_to_the_pilot_playbook(self) -> None:
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")

        self.assertIn("[private pilot playbook](docs/pilot-playbook.md)", roadmap)


if __name__ == "__main__":
    unittest.main()
