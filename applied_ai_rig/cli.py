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
from .intake import MODULE_IDS, MODULE_INFO, QUESTIONS, SETUP_PROFILES, recommend_modules
from .manifest import Manifest, Profile
from .web_setup import WebSetupCancelled, WebSetupResult, plan_payload, run_web_setup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="init.py",
        description="Install Applied AI Rig into an applied-AI project.",
    )
    parser.add_argument("target", nargs="?", default=".", help="Target project directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--check", action="store_true", help="Run structural checks on a target")
    parser.add_argument("--modules", help="Comma-separated optional module IDs")
    parser.add_argument(
        "--profile",
        choices=tuple(SETUP_PROFILES),
        help="Start from a named setup profile",
    )
    parser.add_argument("--list-modules", action="store_true", help="Describe available modules and exit")
    parser.add_argument("--explain", choices=MODULE_IDS, metavar="MODULE", help="Explain one module and exit")
    parser.add_argument("--non-interactive", action="store_true", help="Disable interactive prompts")
    parser.add_argument("--terminal", action="store_true", help="Use the terminal wizard instead of the local web interface")
    parser.add_argument("--no-browser", action="store_true", help="Start the local web interface without opening a browser")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target = Path(args.target)
    metadata = target / ".applied-ai-rig"
    profile_path = metadata / "profile.json"
    manifest_path = metadata / "manifest.json"

    if args.list_modules:
        _print_modules()
        return 0
    if args.explain:
        _print_module_detail(args.explain, print)
        return 0
    if args.modules is not None and args.profile is not None:
        parser.error("--modules and --profile cannot be used together")
    if args.terminal and args.no_browser:
        parser.error("--terminal and --no-browser cannot be used together")
    if args.non_interactive and (args.terminal or args.no_browser):
        parser.error("--terminal and --no-browser are interactive options")

    if args.check:
        result = check_project(target)
        for finding in result.findings:
            print(f"{finding.severity.value.upper():7} {finding.path}: {finding.message}")
        if result.errors:
            print(f"Structural check found {len(result.errors)} error(s).")
            return 1
        print(f"Structural check completed with {len(result.warnings)} warning(s).")
        return 0

    if args.modules is None and args.profile is None and args.non_interactive and not profile_path.exists():
        parser.error("--non-interactive requires --modules or --profile on a new project")

    checksums: dict[str, str] = {}
    if manifest_path.exists():
        manifest = Manifest.from_json(manifest_path.read_text(encoding="utf-8"))
        checksums = {item.path: item.original_checksum for item in manifest.files}
    template_root = Path(__file__).resolve().parents[1] / "templates"
    web_result: WebSetupResult | None = None

    if args.modules is not None:
        selected = _parse_modules(parser, args.modules)
        previous = _read_profile(profile_path)
        answers = previous.answers if previous else {}
        reasons = recommend_modules(answers) if answers else {}
        declined = tuple(module for module in reasons if module not in selected)
        profile = Profile(1, __version__, dict(answers), selected, declined, reasons)
    elif args.profile is not None:
        base = _profile_for_modules(SETUP_PROFILES[args.profile])
        try:
            profile = base if args.non_interactive else _select_modules(base, input, print)
        except WizardCancelled:
            print("Setup cancelled; no files were changed.")
            return 2
    elif profile_path.exists():
        previous = Profile.from_json(profile_path.read_text(encoding="utf-8"))
        _print_existing_project_summary(target, previous)
        try:
            if args.non_interactive:
                profile = previous
            elif _use_web_interface(args):
                web_result = run_web_setup(
                    target,
                    template_root,
                    checksums,
                    previous,
                    open_browser=not args.no_browser,
                )
                profile = web_result.profile
            else:
                profile = run_setup_wizard(previous)
        except WebSetupCancelled as error:
            print(str(error))
            return 2
        except OSError as error:
            if args.no_browser:
                print(f"Could not start the local web interface: {error}", file=sys.stderr)
                return 2
            print(f"Local web interface unavailable; using terminal setup: {error}")
            profile = run_setup_wizard(previous)
        except WizardCancelled:
            print("Setup cancelled; no files were changed.")
            return 2
    else:
        try:
            if _use_web_interface(args):
                web_result = run_web_setup(
                    target,
                    template_root,
                    checksums,
                    open_browser=not args.no_browser,
                )
                profile = web_result.profile
            else:
                profile = run_setup_wizard()
        except WebSetupCancelled as error:
            print(str(error))
            return 2
        except OSError as error:
            if args.no_browser:
                print(f"Could not start the local web interface: {error}", file=sys.stderr)
                return 2
            print(f"Local web interface unavailable; using terminal setup: {error}")
            profile = run_setup_wizard()
        except WizardCancelled:
            print("Setup cancelled; no files were changed.")
            return 2

    plan = build_plan(target, profile, template_root, checksums)
    if web_result is not None and plan_payload(plan)["digest"] != web_result.plan_digest:
        print("The target changed after browser confirmation; no files were changed.", file=sys.stderr)
        return 3
    _print_plan(plan)
    if args.dry_run:
        _print_diffs(plan)
        return 0

    if args.non_interactive and any(
        item.status in (FileStatus.MODIFIED, FileStatus.CONFLICT) for item in plan.files
    ):
        print("Conflicts require interactive approval; no files were changed.", file=sys.stderr)
        return 3

    if web_result is None and not args.non_interactive and _has_changes(plan):
        try:
            reply = input("Apply this complete plan? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nInstallation cancelled; no files were changed.")
            return 2
        if reply not in ("y", "yes"):
            print("Installation cancelled; no files were changed.")
            return 2

    try:
        approve: Callable[[PlannedFile], bool] = InteractiveApprover(plan.target)
        if web_result is not None:
            approve = WebApprover(web_result.approved_paths)
        install_plan(
            plan,
            approve=approve,
            installed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
    except InstallationCancelled as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


def _use_web_interface(args: argparse.Namespace) -> bool:
    if args.terminal or args.non_interactive:
        return False
    return args.no_browser or (sys.stdin.isatty() and sys.stdout.isatty())


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


class WizardCancelled(RuntimeError):
    """Raised when an interactive setup is cancelled before planning writes."""


def _profile_for_modules(selected: tuple[str, ...]) -> Profile:
    reasons = {
        module_id: "Selected by the named setup profile; review whether it applies to this project."
        for module_id in selected
    }
    return Profile(1, __version__, {}, selected, (), reasons)


def run_setup_wizard(
    previous: Profile | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> Profile:
    output_fn("Applied AI Rig setup")
    output_fn("Choose a quick profile or run the custom risk assessment. No files are written yet.")
    output_fn("  1. Minimal core")
    output_fn("  2. API or RAG application")
    output_fn("  3. Agent with tools")
    output_fn("  4. Production AI service")
    output_fn("  5. Custom assessment")
    if previous is not None:
        output_fn("  6. Keep the current project profile")

    while True:
        reply = input_fn("Select setup [1-5, q=quit]: ").strip().lower()
        if reply in ("q", "quit"):
            raise WizardCancelled()
        if reply == "6" and previous is not None:
            return _select_modules(previous, input_fn, output_fn)
        preset_names = ("minimal", "api-rag", "agent", "production")
        if reply in ("1", "2", "3", "4"):
            base = _profile_for_modules(SETUP_PROFILES[preset_names[int(reply) - 1]])
            return _select_modules(base, input_fn, output_fn)
        if reply == "5":
            return _run_custom_assessment(previous, input_fn, output_fn)
        output_fn("Enter a number shown above, or q to quit.")


def _run_custom_assessment(
    previous: Profile | None,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> Profile:
    answers: dict[str, bool] = dict(previous.answers) if previous else {}
    index = 0
    while index < len(QUESTIONS):
        question = QUESTIONS[index]
        prior = answers.get(question.id, False)
        prompt = "Y/n" if prior else "y/N"
        reply = input_fn(f"{index + 1}/{len(QUESTIONS)} {question.prompt} [{prompt}/?=why/b=back/q=quit] ").strip().lower()
        if reply in ("q", "quit"):
            raise WizardCancelled()
        if reply in ("?", "why"):
            output_fn(f"Why this matters: {question.reason}")
            continue
        if reply in ("b", "back"):
            index = max(0, index - 1)
            continue
        if reply in ("", "y", "yes", "n", "no"):
            answers[question.id] = prior if not reply else reply in ("y", "yes")
            index += 1
            continue
        output_fn("Use y, n, ?, b, or q.")

    reasons = recommend_modules(answers)
    selected = tuple(module_id for module_id in MODULE_IDS if module_id in reasons)
    base = Profile(1, __version__, answers, selected, (), reasons)
    return _select_modules(base, input_fn, output_fn)


def _select_modules(
    profile: Profile,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> Profile:
    selected = set(profile.selected_modules)
    while True:
        output_fn("Recommended modules (toggle any module before continuing):")
        for number, module_id in enumerate(MODULE_IDS, start=1):
            mark = "x" if module_id in selected else " "
            reason = profile.recommendation_reasons.get(module_id, "Not triggered by the current answers.")
            output_fn(f"  {number}. [{mark}] {module_id}: {reason}")
        reply = input_fn("Toggle numbers, ?N for details, Enter to continue, or q to quit: ").strip().lower()
        if not reply:
            ordered = tuple(module_id for module_id in MODULE_IDS if module_id in selected)
            declined = tuple(
                module_id for module_id in profile.recommendation_reasons if module_id not in selected
            )
            return Profile(
                1,
                __version__,
                profile.answers,
                ordered,
                declined,
                profile.recommendation_reasons,
            )
        if reply in ("q", "quit"):
            raise WizardCancelled()
        if reply.startswith("?") and reply[1:].isdigit():
            number = int(reply[1:])
            if 1 <= number <= len(MODULE_IDS):
                _print_module_detail(MODULE_IDS[number - 1], output_fn)
                continue
        numbers = [part.strip() for part in reply.split(",")]
        if numbers and all(part.isdigit() and 1 <= int(part) <= len(MODULE_IDS) for part in numbers):
            for part in numbers:
                module_id = MODULE_IDS[int(part) - 1]
                selected.symmetric_difference_update((module_id,))
            continue
        output_fn("Enter comma-separated module numbers, ?N, Enter, or q.")


def _print_modules() -> None:
    print("Applied AI Rig modules")
    for module_id in MODULE_IDS:
        info = MODULE_INFO[module_id]
        print(f"\n{module_id} — {info.title}")
        print(f"  Recommended when: {info.recommended_when}")
        print(f"  Generated: {', '.join(info.generated)}")


def _print_existing_project_summary(target: Path, profile: Profile) -> None:
    selected = ", ".join(profile.selected_modules) or "core only"
    print(f"Existing Applied AI Rig project: {target.resolve(strict=False)}")
    print(f"Current modules: {selected}")
    print("The assessment can keep, add, or decline modules; nothing changes before final approval.")


def _print_module_detail(module_id: str, output_fn: Callable[[str], None]) -> None:
    info = MODULE_INFO[module_id]
    output_fn(f"{info.title} ({module_id})")
    output_fn(f"Recommended when: {info.recommended_when}")
    output_fn(f"Covers: {info.covers}")
    output_fn(f"Generated: {', '.join(info.generated)}")


def _print_plan(plan: InstallationPlan) -> None:
    print(f"Applied AI Rig installation plan for {plan.target}")
    for item in plan.files:
        print(f"{item.status.name:10} {item.relative_path.as_posix()}")
    for path in plan.manual_integrations:
        print(f"MANUAL     {path}: review integration with APPLIED_AI_RIG_AGENT.md")
        print("           Suggested reference: See APPLIED_AI_RIG_AGENT.md for project AI-work guidance.")


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


class WebApprover:
    def __init__(self, approved_paths: frozenset[str]) -> None:
        self.approved_paths = approved_paths

    def __call__(self, item: PlannedFile) -> bool:
        return item.relative_path.as_posix() in self.approved_paths
