import csv
import hashlib
import io
import os
import re
import shlex
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .checker import EXPECTED_CSV_HEADERS, CheckResult, check_project
from .manifest import Manifest, Profile


DECISION_ID = re.compile(r"DEC-[A-Za-z0-9][A-Za-z0-9._-]*\Z")
EVIDENCE_ID = re.compile(r"EVD-[A-Za-z0-9][A-Za-z0-9._-]*\Z")
RUN_ID = re.compile(r"RUN-[A-Za-z0-9][A-Za-z0-9._-]*\Z")
DECISION_ENTRY = re.compile(
    r"^- \*\*Decision ID:\*\*\s+(DEC-[A-Za-z0-9][A-Za-z0-9._-]*)\s*$",
    re.MULTILINE,
)
EVIDENCE_ENTRY = re.compile(
    r"^- \*\*Evidence ID:\*\*\s+(EVD-[A-Za-z0-9][A-Za-z0-9._-]*)\s*$",
    re.MULTILINE,
)


class RecordError(RuntimeError):
    """Raised before a record write when the requested change is unsafe or invalid."""


@dataclass(frozen=True)
class RecordChange:
    target: Path
    relative_path: str
    original_content: str
    original_checksum: str
    addition: str
    record_id: str

    @property
    def destination(self) -> Path:
        return self.target.joinpath(*Path(self.relative_path).parts)

    @property
    def proposed_content(self) -> str:
        separator = "" if not self.original_content or self.original_content.endswith("\n") else "\n"
        return f"{self.original_content}{separator}{self.addition}"


@dataclass(frozen=True)
class ProjectStatus:
    target: Path
    selected_modules: tuple[str, ...]
    check: CheckResult
    counts: Mapping[str, int]
    next_command: tuple[str, ...] | None
    next_instruction: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "counts", MappingProxyType(dict(self.counts)))

    @property
    def next_action(self) -> str:
        if self.next_command is not None:
            return shlex.join(self.next_command)
        return self.next_instruction


