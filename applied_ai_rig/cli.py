import argparse
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from . import __version__
from .checker import check_project
from .installer import (
    FileStatus,
    InstallationPlan,
    PlannedFile,
    build_plan,
    install_plan,
    unified_diff,
)
from .intake import MODULE_IDS, QUESTIONS, recommend_modules
from .manifest import Manifest, Profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="init.py",
        description="Install Applied AI Rig into an applied-AI project.",
    )
    parser.add_argument("target", nargs="?", default=".", help="Target project directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--check", action="store_true", help="Run structural checks on a target")
    parser.add_argument("--modules", help="Comma-separated optional module IDs")
    parser.add_argument("--non-interactive", action="store_true", help="Disable interactive prompts")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target = Path(args.target)
    metadata = target / ".applied-ai-rig"
    profile_path = metadata / "profile.json"
    manifest_path = metadata / "manifest.json"

    if args.check:
        result = check_project(target)
        for finding in result.findings:
            print(f"{finding.severity.value.upper():7} {finding.path}: {finding.message}")
        if result.errors:
            print(f"Structural check found {len(result.errors)} error(s).")
            return 1
        print(f"Structural check completed with {len(result.warnings)} warning(s).")
        return 0

    if args.modules is None and args.non_interactive and not profile_path.exists():
        parser.error("--non-interactive requires --modules on a new project")

    if args.modules is not None:
        selected = _parse_modules(parser, args.modules)
        profile = Profile(1, __version__, {}, selected, (), {})
    elif profile_path.exists():
        profile = Profile.from_json(profile_path.read_text(encoding="utf-8"))
    else:
        profile = _ask_profile()

    checksums: dict[str, str] = {}
    if manifest_path.exists():
        manifest = Manifest.from_json(manifest_path.read_text(encoding="utf-8"))
        checksums = {item.path: item.original_checksum for item in manifest.files}

    template_root = Path(__file__).resolve().parents[1] / "templates"
    plan = build_plan(target, profile, template_root, checksums)
    _print_plan(plan)
    if args.dry_run:
        return 0

    if args.non_interactive and any(
        item.status in (FileStatus.MODIFIED, FileStatus.CONFLICT) for item in plan.files
    ):
        print("Conflicts require interactive approval; no files were changed.", file=sys.stderr)
        return 3

    install_plan(
        plan,
        approve=InteractiveApprover(plan.target),
        installed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    return 0


def _parse_modules(parser: argparse.ArgumentParser, raw: str) -> tuple[str, ...]:
    if raw.strip().lower() in ("", "none"):
        return ()
    selected = tuple(dict.fromkeys(part.strip() for part in raw.split(",") if part.strip()))
    unknown = set(selected) - set(MODULE_IDS)
    if unknown:
        parser.error(f"unknown module ID: {sorted(unknown)[0]}")
    return selected


def _ask_profile() -> Profile:
    answers: dict[str, bool] = {}
    for question in QUESTIONS:
        reply = input(f"{question.prompt} [y/N] ").strip().lower()
        answers[question.id] = reply in ("y", "yes")
    reasons = recommend_modules(answers)
    selected: list[str] = []
    declined: list[str] = []
    for module_id, reason in reasons.items():
        reply = input(f"Recommend {module_id}: {reason} Install it? [Y/n] ").strip().lower()
        (declined if reply in ("n", "no") else selected).append(module_id)
    return Profile(1, __version__, answers, tuple(selected), tuple(declined), reasons)


def _print_plan(plan: InstallationPlan) -> None:
    print(f"Applied AI Rig installation plan for {plan.target}")
    for item in plan.files:
        print(f"{item.status.name:10} {item.relative_path.as_posix()}")
    for path in plan.manual_integrations:
        print(f"MANUAL     {path}: review integration with APPLIED_AI_RIG_AGENT.md")


class InteractiveApprover:
    def __init__(
        self,
        target: Path,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self.target = target
        self.input_fn = input_fn
        self.output_fn = output_fn
        self._remaining: bool | None = None

    def __call__(self, item: PlannedFile) -> bool:
        if self._remaining is not None:
            return self._remaining
        destination = self.target.joinpath(*item.relative_path.parts)
        if destination.exists():
            self.output_fn(unified_diff(item, destination))
        reply = self.input_fn(
            f"Replace {item.relative_path.as_posix()}? [y/N/a=all/s=skip all] "
        ).strip().lower()
        if reply in ("a", "all"):
            self._remaining = True
            return True
        if reply in ("s", "skip", "skip all"):
            self._remaining = False
            return False
        return reply in ("y", "yes")
