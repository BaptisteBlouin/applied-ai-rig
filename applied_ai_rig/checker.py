import csv
import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .manifest import Manifest, Profile


LINK = re.compile(r"\[[^]]+\]\(([^)]+)\)")
PLACEHOLDER = re.compile(r"{{[A-Z][A-Z0-9_]*}}")
EXPECTED_CSV_HEADERS = {
    "api_usage.csv": "timestamp_utc,run_id,decision_id,owner,provider,model,purpose,request_count,input_tokens,cached_input_tokens,output_tokens,total_tokens,latency_ms,status,retry_of,measurement,cost_amount,cost_currency,cost_basis,pricing_snapshot,evidence_id,notes",
    "data_register.csv": "data_id,owner,provenance,purpose,classification,personal_data,allowed_destinations,derived_artifacts,retention_until,deletion_status,decision_id,evidence_id,notes",
    "experiments.csv": "timestamp_utc,run_id,decision_id,code_revision,dataset_id,dataset_version,dataset_fingerprint,model,config_ref,hypothesis,variant,primary_metric,primary_value,baseline_run_id,result,decision,api_usage_ref,evidence_id,external_system_ref,notes",
    "action_register.csv": "action_id,tool,side_effect,resource_scope,permission,argument_validation,human_approval,bounded_consumption,escalation,decision_id,evidence_id,notes",
    "incident_register.csv": "incident_id,opened_at,status,owner,impact,operating_limit,model_or_data_dependency,mitigation,rollback,decision_id,evidence_id,closed_at,notes",
}
REQUIRED_HEADINGS = {
    "docs/applied-ai-rig/README.md": "# Applied AI Rig records",
    "docs/applied-ai-rig/OPERATING_PRINCIPLES.md": "# Operating principles",
    "docs/applied-ai-rig/DECISIONS.md": "# Decisions",
    "docs/applied-ai-rig/EVIDENCE.md": "# Evidence",
    "APPLIED_AI_RIG_AGENT.md": "# Applied AI Rig instructions",
}


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    path: str
    message: str


@dataclass(frozen=True)
class CheckResult:
    findings: tuple[Finding, ...]

    @property
    def errors(self) -> tuple[Finding, ...]:
        return tuple(item for item in self.findings if item.severity is Severity.ERROR)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return tuple(item for item in self.findings if item.severity is Severity.WARNING)


def _finding(severity: Severity, path: str, message: str) -> Finding:
    return Finding(severity, path, message)


def check_project(target: Path) -> CheckResult:
    target = target.resolve(strict=False)
    findings: list[Finding] = []
    manifest_path = target / ".applied-ai-rig/manifest.json"
    profile_path = target / ".applied-ai-rig/profile.json"
    if not manifest_path.exists():
        return CheckResult(
            (_finding(Severity.ERROR, ".applied-ai-rig/manifest.json", "manifest.json is missing; run the initializer first."),)
        )
    if not profile_path.exists():
        return CheckResult(
            (_finding(Severity.ERROR, ".applied-ai-rig/profile.json", "profile.json is missing; re-run the initializer."),)
        )

    try:
        manifest = Manifest.from_json(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        return CheckResult((_finding(Severity.ERROR, str(manifest_path.relative_to(target)), f"Invalid manifest: {error}"),))
    try:
        profile = Profile.from_json(profile_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        return CheckResult((_finding(Severity.ERROR, str(profile_path.relative_to(target)), f"Invalid profile: {error}"),))

    if manifest.selected_modules != profile.selected_modules:
        findings.append(
            _finding(
                Severity.ERROR,
                ".applied-ai-rig",
                "Profile and manifest select different modules; re-run the initializer and review the plan.",
            )
        )

    generated_paths: list[Path] = []
    for entry in manifest.files:
        path = target.joinpath(*Path(entry.path).parts)
        generated_paths.append(path)
        if not path.is_file():
            findings.append(_finding(Severity.ERROR, entry.path, "Generated file is missing; restore or re-run the initializer."))
            continue
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        if checksum != entry.original_checksum:
            findings.append(
                _finding(
                    Severity.WARNING,
                    entry.path,
                    "Generated file differs from its installed template; review the local change before updating.",
                )
            )

    for path in generated_paths:
        if not path.is_file() or path.suffix.lower() not in (".md", ".csv"):
            continue
        relative = path.relative_to(target).as_posix()
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            findings.append(_finding(Severity.ERROR, relative, "Generated text file is not valid UTF-8."))
            continue
        if PLACEHOLDER.search(content):
            findings.append(_finding(Severity.ERROR, relative, "Unresolved template placeholder found."))
        expected_heading = REQUIRED_HEADINGS.get(relative)
        if expected_heading and expected_heading not in content.splitlines():
            findings.append(_finding(Severity.ERROR, relative, f"Required heading is missing: {expected_heading}"))
        if path.suffix.lower() == ".md":
            findings.extend(_check_links(target, path, content))
        if path.suffix.lower() == ".csv":
            findings.extend(_check_csv(path, relative, content))

    agent_path = target / "APPLIED_AI_RIG_AGENT.md"
    if agent_path.exists():
        content = agent_path.read_text(encoding="utf-8")
        reference = target / "docs/applied-ai-rig/README.md"
        if "docs/applied-ai-rig/README.md" not in content or not reference.exists():
            findings.append(
                _finding(Severity.ERROR, "APPLIED_AI_RIG_AGENT.md", "Generated agent guidance does not reference an existing Rig README.")
            )

    return CheckResult(tuple(findings))


def _check_links(target: Path, source: Path, content: str) -> list[Finding]:
    findings: list[Finding] = []
    for raw in LINK.findall(content):
        link = raw.split("#", 1)[0]
        if not link or "://" in link or link.startswith("mailto:"):
            continue
        destination = (source.parent / link).resolve(strict=False)
        try:
            destination.relative_to(target)
        except ValueError:
            findings.append(_finding(Severity.ERROR, source.relative_to(target).as_posix(), f"Internal link escapes the project: {raw}"))
            continue
        if not destination.exists():
            findings.append(_finding(Severity.ERROR, source.relative_to(target).as_posix(), f"Broken internal link: {raw}"))
    return findings


def _check_csv(path: Path, relative: str, content: str) -> list[Finding]:
    expected = EXPECTED_CSV_HEADERS.get(path.name)
    if expected is None:
        return []
    rows = list(csv.reader(content.splitlines()))
    actual = ",".join(rows[0]) if rows else ""
    if actual != expected:
        return [_finding(Severity.ERROR, relative, f"CSV header does not match the {path.name} schema.")]
    return []
