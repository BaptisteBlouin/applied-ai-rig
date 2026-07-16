import argparse
import shlex
import sys
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable

from . import __version__
from .checker import check_project
from .installer import (
    FileStatus,
    InstallationPlan,
    InstallationCancelled,
    PlannedFile,
    PreservationError,
    build_plan,
    install_plan,
    preserve_conflicts,
    unified_diff,
)
from .intake import MODULE_IDS, MODULE_INFO, QUESTIONS, SETUP_PROFILES, recommend_modules
from .manifest import Manifest, Profile
from .records import (
    RecordChange,
    RecordError,
    apply_record_change,
    project_status,
    propose_decision,
    propose_evidence,
    propose_experiment,
)
from .web_setup import WebSetupCancelled, WebSetupResult, plan_payload, run_web_setup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="init.py",
        description="Install Applied AI Rig into an applied-AI project.",
        epilog="Daily workflow: applied-ai-rig status [target] or applied-ai-rig add --help",
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
    parser.add_argument(
        "--preserve-conflicts",
        action="store_true",
        help="Preserve untracked Markdown conflicts as adjacent .project.md sidecars",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    if _is_workflow_command(raw_args):
        return _workflow_main(raw_args)
    parser = build_parser()
    args = parser.parse_args(raw_args)
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
    if args.preserve_conflicts and not (args.non_interactive or args.terminal):
        parser.error("--preserve-conflicts requires --non-interactive or --terminal")

    if args.check:
        result = check_project(target)
        for finding in result.findings:
            print(f"{finding.severity.value.upper():7} {finding.path}: {finding.message}")
        if result.errors:
            print(f"Structural check found {len(result.errors)} error(s).")
            return 1
        print(
            f"Structural check completed with {len(result.warnings)} warning(s) "
            f"and {len(result.infos)} informational finding(s)."
        )
        return 0

    if args.modules is None and args.profile is None and args.non_interactive and not profile_path.exists():
        parser.error("--non-interactive requires --modules or --profile on a new project")

    checksums: dict[str, str] = {}
    known_manual_integrations: tuple[str, ...] = ()
    if manifest_path.exists():
        manifest = Manifest.from_json(manifest_path.read_text(encoding="utf-8"))
        checksums = {item.path: item.original_checksum for item in manifest.files}
        known_manual_integrations = manifest.manual_integrations
    template_root = Path(__file__).resolve().parent / "templates"
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
                    known_manual_integrations=known_manual_integrations,
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
                    known_manual_integrations=known_manual_integrations,
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

    plan = build_plan(
        target,
        profile,
        template_root,
        checksums,
        known_manual_integrations,
    )
    if args.preserve_conflicts:
        try:
            plan = preserve_conflicts(plan)
        except (OSError, PreservationError) as error:
            print(f"Could not preserve conflicts: {error}; no files were changed.", file=sys.stderr)
            return 3
    if web_result is not None and plan_payload(plan)["digest"] != web_result.plan_digest:
        print("The target changed after browser confirmation; no files were changed.", file=sys.stderr)
        return 3
    _print_plan(plan)
    sys.stdout.flush()
    if args.dry_run:
        _print_diffs(plan)
        return 0

    preserved_paths = {item.original_path for item in plan.preservations}
    if args.non_interactive and any(
        item.status is FileStatus.MODIFIED
        or (item.status is FileStatus.CONFLICT and item.relative_path not in preserved_paths)
        for item in plan.files
    ):
        print(
            "Conflicts require a safe resolution; no files were changed. "
            "Re-run with --preserve-conflicts to keep untracked Markdown files as sidecars, "
            "or use --terminal to review replacements individually.",
            file=sys.stderr,
        )
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
        elif args.non_interactive and plan.preservations:
            approve = PreservedConflictApprover(preserved_paths)
        install_plan(
            plan,
            approve=approve,
            installed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
    except InstallationCancelled as error:
        print(str(error), file=sys.stderr)
        return 2
    _print_installation_next_steps(target, plan)
    return 0


def _is_workflow_command(raw_args: Sequence[str]) -> bool:
    if not raw_args:
        return False
    if raw_args[0] == "add":
        return len(raw_args) > 1 and raw_args[1] in {
            "decision",
            "evidence",
            "experiment",
            "--help",
            "-h",
        }
    if raw_args[0] != "status":
        return False
    legacy_options = {
        "--check",
        "--modules",
        "--profile",
        "--list-modules",
        "--explain",
        "--non-interactive",
        "--terminal",
        "--no-browser",
        "--dry-run",
        "--preserve-conflicts",
    }
    if any(argument in legacy_options for argument in raw_args[1:]):
        return False
    if len(raw_args) > 1:
        return True
    return True


def _workflow_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="applied-ai-rig",
        description="Inspect an installed Rig or safely add a decision-relevant record.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status", help="Show structural health, record counts, and the next action")
    status.add_argument("target", nargs="?", default=".")

    add = commands.add_parser("add", help="Preview or append a record")
    record_types = add.add_subparsers(dest="record_type", required=True)

    decision = record_types.add_parser("decision", help="Add a proposed decision skeleton")
    _add_record_target_and_write_mode(decision)
    decision.add_argument("--id", required=True, dest="record_id")
    decision.add_argument("--title", required=True)

    evidence = record_types.add_parser("evidence", help="Add evidence linked to a decision")
    _add_record_target_and_write_mode(evidence)
    evidence.add_argument("--id", required=True, dest="record_id")
    evidence.add_argument("--claim", required=True)
    evidence.add_argument("--decision", required=True, dest="decision_id")
    evidence.add_argument(
        "--status",
        choices=("measured", "estimated", "unknown"),
        default="unknown",
    )

    experiment = record_types.add_parser("experiment", help="Add a row to experiments.csv")
    _add_record_target_and_write_mode(experiment)
    experiment.add_argument("--run-id", required=True)
    experiment.add_argument("--decision", required=True, dest="decision_id")
    experiment.add_argument("--model", required=True)
    experiment.add_argument("--metric", required=True)
    experiment.add_argument("--value", required=True)
    return parser


def _add_record_target_and_write_mode(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("target", nargs="?", default=".")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--yes", action="store_true", help="Apply the previewed append")
    mode.add_argument("--dry-run", action="store_true", help="Preview only; this is the default")


def _workflow_main(raw_args: Sequence[str]) -> int:
    parser = _workflow_parser()
    args = parser.parse_args(raw_args)
    try:
        if args.command == "status":
            status = project_status(Path(args.target))
            if status.selected_modules is None:
                modules = "unknown (profile and manifest are unreadable)"
            else:
                modules = ", ".join(status.selected_modules) or "core only"
            health = "healthy" if not status.check.errors else "needs attention"
            print(f"Applied AI Rig status for {status.target}")
            print(f"Modules: {modules}")
            print(
                f"Structural health: {health} "
                f"({len(status.check.errors)} error(s), {len(status.check.warnings)} warning(s), "
                f"{len(status.check.infos)} info)"
            )
            for finding in status.check.findings:
                print(
                    f"  {finding.severity.value.upper()} {finding.path}: "
                    f"{finding.message}"
                )
            print("Records:")
            for name, count in status.counts.items():
                displayed_count = "unknown" if count is None else str(count)
                print(f"  {name}: {displayed_count}")
            print("Next:")
            if status.next_command is None:
                print(f"  {status.next_instruction}")
            else:
                print(f"  {_format_workflow_command(status.next_command)}")
            return 1 if status.check.errors else 0

        change = _propose_record(args)
        if not args.yes:
            print(f"Preview: append to {change.relative_path}\n")
            print(change.addition, end="")
            print("\nNo files changed. Re-run the command with --yes to apply this append.")
            return 0
        apply_record_change(change)
        print(f"Added {change.record_id} to {change.relative_path}.")
        if args.record_type == "decision":
            print("Next:")
            print(
                "  Complete Context, Options, Decision, Consequences, and Revision threshold "
                f"in {change.relative_path}."
            )
            print(
                "  Preview linked evidence with "
                + _format_workflow_command(
                    (
                        "add",
                        "evidence",
                        str(change.target),
                        "--id",
                        "EVD-YYYYMMDD-short-name",
                        "--claim",
                        "Describe the supported claim",
                        "--decision",
                        change.record_id,
                    )
                )
            )
        return 0
    except RecordError as error:
        print(str(error), file=sys.stderr)
        return 2


def _propose_record(args: argparse.Namespace) -> RecordChange:
    target = Path(args.target)
    if args.record_type == "decision":
        return propose_decision(target, args.record_id, args.title)
    if args.record_type == "evidence":
        return propose_evidence(
            target,
            args.record_id,
            args.claim,
            args.decision_id,
            args.status,
        )
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return propose_experiment(
        target,
        args.run_id,
        args.decision_id,
        args.model,
        args.metric,
        args.value,
        timestamp,
    )


def _command_prefix() -> tuple[str, ...]:
    executable = Path(sys.argv[0])
    if executable.name == "init.py":
        return (sys.executable, str(executable.resolve(strict=False)))
    return (executable.name or "applied-ai-rig",)


def _format_workflow_command(command: Sequence[str]) -> str:
    return shlex.join((*_command_prefix(), *command))


def _print_installation_next_steps(target: Path, plan: InstallationPlan) -> None:
    resolved = str(target.resolve(strict=False))
    if plan.preservations:
        print("\nPreserved project content:")
        for item in plan.preservations:
            print(
                f"  {item.original_path.as_posix()} -> {item.preserved_path.as_posix()} "
                f"(sha256 {item.checksum})"
            )
        print("  Review and link or merge these sidecars; the originals were not discarded.")
    print("\nNext:")
    print(f"  {_format_workflow_command(('status', resolved))}")
    print(
        "  "
        + _format_workflow_command(
            (
                "add",
                "decision",
                resolved,
                "--id",
                "DEC-YYYYMMDD-short-name",
                "--title",
                "Describe the choice",
            )
        )
    )


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
    selected = ", ".join(plan.profile.selected_modules) or "core only"
    print(f"Selected modules: {selected}")
    print("First-use focus: decision and evidence; other generated records are available when their risk applies.")
    for preservation in plan.preservations:
        print(
            f"PRESERVE   {preservation.original_path.as_posix()} -> "
            f"{preservation.preserved_path.as_posix()}"
        )
    for planned_file in plan.files:
        print(
            f"{planned_file.status.name:10} "
            f"{planned_file.relative_path.as_posix()}"
        )
    preserved = {
        preservation.preserved_path.as_posix()
        for preservation in plan.preservations
    }
    for path in plan.manual_integrations:
        if path in preserved or path.endswith(".project.md"):
            print(f"MANUAL     {path}: review preserved content and link or merge it.")
        else:
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
            f"Replace {item.relative_path.as_posix()}? [y/N/a=replace all/c=cancel] "
        ).strip().lower()
        if reply in ("a", "all"):
            self._remaining = True
            return True
        if reply in ("c", "cancel", "s", "skip", "skip all"):
            self._remaining = False
            return False
        return reply in ("y", "yes")


class PreservedConflictApprover:
    def __init__(self, preserved_paths: set[PurePosixPath]) -> None:
        self.preserved_paths = frozenset(preserved_paths)

    def __call__(self, item: PlannedFile) -> bool:
        return item.relative_path in self.preserved_paths


class WebApprover:
    def __init__(self, approved_paths: frozenset[str]) -> None:
        self.approved_paths = approved_paths

    def __call__(self, item: PlannedFile) -> bool:
        return item.relative_path.as_posix() in self.approved_paths
