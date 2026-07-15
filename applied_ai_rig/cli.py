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
    InstallationCancelled,
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
        previous = _read_profile(profile_path)
        answers = previous.answers if previous else {}
        reasons = recommend_modules(answers) if answers else {}
        declined = tuple(module for module in reasons if module not in selected)
        profile = Profile(1, __version__, dict(answers), selected, declined, reasons)
    elif profile_path.exists():
        previous = Profile.from_json(profile_path.read_text(encoding="utf-8"))
        profile = previous if args.non_interactive else _ask_profile(previous)
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
        _print_diffs(plan)
        return 0

    if args.non_interactive and any(
        item.status in (FileStatus.MODIFIED, FileStatus.CONFLICT) for item in plan.files
    ):
        print("Conflicts require interactive approval; no files were changed.", file=sys.stderr)
        return 3

    if not args.non_interactive and _has_changes(plan):
        try:
            reply = input("Apply this complete plan? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nInstallation cancelled; no files were changed.")
            return 2
        if reply not in ("y", "yes"):
            print("Installation cancelled; no files were changed.")
            return 2

    try:
        install_plan(
            plan,
            approve=InteractiveApprover(plan.target),
            installed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
    except InstallationCancelled as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


def _parse_modules(parser: argparse.ArgumentParser, raw: str) -> tuple[str, ...]:
    if raw.strip().lower() in ("", "none"):
        return ()
    selected = tuple(dict.fromkeys(part.strip() for part in raw.split(",") if part.strip()))
    unknown = set(selected) - set(MODULE_IDS)
    if unknown:
        parser.error(f"unknown module ID: {sorted(unknown)[0]}")
    return selected


def _read_profile(path: Path) -> Profile | None:
    if not path.exists():
        return None
    return Profile.from_json(path.read_text(encoding="utf-8"))


def _ask_profile(previous: Profile | None = None) -> Profile:
    answers: dict[str, bool] = {}
    for question in QUESTIONS:
        prior = previous.answers.get(question.id, False) if previous else False
        prompt = "[Y/n]" if prior else "[y/N]"
        reply = input(f"{question.prompt} {prompt} ").strip().lower()
        answers[question.id] = prior if not reply else reply in ("y", "yes")
    reasons = recommend_modules(answers)
    selected: list[str] = []
    declined: list[str] = []
    for module_id, reason in reasons.items():
        prior_selected = previous is not None and module_id in previous.selected_modules
        prompt = "[Y/n]" if prior_selected or previous is None else "[y/N]"
        reply = input(f"Recommend {module_id}: {reason} Install it? {prompt} ").strip().lower()
        accepted = prior_selected if not reply and previous else reply not in ("n", "no")
        (selected if accepted else declined).append(module_id)
    return Profile(1, __version__, answers, tuple(selected), tuple(declined), reasons)


def _print_plan(plan: InstallationPlan) -> None:
    print(f"Applied AI Rig installation plan for {plan.target}")
    for item in plan.files:
        print(f"{item.status.name:10} {item.relative_path.as_posix()}")
    for path in plan.manual_integrations:
        print(f"MANUAL     {path}: review integration with APPLIED_AI_RIG_AGENT.md")
        print(f"           Suggested reference: See APPLIED_AI_RIG_AGENT.md for project AI-work guidance.")


def _has_changes(plan: InstallationPlan) -> bool:
    return any(item.status is not FileStatus.UNCHANGED for item in plan.files)


def _print_diffs(plan: InstallationPlan) -> None:
    for item in plan.files:
        if item.status not in (FileStatus.MODIFIED, FileStatus.CONFLICT):
            continue
        destination = plan.target.joinpath(*item.relative_path.parts)
        print(unified_diff(item, destination))


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
