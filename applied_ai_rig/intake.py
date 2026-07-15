from dataclasses import dataclass
from typing import Mapping


MODULE_IDS = ("model-api", "data", "evaluation", "agentic-runtime", "operations")


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    recommends: tuple[str, ...]
    reason: str


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