def _load_installation(target: Path) -> tuple[Path, Profile, Manifest]:
    target = target.resolve(strict=False)
    profile_path = target / ".applied-ai-rig/profile.json"
    manifest_path = target / ".applied-ai-rig/manifest.json"
    if not profile_path.is_file() or not manifest_path.is_file():
        raise RecordError("Applied AI Rig is not installed in this target; run the initializer first.")
    try:
        profile = Profile.from_json(profile_path.read_text(encoding="utf-8"))
        manifest = Manifest.from_json(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise RecordError(f"Cannot read the Applied AI Rig installation: {error}") from error
    return target, profile, manifest


def _read_managed_file(target: Path, manifest: Manifest, relative_path: str) -> tuple[Path, str, str]:
    if relative_path not in {entry.path for entry in manifest.files}:
        raise RecordError(f"The installed manifest does not manage {relative_path}; re-run the initializer.")
    destination = target.joinpath(*Path(relative_path).parts)
    try:
        destination.resolve(strict=False).relative_to(target)
    except ValueError as error:
        raise RecordError(f"Managed record path escapes the target: {relative_path}") from error
    if not destination.is_file():
        raise RecordError(f"Managed record is missing: {relative_path}; re-run the initializer.")
    try:
        raw = destination.read_bytes()
        content = raw.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise RecordError(f"Cannot read {relative_path}: {error}") from error
    return destination, content, hashlib.sha256(raw).hexdigest()


def _require_identifier(label: str, value: str, pattern: re.Pattern[str]) -> str:
    if not pattern.fullmatch(value):
        expected = pattern.pattern.removesuffix("\\Z")
        raise RecordError(f"{label} must use the {expected} format.")
    return value


def _require_one_line(label: str, value: str) -> str:
    value = value.strip()
    if not value:
        raise RecordError(f"{label} must not be empty.")
    if "\n" in value or "\r" in value or "\x00" in value:
        raise RecordError(f"{label} must be a single text line.")
    if len(value) > 500:
        raise RecordError(f"{label} must be 500 characters or fewer.")
    return value


def _change(
    target: Path,
    manifest: Manifest,
    relative_path: str,
    addition: str,
    record_id: str,
) -> RecordChange:
    _, original, checksum = _read_managed_file(target, manifest, relative_path)
    if not addition.endswith("\n"):
        addition += "\n"
    return RecordChange(target, relative_path, original, checksum, addition, record_id)


def _require_existing_decision(target: Path, manifest: Manifest, decision_id: str) -> None:
    _, decisions, _ = _read_managed_file(
        target, manifest, "docs/applied-ai-rig/DECISIONS.md"
    )
    if decision_id not in DECISION_ENTRY.findall(decisions):
        raise RecordError(f"Decision ID does not exist: {decision_id}")


def propose_decision(
    target: Path,
    record_id: str,
    title: str,
    status: str = "proposed",
) -> RecordChange:
    target, _, manifest = _load_installation(target)
    record_id = _require_identifier("Decision ID", record_id, DECISION_ID)
    title = _require_one_line("Decision title", title)
    if status not in {"proposed", "accepted", "superseded", "rejected"}:
        raise RecordError(f"Unknown decision status: {status}")
    relative = "docs/applied-ai-rig/DECISIONS.md"
    _, content, _ = _read_managed_file(target, manifest, relative)
    if record_id in DECISION_ENTRY.findall(content):
        raise RecordError(f"Decision ID already exists: {record_id}")
    addition = f"""
## {record_id} — {title}

- **Decision ID:** {record_id}
- **Status:** {status}
- **Context:** Unknown — record the constraint or risk that requires this choice.
- **Options:** Unknown — list the real alternatives considered.
- **Decision:** Unknown — record what is selected and why.
- **Consequences:** Unknown — record accepted costs, limitations, or closed options.
- **Revision threshold:** Unknown — define the measurable fact that would change this decision.
- **Supersedes:** None
- **Evidence:** Unknown — link one or more `EVD-...` identifiers.
"""
    return _change(target, manifest, relative, addition, record_id)


def propose_evidence(
    target: Path,
    record_id: str,
    claim: str,
    decision_id: str,
    status: str = "unknown",
) -> RecordChange:
    target, _, manifest = _load_installation(target)
    record_id = _require_identifier("Evidence ID", record_id, EVIDENCE_ID)
    decision_id = _require_identifier("Decision ID", decision_id, DECISION_ID)
    _require_existing_decision(target, manifest, decision_id)
    claim = _require_one_line("Evidence claim", claim)
    if status not in {"measured", "estimated", "unknown"}:
        raise RecordError(f"Unknown evidence status: {status}")
    relative = "docs/applied-ai-rig/EVIDENCE.md"
    _, content, _ = _read_managed_file(target, manifest, relative)
    if record_id in EVIDENCE_ENTRY.findall(content):
        raise RecordError(f"Evidence ID already exists: {record_id}")
    addition = f"""
## {record_id} — {claim}

- **Evidence ID:** {record_id}
- **Claim:** {claim}
- **Status:** {status}
- **Basis:** {status}
- **Source:** Unknown — link the run, test, report, issue, or canonical external system.
- **Scope:** Unknown — state what this evidence covers.
- **Limitations:** Unknown — state what this evidence does not prove.
- **Related decisions:** {decision_id}
"""
    return _change(target, manifest, relative, addition, record_id)


def _safe_csv_cell(label: str, value: str) -> str:
    value = _require_one_line(label, value)
    if value.lstrip().startswith(("=", "+", "@")):
        raise RecordError(f"{label} must not begin with a spreadsheet formula marker.")
    if value.lstrip().startswith("-") and not re.fullmatch(r"-?(?:\d+(?:\.\d*)?|\.\d+)", value):
        raise RecordError(f"{label} must not begin with a spreadsheet formula marker.")
    return value


def propose_experiment(
    target: Path,
    run_id: str,
    decision_id: str,
    model: str,
    metric: str,
    value: str,
    timestamp: str,
) -> RecordChange:
    target, profile, manifest = _load_installation(target)
    if "evaluation" not in profile.selected_modules:
        raise RecordError("The evaluation module is not installed; re-run setup and review that module first.")
    run_id = _require_identifier("Run ID", run_id, RUN_ID)
    decision_id = _require_identifier("Decision ID", decision_id, DECISION_ID)
    _require_existing_decision(target, manifest, decision_id)
    model = _safe_csv_cell("Model", model)
    metric = _safe_csv_cell("Metric", metric)
    value = _safe_csv_cell("Metric value", value)
    timestamp = _require_one_line("Timestamp", timestamp)
    relative = "docs/applied-ai-rig/modules/evaluation/experiments.csv"
    _, content, _ = _read_managed_file(target, manifest, relative)
    rows = list(csv.reader(content.splitlines()))
    if not rows or tuple(rows[0]) != EXPECTED_CSV_HEADERS["experiments.csv"]:
        raise RecordError("The experiments.csv header is invalid; run the structural check before adding a row.")
    if any(len(row) > 1 and row[1] == run_id for row in rows[1:]):
        raise RecordError(f"Run ID already exists: {run_id}")
    row = [
        timestamp,
        run_id,
        decision_id,
        "unknown",
        "unknown",
        "unknown",
        "unknown",
        model,
        "unknown",
        "Unknown — complete before interpreting the result.",
        "candidate",
        metric,
        value,
        "",
        "pending",
        "pending",
        "",
        "",
        "",
        "Created by the Applied AI Rig CLI; complete unknown fields before citing.",
    ]
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerow(row)
    return _change(target, manifest, relative, output.getvalue(), run_id)


def apply_record_change(change: RecordChange) -> None:
    destination = change.destination
    try:
        destination.resolve(strict=False).relative_to(change.target.resolve(strict=False))
    except ValueError as error:
        raise RecordError(f"Managed record path escapes the target: {change.relative_path}") from error
    try:
        current = destination.read_bytes()
    except OSError as error:
        raise RecordError(f"Cannot verify {change.relative_path}: {error}") from error
    if hashlib.sha256(current).hexdigest() != change.original_checksum:
        raise RecordError(f"{change.relative_path} changed after the preview; no record was written.")
    staged_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=".rig-record-",
            dir=destination.parent,
            delete=False,
        ) as staged:
            staged.write(change.proposed_content)
            staged.flush()
            os.fsync(staged.fileno())
            staged_path = Path(staged.name)
        try:
            destination.resolve(strict=False).relative_to(change.target.resolve(strict=False))
        except ValueError as error:
            raise RecordError(
                f"Managed record path escapes the target: {change.relative_path}"
            ) from error
        if hashlib.sha256(destination.read_bytes()).hexdigest() != change.original_checksum:
            raise RecordError(
                f"{change.relative_path} changed after the preview; no record was written."
            )
        os.chmod(staged_path, destination.stat().st_mode & 0o777)
        os.replace(staged_path, destination)
    except OSError as error:
        raise RecordError(f"Could not write {change.relative_path}: {error}") from error
    finally:
        if staged_path is not None:
            staged_path.unlink(missing_ok=True)


