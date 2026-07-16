import csv
import tempfile
import unittest
from pathlib import Path

from applied_ai_rig.installer import build_plan, install_plan
from applied_ai_rig.manifest import Profile
from applied_ai_rig.records import (
    RecordError,
    apply_record_change,
    project_status,
    propose_decision,
    propose_evidence,
    propose_experiment,
)


ROOT = Path(__file__).resolve().parents[1]


def install_fixture(target: Path, *modules: str) -> None:
    profile = Profile(1, "0.1.0", {}, tuple(modules), (), {})
    plan = build_plan(target, profile, ROOT / "applied_ai_rig" / "templates")
    install_plan(plan, approve=lambda _: True, installed_at="2026-07-16T10:00:00Z")


class RecordChangeTests(unittest.TestCase):
    def test_decision_is_previewed_before_an_explicit_atomic_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            path = target / "docs/applied-ai-rig/DECISIONS.md"
            before = path.read_text(encoding="utf-8")

            change = propose_decision(
                target,
                record_id="DEC-20260716-model-choice",
                title="Choose the initial model",
            )

            self.assertEqual(path.read_text(encoding="utf-8"), before)
            self.assertIn("## DEC-20260716-model-choice — Choose the initial model", change.addition)
            self.assertIn("**Status:** proposed", change.addition)
            apply_record_change(change)

            content = path.read_text(encoding="utf-8")
            self.assertIn("**Decision ID:** DEC-20260716-model-choice", content)
            self.assertTrue(content.endswith("\n"))

    def test_decision_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            change = propose_decision(target, "DEC-1", "Choose a model")
            apply_record_change(change)

            with self.assertRaisesRegex(RecordError, "already exists"):
                propose_decision(target, "DEC-1", "Choose another model")

    def test_record_write_rejects_a_file_changed_after_preview(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            change = propose_decision(target, "DEC-1", "Choose a model")
            change.destination.write_text("concurrent edit\n", encoding="utf-8")

            with self.assertRaisesRegex(RecordError, "changed after the preview"):
                apply_record_change(change)

            final = change.destination.read_text(encoding="utf-8")

        self.assertEqual(final, "concurrent edit\n")

    def test_evidence_records_basis_and_related_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            apply_record_change(
                propose_decision(target, "DEC-20260716-model-choice", "Choose a model")
            )

            change = propose_evidence(
                target,
                record_id="EVD-20260716-latency",
                claim="Candidate latency is below the acceptance threshold",
                decision_id="DEC-20260716-model-choice",
                status="measured",
            )

        self.assertIn("**Status:** measured", change.addition)
        self.assertIn("**Basis:** measured", change.addition)
        self.assertIn("**Related decisions:** DEC-20260716-model-choice", change.addition)

    def test_evidence_rejects_a_missing_related_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)

            with self.assertRaisesRegex(RecordError, "Decision ID does not exist"):
                propose_evidence(
                    target,
                    record_id="EVD-001",
                    claim="A claim",
                    decision_id="DEC-missing",
                )

    def test_evidence_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            apply_record_change(propose_decision(target, "DEC-001", "Choose a model"))
            apply_record_change(
                propose_evidence(target, "EVD-001", "Candidate passed", "DEC-001")
            )

            with self.assertRaisesRegex(RecordError, "already exists"):
                propose_evidence(target, "EVD-001", "Another claim", "DEC-001")

    def test_experiment_requires_the_evaluation_module(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)

            with self.assertRaisesRegex(RecordError, "evaluation module"):
                propose_experiment(
                    target,
                    run_id="RUN-001",
                    decision_id="DEC-001",
                    model="model-a",
                    metric="accuracy",
                    value="0.91",
                    timestamp="2026-07-16T10:00:00Z",
                )

    def test_experiment_append_preserves_the_register_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target, "evaluation")
            apply_record_change(propose_decision(target, "DEC-001", "Choose a model"))
            change = propose_experiment(
                target,
                run_id="RUN-001",
                decision_id="DEC-001",
                model="model-a",
                metric="accuracy",
                value="0.91",
                timestamp="2026-07-16T10:00:00Z",
            )
            apply_record_change(change)

            rows = list(csv.reader(change.destination.read_text(encoding="utf-8").splitlines()))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], "2026-07-16T10:00:00Z")
        self.assertEqual(rows[1][1], "RUN-001")
        self.assertEqual(rows[1][2], "DEC-001")
        self.assertEqual(rows[1][7], "model-a")
        self.assertEqual(rows[1][11:13], ["accuracy", "0.91"])

    def test_experiment_rejects_a_missing_related_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target, "evaluation")

            with self.assertRaisesRegex(RecordError, "Decision ID does not exist"):
                propose_experiment(
                    target,
                    run_id="RUN-001",
                    decision_id="DEC-missing",
                    model="model-a",
                    metric="accuracy",
                    value="0.91",
                    timestamp="2026-07-16T10:00:00Z",
                )

    def test_experiment_rejects_duplicate_run_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target, "evaluation")
            apply_record_change(propose_decision(target, "DEC-001", "Choose a model"))
            first = propose_experiment(
                target,
                "RUN-001",
                "DEC-001",
                "model-a",
                "accuracy",
                "0.91",
                "2026-07-16T10:00:00Z",
            )
            apply_record_change(first)

            with self.assertRaisesRegex(RecordError, "already exists"):
                propose_experiment(
                    target,
                    "RUN-001",
                    "DEC-001",
                    "model-b",
                    "accuracy",
                    "0.92",
                    "2026-07-16T11:00:00Z",
                )

    def test_record_write_rechecks_that_the_destination_stays_inside_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            target = Path(directory)
            install_fixture(target)
            change = propose_decision(target, "DEC-1", "Choose a model")
            decisions = target / "docs/applied-ai-rig/DECISIONS.md"
            decisions.unlink()
            decisions.symlink_to(Path(outside) / "DECISIONS.md")
            (Path(outside) / "DECISIONS.md").write_text(
                change.original_content, encoding="utf-8"
            )

            with self.assertRaisesRegex(RecordError, "escapes the target"):
                apply_record_change(change)


class ProjectStatusTests(unittest.TestCase):
    def test_empty_project_recommends_the_first_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target, "evaluation")

            status = project_status(target)

        self.assertEqual(status.counts["decisions"], 0)
        self.assertEqual(status.counts["evidence"], 0)
        self.assertEqual(status.counts["experiments"], 0)
        self.assertIn("add decision", status.next_action)

    def test_status_counts_records_and_advances_to_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target)
            apply_record_change(propose_decision(target, "DEC-1", "Choose a model"))

            status = project_status(target)

        self.assertEqual(status.counts["decisions"], 1)
        self.assertIn("add evidence", status.next_action)
        self.assertIn("DEC-1", status.next_action)

    def test_status_advances_from_experiment_to_the_next_risk_register(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            install_fixture(target, "model-api", "data", "evaluation")
            apply_record_change(propose_decision(target, "DEC-1", "Choose a model"))
            apply_record_change(
                propose_evidence(target, "EVD-1", "Candidate passed", "DEC-1", "measured")
            )
            apply_record_change(
                propose_experiment(
                    target,
                    "RUN-1",
                    "DEC-1",
                    "model-a",
                    "accuracy",
                    "0.91",
                    "2026-07-16T10:00:00Z",
                )
            )

            status = project_status(target)

        self.assertIn("model_register.csv", status.next_action)
        self.assertIsNone(status.next_command)


if __name__ == "__main__":
    unittest.main()
