# Applied AI Rig V1 verification

Verification date: 2026-07-16.

The local verification used Python 3.12 on Linux. The implementation targets Python 3.10 or later and uses
only the standard library. GitHub Actions also runs the suite on Linux, macOS, and Windows with the oldest
and newest supported Python versions.

## Automated commands

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q init.py applied_ai_rig tests
```

Result: 74 tests passed. The standard-library compilation check also completed successfully.

The suite includes loopback HTTP integration tests for profile validation, real-plan rendering, diff
generation, stale-plan rejection, exhaustive conflict approval, Host and Origin validation, request-size
limits, nonce-based CSP, and successful confirmation.
Browser-launch failure is also covered: Linux launcher output is suppressed, failure is reported as a
single actionable line, and the loopback URL remains available for manual opening.
WSL2 is detected explicitly and uses the Windows URL handler through `cmd.exe /c start` before trying
Linux launchers. A real WSL2 session opened without emitting the manual-browser fallback.

## Clean-room walkthrough

The following flow completed successfully against a fresh temporary directory:

```bash
python3 init.py /tmp/applied-ai-rig-check \
  --modules model-api,data,evaluation,agentic-runtime,operations \
  --non-interactive
python3 init.py --check /tmp/applied-ai-rig-check
python3 init.py /tmp/applied-ai-rig-check \
  --modules model-api,data,evaluation,agentic-runtime,operations \
  --non-interactive
```

The first command generated core plus all selected modules. The structural check completed with zero errors
and zero warnings. The re-run classified every generated file as unchanged. A subsequent all-modules
clean-room run generated the conditional `REGISTER_GUIDANCE.md` alongside the module registers and also
completed structural checking with zero warnings.

## Local web walkthrough

A real no-browser session was started against a fresh target:

```bash
python3 init.py /tmp/applied-ai-rig-web-e2e --no-browser
```

The printed loopback URL served the canonical profiles, questions, and module descriptions. A core-only
profile produced a real eight-file plan, browser confirmation returned a matching plan fingerprint, the
CLI installed the plan without a second prompt, and `python3 init.py --check` completed with zero warnings.
The server stopped automatically after confirmation.

## Success criteria evidence

| Criterion | Evidence |
|---|---|
| 1. First installation in under five minutes | README quick start plus clean temporary-directory walkthrough completed well below the limit; interactive decisions remain user-paced |
| 2. Complete read-only dry-run | `CliSmokeTests.test_core_only_dry_run_lists_plan_and_writes_nothing` |
| 3. Idempotent unchanged re-run | `RerunTests.test_unchanged_rerun_has_only_unchanged_files` and clean-room walkthrough |
| 4. No silent conflict overwrite | `RerunTests.test_user_modified_generated_file_is_not_replaced_without_approval` and interactive approval tests |
| 5. Non-interactive conflicts fail without writes | `CliSmokeTests.test_non_interactive_conflict_changes_nothing` |
| 6. Versioned checksum manifest | `AtomicInstallTests.test_fresh_install_writes_files_and_checksum_manifest` and manifest unit tests |
| 7. Explained risk recommendations | `IntakeTests.test_each_risk_answer_recommends_expected_module_with_reason` |
| 8. Core-only means core-only | `ModuleCompositionTests.test_core_only_has_no_optional_module_paths_or_links` |
| 9. Structural defect detection | Checker tests for missing files, bad links, all generated CSV headers, required record headings, placeholders, schemas, and modified files |
| 10. Canonical project files remain untouched | `ClassificationTests.test_existing_agent_file_becomes_manual_integration` and conflict policy |
| 11. Stable evidence chain | Core decision/evidence tests and `EvaluationModuleTests` |
| 12. Dependency-free offline suite | Standard-library imports, full `unittest` suite, and compile check |
| 13. Clean generated output | Module-selection tests, path validation, placeholder checks, and private-context scan |
| 14. Coexistence guidance | `docs/coexistence.md` documents spec, agent, experiment, billing, and policy-tool boundaries |

## Safety-specific evidence

- Atomic failure restores existing files and removes newly written files.
- Rollback never removes unrelated empty project directories.
- Absolute POSIX paths, absolute Windows paths, and parent traversal are rejected in manifests.
- Escaping template destinations are rejected before writes.
- Existing generated modifications produce warnings in structural checks, not false claims of validity.
- Structural output avoids claims of compliance, certification, or production readiness.
- Core workflow tests require before/during/delivery guidance, worklog continuity, and residual-risk handoff.
- Module tests require the risk-specific lifecycle controls and registers documented by each selected module.
- Register tests require conditional shared guidance for modular projects and verify embedded/external
  modes, decision-relevant row grain, scale and concurrency triggers, sensitive-content boundaries, and
  explicit treatment of `api_usage.csv` and `experiments.csv`.
- CLI tests cover module discovery, detailed explanations, named profiles, contextual question help,
  backward navigation, and explicit module toggling.
- Local web tests require loopback-only binding, an unguessable session path, strict Host and Origin
  validation, bounded JSON requests, nonce-based content security policy, allowlisted profile fields,
  current-plan fingerprints, and approval of every modified or conflicting path.
- The production web asset is self-contained, uses no remote resource, and does not construct HTML from
  target-project data.

## Publication follow-up

- Create release tags and changelog policy after the first public release decision.

This does not change V1 behavior and should follow the first public release decision.