def _csv_record_count(path: Path) -> int:
    try:
        rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    except (OSError, UnicodeError, csv.Error):
        return 0
    return max(0, len(rows) - 1)


def project_status(target: Path) -> ProjectStatus:
    target, profile, manifest = _load_installation(target)
    decisions_path, decisions, _ = _read_managed_file(
        target, manifest, "docs/applied-ai-rig/DECISIONS.md"
    )
    evidence_path, evidence, _ = _read_managed_file(
        target, manifest, "docs/applied-ai-rig/EVIDENCE.md"
    )
    del decisions_path, evidence_path
    decision_ids = DECISION_ENTRY.findall(decisions)
    evidence_ids = EVIDENCE_ENTRY.findall(evidence)
    counts: dict[str, int] = {
        "decisions": len(decision_ids),
        "evidence": len(evidence_ids),
    }
    register_names = {
        "api_usage.csv": "api_usage",
        "model_register.csv": "models",
        "data_register.csv": "data",
        "experiments.csv": "experiments",
        "action_register.csv": "actions",
        "misuse_cases.csv": "misuse_cases",
        "incident_register.csv": "incidents",
        "service_register.csv": "services",
    }
    for entry in manifest.files:
        name = Path(entry.path).name
        if name in register_names:
            counts[register_names[name]] = _csv_record_count(target.joinpath(*Path(entry.path).parts))

    next_command: tuple[str, ...] | None
    next_instruction = ""
    if not decision_ids:
        next_command = (
            "add",
            "decision",
            str(target),
            "--id",
            "DEC-YYYYMMDD-short-name",
            "--title",
            "Describe the choice",
        )
    elif not evidence_ids:
        next_command = (
            "add",
            "evidence",
            str(target),
            "--id",
            "EVD-YYYYMMDD-short-name",
            "--claim",
            "Describe the supported claim",
            "--decision",
            decision_ids[-1],
        )
    elif "evaluation" in profile.selected_modules and counts.get("experiments", 0) == 0:
        next_command = (
            "add",
            "experiment",
            str(target),
            "--run-id",
            "RUN-short-name",
            "--decision",
            decision_ids[-1],
            "--model",
            "model-name",
            "--metric",
            "metric-name",
            "--value",
            "unknown",
        )
    elif "model-api" in profile.selected_modules and counts.get("models", 0) == 0:
        next_command = None
        next_instruction = (
            "Complete the minimum useful fields in "
            "docs/applied-ai-rig/modules/model-api/model_register.csv."
        )
    elif "data" in profile.selected_modules and counts.get("data", 0) == 0:
        next_command = None
        next_instruction = (
            "Complete the minimum useful fields in "
            "docs/applied-ai-rig/modules/data/data_register.csv."
        )
    elif "agentic-runtime" in profile.selected_modules and counts.get("actions", 0) == 0:
        next_command = None
        next_instruction = (
            "Complete the minimum useful fields in "
            "docs/applied-ai-rig/modules/agentic-runtime/action_register.csv."
        )
    elif "agentic-runtime" in profile.selected_modules and counts.get("misuse_cases", 0) == 0:
        next_command = None
        next_instruction = (
            "Record one representative denial path in "
            "docs/applied-ai-rig/modules/agentic-runtime/misuse_cases.csv."
        )
    elif "operations" in profile.selected_modules and counts.get("services", 0) == 0:
        next_command = None
        next_instruction = (
            "Complete the minimum useful fields in "
            "docs/applied-ai-rig/modules/operations/service_register.csv."
        )
    else:
        next_command = None
        next_instruction = (
            "Review docs/applied-ai-rig/DELIVERY_CHECKLIST.md at the next meaningful handoff."
        )
    return ProjectStatus(
        target=target,
        selected_modules=profile.selected_modules,
        check=check_project(target),
        counts=counts,
        next_command=next_command,
        next_instruction=next_instruction,
    )
