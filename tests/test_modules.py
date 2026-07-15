import tempfile
import unittest
from pathlib import Path

from applied_ai_rig.installer import build_plan
from applied_ai_rig.manifest import Profile


ROOT = Path(__file__).resolve().parents[1]


def profile(*modules: str) -> Profile:
    return Profile(1, "0.1.0", {}, tuple(modules), (), {})


def plan_content(*modules: str) -> tuple[set[str], str]:
    with tempfile.TemporaryDirectory() as directory:
        plan = build_plan(Path(directory), profile(*modules), ROOT / "templates")
    return (
        {item.relative_path.as_posix() for item in plan.files},
        "\n".join(item.content for item in plan.files),
    )


class ModelApiModuleTests(unittest.TestCase):
    def test_model_api_records_usage_without_secrets_or_private_endpoints(self) -> None:
        paths, content = plan_content("model-api")

        self.assertIn("docs/applied-ai-rig/modules/model-api/api_usage.csv", paths)
        for field in ("input_tokens", "output_tokens", "cost_basis", "retry_of"):
            self.assertIn(field, content)
        self.assertIn("unknown", content)
        self.assertNotIn("api_key,", content.lower())


class DataModuleTests(unittest.TestCase):
    def test_data_module_covers_sources_derivatives_destinations_and_deletion(self) -> None:
        paths, content = plan_content("data")

        self.assertIn("docs/applied-ai-rig/modules/data/data_register.csv", paths)
        for phrase in ("provenance", "derived artifacts", "allowed destinations", "deletion"):
            self.assertIn(phrase, content.lower())
        self.assertIn("does not prove anonymization", content.lower())


class EvaluationModuleTests(unittest.TestCase):
    def test_evaluation_module_links_decisions_runs_and_external_systems(self) -> None:
        paths, content = plan_content("evaluation")

        self.assertIn("docs/applied-ai-rig/modules/evaluation/experiments.csv", paths)
        for field in ("run_id", "decision_id", "code_revision", "dataset_version", "evidence_id"):
            self.assertIn(field, content)
        self.assertIn("external system", content.lower())


class AgenticRuntimeModuleTests(unittest.TestCase):
    def test_agentic_module_records_approval_and_side_effect_boundaries(self) -> None:
        _, content = plan_content("agentic-runtime")

        for phrase in ("side effect", "human approval", "bounded consumption", "tool arguments"):
            self.assertIn(phrase, content.lower())
        self.assertIn("not a runtime policy engine", content.lower())


class OperationsModuleTests(unittest.TestCase):
    def test_operations_module_covers_run_ownership_and_recovery(self) -> None:
        _, content = plan_content("operations")

        for phrase in ("owner", "health", "operating limit", "rollback", "incident"):
            self.assertIn(phrase, content.lower())
        self.assertIn("does not deploy", content.lower())


class ModuleCompositionTests(unittest.TestCase):
    def test_core_only_has_no_optional_module_paths_or_links(self) -> None:
        paths, content = plan_content()

        self.assertFalse(any("/modules/" in path for path in paths))
        self.assertNotIn("Selected modules:", content)

    def test_selected_subset_contains_only_selected_modules(self) -> None:
        paths, content = plan_content("data", "evaluation")

        module_paths = {path.split("/modules/")[1].split("/")[0] for path in paths if "/modules/" in path}
        self.assertEqual(module_paths, {"data", "evaluation"})
        self.assertIn("[data](modules/data/README.md)", content)
        self.assertIn("[evaluation](modules/evaluation/README.md)", content)

    def test_all_modules_have_readme_and_records(self) -> None:
        modules = ("model-api", "data", "evaluation", "agentic-runtime", "operations")
        paths, _ = plan_content(*modules)

        for module_id in modules:
            with self.subTest(module_id=module_id):
                prefix = f"docs/applied-ai-rig/modules/{module_id}/"
                self.assertIn(prefix + "README.md", paths)
                self.assertTrue(any(path.startswith(prefix) and path.endswith(".csv") for path in paths))


if __name__ == "__main__":
    unittest.main()
