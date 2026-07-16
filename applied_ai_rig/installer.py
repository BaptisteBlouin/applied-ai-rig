import hashlib
import difflib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

from .manifest import GeneratedFile, Manifest, Profile


PLACEHOLDER = re.compile(r"{{([A-Z][A-Z0-9_]*)}}")
CANONICAL_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "SECURITY.md",
    "docs/adr",
    "docs/decisions",
    "mlruns",
)


class FileStatus(str, Enum):
    NEW = "new"
    UNCHANGED = "unchanged"
    MODIFIED = "modified-generated"
    CONFLICT = "untracked-conflict"


class InstallationCancelled(RuntimeError):
    """Raised before writes when the user rejects any planned replacement."""


class PreservationError(RuntimeError):
    """Raised before writes when a conflict cannot be preserved unambiguously."""


@dataclass(frozen=True)
class PlannedFile:
    relative_path: PurePosixPath
    content: str
    status: FileStatus
    known_checksum: str | None = None

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PreservedFile:
    original_path: PurePosixPath
    preserved_path: PurePosixPath
    content: bytes
    previous_content: bytes | None

    @property
    def checksum(self) -> str:
        return sha256_bytes(self.content)


@dataclass(frozen=True)
class InstallationPlan:
    target: Path
    profile: Profile
    files: tuple[PlannedFile, ...]
    manual_integrations: tuple[str, ...]
    preservations: tuple[PreservedFile, ...] = ()


def render_template(template: str, values: Mapping[str, str]) -> str:
    normalized = template.replace("\r\n", "\n").replace("\r", "\n")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise ValueError(f"Unresolved template placeholder: {key}")
        return values[key]

    rendered = PLACEHOLDER.sub(replace, normalized)
    unresolved = PLACEHOLDER.search(rendered)
    if unresolved:
        raise ValueError(f"Unresolved template placeholder: {unresolved.group(1)}")
    return rendered


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def classify_file(destination: Path, rendered: bytes, known_checksum: str | None) -> FileStatus:
    if not destination.exists():
        return FileStatus.NEW
    current = destination.read_bytes()
    if current == rendered:
        return FileStatus.UNCHANGED
    if known_checksum is None:
        return FileStatus.CONFLICT
    return FileStatus.MODIFIED


def _safe_destination(target: Path, relative_path: PurePosixPath) -> Path:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Template destination escapes target: {relative_path}")
    destination = target.joinpath(*relative_path.parts)
    try:
        destination.resolve(strict=False).relative_to(target.resolve(strict=False))
    except ValueError as error:
        raise ValueError(f"Template destination escapes target: {relative_path}") from error
    return destination


