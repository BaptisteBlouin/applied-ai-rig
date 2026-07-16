import csv
import re
import unittest
from pathlib import Path

from applied_ai_rig.checker import EXPECTED_CSV_HEADERS


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
DECISION_ID = re.compile(r"^- \*\*Decision ID:\*\*\s+(DEC-[A-Za-z0-9._-]+)$", re.MULTILINE)
EVIDENCE_ID = re.compile(r"^- \*\*Evidence ID:\*\*\s+(EVD-[A-Za-z0-9._-]+)$", re.MULTILINE)


class WorkedExampleTests(unittest.TestCase):
    def test_three_examples_cover_the_primary_adoption_scenarios(self) -> None:
        directories = {path.name for path in EXAMPLES.iterdir() if path.is_dir()}

        self.assertEqual(
            directories,
            {"rag-assistant", "tool-agent", "production-service"},
        )

    def test_examples_are_synthetic_linked_and_decision_complete(self) -> None:
        for directory in (path for path in EXAMPLES.iterdir() if path.is_dir()):
            with self.subTest(example=directory.name):
                readme = (directory / "README.md").read_text(encoding="utf-8")
                decisions = (directory / "DECISIONS.md").read_text(encoding="utf-8")
                evidence = (directory / "EVIDENCE.md").read_text(encoding="utf-8")
                self.assertIn("synthetic", readme.lower())
                self.assertIn("decision -> evidence", readme.lower())
                self.assertTrue(DECISION_ID.findall(decisions))
                self.assertTrue(EVIDENCE_ID.findall(evidence))
                self.assertNotIn("**Basis:**", evidence)
                for raw in LINK.findall(readme):
                    if "://" not in raw:
                        self.assertTrue((directory / raw.split("#", 1)[0]).exists(), raw)

    def test_example_registers_keep_the_product_schemas_and_resolve_ids(self) -> None:
        for directory in (path for path in EXAMPLES.iterdir() if path.is_dir()):
            decisions = set(
                DECISION_ID.findall((directory / "DECISIONS.md").read_text(encoding="utf-8"))
            )
            evidence = set(
                EVIDENCE_ID.findall((directory / "EVIDENCE.md").read_text(encoding="utf-8"))
            )
            registers = list(directory.glob("*.csv"))
            self.assertTrue(registers, directory.name)
            for path in registers:
                with self.subTest(example=directory.name, register=path.name):
                    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
                    self.assertEqual(tuple(rows[0]), EXPECTED_CSV_HEADERS[path.name])
                    self.assertTrue(rows)
                    for row in rows:
                        self.assertNotIn(None, row)
                        self.assertNotIn(None, row.values())
                        if row.get("decision_id"):
                            self.assertIn(row["decision_id"], decisions)
                        if row.get("evidence_id"):
                            self.assertIn(row["evidence_id"], evidence)


if __name__ == "__main__":
    unittest.main()
