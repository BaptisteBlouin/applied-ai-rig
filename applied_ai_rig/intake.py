from dataclasses import dataclass
from typing import Mapping


MODULE_IDS = ("model-api", "data", "evaluation", "agentic-runtime", "operations")


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    recommends: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class ModuleInfo:
    id: str
    title: str
    recommended_when: str
    covers: str
    generated: tuple[str, ...]


MODULE_INFO = {
    "model-api": ModuleInfo(
        "model-api",
        "Model API",
        "The project uses credentials, external inference, embeddings, reranking, or metered models.",
        "Model inventory, credential boundaries, provider terms, limits, retries, validation, usage, and cost.",
        ("README.md", "model_register.csv", "api_usage.csv"),
    ),
    "data": ModuleInfo(
        "data",
        "Data",
        "The project handles supplied, persisted, personal, confidential, or third-party data.",
        "Provenance, access, destinations, derivatives, quality, backups, retention, and deletion evidence.",
        ("README.md", "data_register.csv"),
    ),
    "evaluation": ModuleInfo(
        "evaluation",
        "Evaluation",
        "Variants are compared, behavior can regress, or quality, safety, latency, or cost claims are made.",
        "Evaluation protocol, held-out data, thresholds, uncertainty, judges, experiments, and error analysis.",
        ("README.md", "EVALUATION_PLAN.md", "experiments.csv"),
    ),
    "agentic-runtime": ModuleInfo(
        "agentic-runtime",
        "Agentic runtime",
        "Model-driven behavior can call tools, communicate externally, spend money, or mutate resources.",
        "Permissions, approvals, injection, exfiltration, idempotency, compensation, audit, and misuse cases.",
        ("README.md", "action_register.csv", "misuse_cases.csv"),
    ),
    "operations": ModuleInfo(
        "operations",
        "Operations",
        "The application serves users or runs as a scheduled, long-lived, or production service.",
        "Ownership, service levels, alerts, runbooks, budgets, recovery, incidents, and regressions.",
        ("README.md", "service_register.csv", "incident_register.csv"),
    ),
}


SETUP_PROFILES = {
    "minimal": (),
    "api-rag": ("model-api", "data", "evaluation"),
    "agent": ("model-api", "data", "evaluation", "agentic-runtime"),
    "production": ("model-api", "data", "evaluation", "operations"),
}


QUESTIONS = (
    Question(
        "external_model_api",
        "Will this project call an external model or embedding API?",
        ("model-api",),
        "Track credential boundaries, model usage, and attributable cost.",
    ),
    Question(
        "sensitive_or_supplied_data",
        "Will it process supplied, personal, confidential, or third-party data?",
        ("data",),
        "Record provenance, allowed destinations, derivatives, and retention.",
    ),
    Question(
        "persist_model_content",
        "Will prompts, model outputs, embeddings, or derived content be persisted?",
        ("data",),
        "Treat persisted and derived content according to its source sensitivity.",
    ),
    Question(
        "quality_claims",
        "Will variants be compared or quality claims be shared with stakeholders?",
        ("evaluation",),
        "Link claims to reproducible runs, metrics, and known limitations.",
    ),
    Question(
        "side_effects",
        "Can the application call tools or take actions with side effects?",
        ("agentic-runtime",),
        "Record permission boundaries, approvals, and bounded consumption.",
    ),
    Question(
        "production_use",
        "Will the application run in production or serve users?",
        ("operations",),
        "Define ownership, operating limits, releases, rollback, and incidents.",
    ),
)


def recommend_modules(answers: Mapping[str, bool]) -> dict[str, str]:
    questions = {question.id: question for question in QUESTIONS}
    unknown = set(answers) - set(questions)
    if unknown:
        raise ValueError(f"Unknown question ID: {sorted(unknown)[0]}")

    recommendations: dict[str, list[str]] = {}
    for question_id, answer in answers.items():
        if not isinstance(answer, bool):
            raise ValueError(f"Answer for {question_id} must be true or false")
        if not answer:
            continue
        question = questions[question_id]
        for module_id in question.recommends:
            recommendations.setdefault(module_id, []).append(question.reason)

    return {module_id: " ".join(reasons) for module_id, reasons in recommendations.items()}