def _load_inventory(directory: Path) -> list[dict[str, str]]:
    inventory = directory / "inventory.json"
    if not inventory.exists():
        return []
    data = json.loads(inventory.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Template inventory must be a list: {inventory}")
    return [dict(item) for item in data]


def _module_links(selected_modules: tuple[str, ...]) -> str:
    if not selected_modules:
        return ""
    lines = ["", "Selected modules:"]
    for module_id in selected_modules:
        lines.append(f"- [{module_id}](modules/{module_id}/README.md)")
    return "\n".join(lines)


def build_plan(
    target: Path,
    profile: Profile,
    template_root: Path,
    known_checksums: Mapping[str, str] | None = None,
    known_manual_integrations: Sequence[str] = (),
) -> InstallationPlan:
    known_checksums = known_checksums or {}
    target = target.resolve(strict=False)
    values = {
        "PROJECT_NAME": target.name or "project",
        "MODULE_LINKS": _module_links(profile.selected_modules),
        "SELECTED_MODULES": ", ".join(profile.selected_modules) or "none",
    }

    entries = _load_inventory(template_root / "core")
    if profile.selected_modules:
        entries.extend(_load_inventory(template_root / "shared"))
    for module_id in profile.selected_modules:
        entries.extend(_load_inventory(template_root / "modules" / module_id))

    planned: list[PlannedFile] = []
    for entry in entries:
        source = template_root / "core" / entry["source"]
        if entry.get("shared"):
            source = template_root / "shared" / entry["source"]
        if "module" in entry:
            source = template_root / "modules" / entry["module"] / entry["source"]
        relative = PurePosixPath(entry["destination"])
        destination = _safe_destination(target, relative)
        content = render_template(source.read_text(encoding="utf-8"), values)
        known = known_checksums.get(relative.as_posix())
        status = classify_file(destination, content.encode("utf-8"), known)
        planned.append(PlannedFile(relative, content, status, known))

    profile_relative = PurePosixPath(".applied-ai-rig/profile.json")
    profile_content = profile.to_json()
    profile_destination = _safe_destination(target, profile_relative)
    profile_known = known_checksums.get(profile_relative.as_posix())
    planned.append(
        PlannedFile(
            profile_relative,
            profile_content,
            classify_file(profile_destination, profile_content.encode("utf-8"), profile_known),
            profile_known,
        )
    )

    manual = tuple(
        sorted(
            set(known_manual_integrations)
            | {path for path in CANONICAL_FILES if (target / path).exists()}
        )
    )
    return InstallationPlan(
        target,
        profile,
        tuple(sorted(planned, key=lambda item: item.relative_path.as_posix())),
        manual,
    )


def _preserved_sidecar(relative_path: PurePosixPath) -> PurePosixPath:
    if relative_path.suffix.lower() != ".md":
        raise PreservationError(
            f"Cannot automatically preserve non-Markdown conflict: {relative_path.as_posix()}"
        )
    return relative_path.with_name(
        f"{relative_path.stem}.project{relative_path.suffix}"
    )


def preserve_conflicts(plan: InstallationPlan) -> InstallationPlan:
    """Keep untracked Markdown conflicts beside the generated files."""
    planned_paths = {item.relative_path for item in plan.files}
    preservations: list[PreservedFile] = []
    manual_integrations = set(plan.manual_integrations)
    for item in plan.files:
        if item.status is not FileStatus.CONFLICT:
            continue
        original = _safe_destination(plan.target, item.relative_path)
        preserved_path = _preserved_sidecar(item.relative_path)
        if preserved_path in planned_paths:
            raise PreservationError(
                f"Preservation path is already managed by the Rig: {preserved_path.as_posix()}"
            )
        preserved = _safe_destination(plan.target, preserved_path)
        content = original.read_bytes()
        previous_content = preserved.read_bytes() if preserved.exists() else None
        if previous_content is not None and previous_content != content:
            raise PreservationError(
                f"Preservation path already contains different content: {preserved_path.as_posix()}"
            )
        preservations.append(
            PreservedFile(
                item.relative_path,
                preserved_path,
                content,
                previous_content,
            )
        )
        manual_integrations.add(preserved_path.as_posix())
    return InstallationPlan(
        target=plan.target,
        profile=plan.profile,
        files=plan.files,
        manual_integrations=tuple(sorted(manual_integrations)),
        preservations=tuple(preservations),
    )


def _require_unchanged(
    target: Path,
    relative_path: PurePosixPath,
    expected: bytes | None,
    label: str,
) -> None:
    destination = _safe_destination(target, relative_path)
    matches = (
        not destination.exists()
        if expected is None
        else destination.is_file() and destination.read_bytes() == expected
    )
    if not matches:
        raise InstallationCancelled(
            f"{label} changed after preview: {relative_path.as_posix()}; no files were changed."
        )


def required_paths(profile: Profile, template_root: Path) -> tuple[str, ...]:
    entries = _load_inventory(template_root / "core")
    if profile.selected_modules:
        entries.extend(_load_inventory(template_root / "shared"))
    for module_id in profile.selected_modules:
        entries.extend(_load_inventory(template_root / "modules" / module_id))
    paths = [entry["destination"] for entry in entries]
    paths.append(".applied-ai-rig/profile.json")
    return tuple(sorted(paths))


def unified_diff(item: PlannedFile, destination: Path) -> str:
    try:
        current = destination.read_text(encoding="utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return "Binary or non-UTF-8 content differs; no text diff available.\n"
    proposed = item.content.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            current,
            proposed,
            fromfile=f"current/{item.relative_path.as_posix()}",
            tofile=f"proposed/{item.relative_path.as_posix()}",
        )
    )


def install_plan(
    plan: InstallationPlan,
    approve: Callable[[PlannedFile], bool],
    installed_at: str,
    fail_after: int | None = None,
) -> Manifest:
    created_directories: set[Path] = set()
    selected: list[PlannedFile] = []
    manifest_files: list[GeneratedFile] = []
    for item in plan.files:
        if item.status is FileStatus.UNCHANGED:
            manifest_files.append(GeneratedFile(item.relative_path.as_posix(), item.checksum))
            continue
        if item.status in (FileStatus.MODIFIED, FileStatus.CONFLICT) and not approve(item):
            raise InstallationCancelled(
                f"Installation cancelled; {item.relative_path.as_posix()} was not approved."
            )
        selected.append(item)
        manifest_files.append(GeneratedFile(item.relative_path.as_posix(), item.checksum))

    manifest = Manifest(
        schema_version=1,
        rig_version=plan.profile.rig_version,
        installed_at=installed_at,
        selected_modules=plan.profile.selected_modules,
        files=tuple(sorted(manifest_files, key=lambda entry: entry.path)),
        manual_integrations=plan.manual_integrations,
        manual_integration_statuses={path: "proposed" for path in plan.manual_integrations},
    )
    manifest_relative = PurePosixPath(".applied-ai-rig/manifest.json")
    manifest_destination = _safe_destination(plan.target, manifest_relative)
    if not selected and manifest_destination.exists():
        existing = Manifest.from_json(manifest_destination.read_text(encoding="utf-8"))
        if (
            existing.rig_version == manifest.rig_version
            and existing.selected_modules == manifest.selected_modules
            and existing.files == manifest.files
            and existing.manual_integrations == manifest.manual_integrations
            and existing.manual_integration_statuses == manifest.manual_integration_statuses
        ):
            return existing

    for preservation in plan.preservations:
        _require_unchanged(
            plan.target,
            preservation.original_path,
            preservation.content,
            "Conflict",
        )
        _require_unchanged(
            plan.target,
            preservation.preserved_path,
            preservation.previous_content,
            "Preservation path",
        )

    staging_parent = plan.target / ".applied-ai-rig"
    _mkdir(staging_parent, created_directories)
    staging = Path(tempfile.mkdtemp(prefix=".rig-staging-", dir=staging_parent))

    staged: list[tuple[Path, Path]] = []
    for preservation in plan.preservations:
        source = staging.joinpath(*preservation.preserved_path.parts)
        _mkdir(source.parent, created_directories)
        source.write_bytes(preservation.content)
        staged.append(
            (source, _safe_destination(plan.target, preservation.preserved_path))
        )
    for item in selected:
        source = staging.joinpath(*item.relative_path.parts)
        _mkdir(source.parent, created_directories)
        source.write_text(item.content, encoding="utf-8", newline="\n")
        staged.append((source, _safe_destination(plan.target, item.relative_path)))
    staged_manifest = staging / "manifest.json"
    staged_manifest.write_text(manifest.to_json(), encoding="utf-8", newline="\n")
    staged.append((staged_manifest, manifest_destination))

    backups: dict[Path, bytes | None] = {}
    written: list[Path] = []
    expected_preserved_state = {
        item.preserved_path: item.previous_content
        for item in plan.preservations
    }
    expected_original_state = {
        item.original_path: item.content
        for item in plan.preservations
    }
    expected_paths = {
        _safe_destination(plan.target, relative): (relative, expected, label)
        for states, label in (
            (expected_preserved_state, "Preservation path"),
            (expected_original_state, "Conflict"),
        )
        for relative, expected in states.items()
    }
    try:
        for index, (source, destination) in enumerate(staged, start=1):
            if destination in expected_paths:
                relative, expected, label = expected_paths[destination]
                _require_unchanged(plan.target, relative, expected, label)
            backups[destination] = destination.read_bytes() if destination.exists() else None
            _mkdir(destination.parent, created_directories)
            os.replace(source, destination)
            written.append(destination)
            if fail_after is not None and index >= fail_after:
                raise RuntimeError("simulated write failure")
    except Exception:
        for destination in reversed(written):
            previous = backups[destination]
            if previous is None:
                destination.unlink(missing_ok=True)
            else:
                destination.write_bytes(previous)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        for directory in sorted(created_directories, key=lambda path: len(path.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
    return manifest


def _mkdir(directory: Path, created: set[Path]) -> None:
    missing: list[Path] = []
    current = directory
    while not current.exists():
        missing.append(current)
        current = current.parent
    directory.mkdir(parents=True, exist_ok=True)
    created.update(missing)
