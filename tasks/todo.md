# Applied AI Rig V1 tasks

Tasks are ordered by dependency. A task is complete only when its acceptance criteria and verification step
pass. Update `docs/spec.md` before implementing any requirement or stable interface change.

## Foundation

- [x] **T01: Establish repository metadata and test command**
  - Depends on: approved specification and plan.
  - Acceptance: the repository has an MIT license, public project description, contribution entry point,
    ignore rules, and an empty `unittest` suite that exits successfully without network access.
  - Verify: `python -m unittest discover -s tests -v` and manual license/name review.
  - Files: `README.md`, `LICENSE`, `CONTRIBUTING.md`, `.gitignore`, `tests/__init__.py`.

- [x] **T02: Add the dependency-free CLI skeleton**
  - Depends on: T01.
  - Acceptance: `python init.py --help` succeeds on Python 3.10+, invalid arguments return a stable non-zero
    code, and the entry point contains no installation logic.
  - Verify: `python -m unittest tests.test_cli -v` and
    `python -m compileall -q init.py applied_ai_rig tests`.
  - Files: `init.py`, `applied_ai_rig/__init__.py`, `applied_ai_rig/cli.py`, `tests/test_cli.py`.

## Intake and persistent metadata

- [x] **T03: Define stable intake questions and module recommendations**
  - Depends on: T02.
  - Acceptance: observable answers deterministically recommend the five V1 modules with explanations;
    recommendations and user selections remain separate; all IDs match the specification.
  - Verify: `python -m unittest tests.test_intake -v`.
  - Files: `applied_ai_rig/intake.py`, `tests/test_intake.py`.

- [x] **T04: Serialize and validate project profiles**
  - Depends on: T03.
  - Acceptance: profiles preserve schema version, Rig version, answers, accepted modules, declined
    recommendations, and reasons; malformed or unknown required fields fail explicitly; round trips are
    deterministic.
  - Verify: `python -m unittest tests.test_manifest.ProfileTests -v`.
  - Files: `applied_ai_rig/manifest.py`, `tests/test_manifest.py`.

- [x] **T05: Model installation manifests and generated-file checksums**
  - Depends on: T04.
  - Acceptance: manifests serialize schema version, Rig version, timestamp, selected modules, generated
    relative paths, original SHA-256 checksums, and manual-integration status; absolute paths and identities
    are rejected.
  - Verify: `python -m unittest tests.test_manifest.ManifestTests -v`.
  - Files: `applied_ai_rig/manifest.py`, `tests/test_manifest.py`.

## Pure rendering and planning

- [x] **T06: Implement the bounded template renderer and inventory**
  - Depends on: T05.
  - Acceptance: the renderer supports only documented placeholders, rejects unresolved values, produces
    UTF-8 text with `\n`, and rejects destinations outside the target; template inventory is deterministic.
  - Verify: `python -m unittest tests.test_installer.RendererTests -v`.
  - Files: `applied_ai_rig/installer.py`, `tests/test_installer.py`, `templates/core/inventory.json`.

- [x] **T07: Add the first half of the core templates**
  - Depends on: T06.
  - Acceptance: generated reading order, operating principles, and decisions use provider-neutral language,
    stable IDs, decision status, supersession, consequences, and revision thresholds.
  - Verify: focused template-rendering assertions in `tests.test_installer.CoreTemplateTests`.
  - Files: `templates/core/README.md.tmpl`, `templates/core/OPERATING_PRINCIPLES.md.tmpl`,
    `templates/core/DECISIONS.md.tmpl`, `tests/test_installer.py`.

- [x] **T08: Complete core evidence and companion-agent templates**
  - Depends on: T07.
  - Acceptance: claim records distinguish measured, estimated, and unknown values; companion guidance points
    to canonical generated files; no template requires a specific agent, provider, framework, or workflow.
  - Verify: focused assertions in `tests.test_installer.CoreTemplateTests` plus forbidden-term scan.
  - Files: `templates/core/EVIDENCE.md.tmpl`, `templates/core/APPLIED_AI_RIG_AGENT.md.tmpl`,
    `tests/test_installer.py`.

- [x] **T09: Classify target files and brownfield integrations without writes**
  - Depends on: T08.
  - Acceptance: planning distinguishes new, unchanged, modified-generated, untracked-conflict, and manual
    integration states; common agent, ADR, security, and experiment artifacts are reported but not parsed or
    modified.
  - Verify: `python -m unittest tests.test_installer.ClassificationTests -v`.
  - Files: `applied_ai_rig/installer.py`, `tests/test_installer.py`, `tests/fixtures/existing/AGENTS.md`.

- [x] **T10: Expose deterministic dry-run and non-interactive planning**
  - Depends on: T09.
  - Acceptance: `--dry-run` shows target, core, selected modules, statuses, recommendations, and manual
    integrations while writing nothing; non-interactive mode rejects missing selections or ambiguous state.
  - Verify: `python -m unittest tests.test_cli.DryRunTests -v` and compare a temporary target before/after.
  - Files: `applied_ai_rig/cli.py`, `applied_ai_rig/installer.py`, `tests/test_cli.py`.

## Safe installation and re-runs

- [x] **T11: Install an approved plan atomically**
  - Depends on: T10.
  - Acceptance: fresh installation writes core, profile, and final manifest through a target-local staging
    area; cancellation or simulated failure leaves no partial destination or staging artifact.
  - Verify: `python -m unittest tests.test_installer.AtomicInstallTests -v`.
  - Files: `applied_ai_rig/installer.py`, `applied_ai_rig/manifest.py`, `tests/test_installer.py`.

- [x] **T12: Implement safe re-runs, diffs, and interactive conflicts**
  - Depends on: T11.
  - Acceptance: unchanged re-runs produce no content changes; modified generated text produces a unified
    diff; interactive replacement requires explicit approval; apply-to-all is explicit; binary or undecodable
    conflicts are never displayed as text.
  - Verify: `python -m unittest tests.test_installer.RerunTests -v`.
  - Files: `applied_ai_rig/installer.py`, `applied_ai_rig/cli.py`, `tests/test_installer.py`,
    `tests/test_cli.py`.

- [x] **T13: Make non-interactive conflicts fail safely**
  - Depends on: T12.
  - Acceptance: non-interactive conflicts return a documented non-zero code, identify affected paths, offer
    no force-overwrite flag, and leave every target file unchanged.
  - Verify: `python -m unittest tests.test_cli.NonInteractiveConflictTests -v`.
  - Files: `applied_ai_rig/cli.py`, `applied_ai_rig/installer.py`, `tests/test_cli.py`.

## Optional modules

- [x] **T14: Add the model API and cost module**
  - Depends on: T13.
  - Acceptance: the module generates credential-boundary guidance, model/provider inventory, and usage-cost
    records covering calls, tokens, retries, evaluation, and unknown prices without secrets or endpoints;
    external billing and tracing systems can be linked.
  - Verify: `python -m unittest tests.test_modules.ModelApiModuleTests -v`.
  - Files: `templates/modules/model-api/MODEL_API.md.tmpl`,
    `templates/modules/model-api/api_usage.csv.tmpl`, `tests/test_modules.py`.

- [x] **T15: Add the supplied and sensitive data module**
  - Depends on: T13.
  - Acceptance: the module covers provenance, classification, minimization, authorized destinations,
    derivative sensitivity, retention, deletion, and incident response without claiming anonymization or
    compliance.
  - Verify: `python -m unittest tests.test_modules.DataModuleTests -v`.
  - Files: `templates/modules/data/DATA_HANDLING.md.tmpl`,
    `templates/modules/data/data_register.csv.tmpl`, `tests/test_modules.py`.

- [x] **T16: Add the evaluation and experiment module**
  - Depends on: T14 and T15.
  - Acceptance: stable run IDs link hypothesis, code, dataset, model/config, metrics, cost, and evidence;
    records can point to external experiment systems and explicitly avoid duplicating detailed traces.
  - Verify: `python -m unittest tests.test_modules.EvaluationModuleTests -v`.
  - Files: `templates/modules/evaluation/EVALUATION.md.tmpl`,
    `templates/modules/evaluation/experiments.csv.tmpl`, `tests/test_modules.py`.

- [x] **T17: Add the agentic runtime module**
  - Depends on: T13.
  - Acceptance: the module records side effects, minimum tool permissions, approval boundaries, bounded
    consumption, argument validation, and escalation while clearly stating that it is not runtime policy
    enforcement.
  - Verify: `python -m unittest tests.test_modules.AgenticRuntimeModuleTests -v`.
  - Files: `templates/modules/agentic-runtime/AGENTIC_RUNTIME.md.tmpl`,
    `templates/modules/agentic-runtime/action_register.csv.tmpl`, `tests/test_modules.py`.

- [x] **T18: Add the production operations module**
  - Depends on: T13.
  - Acceptance: the module covers ownership, health, observability references, operating limits, releases,
    rollback, incidents, and evidence links without generating deployment infrastructure.
  - Verify: `python -m unittest tests.test_modules.OperationsModuleTests -v`.
  - Files: `templates/modules/operations/OPERATIONS.md.tmpl`,
    `templates/modules/operations/incident_register.csv.tmpl`, `tests/test_modules.py`.

- [x] **T19: Compose selected modules into reading order and agent guidance**
  - Depends on: T14 through T18.
  - Acceptance: all-modules installation has valid links and stable headers; core-only installation has no
    optional files or references; selected subsets contain exactly their chosen artifacts.
  - Verify: `python -m unittest tests.test_modules.ModuleCompositionTests -v`.
  - Files: `applied_ai_rig/installer.py`, `templates/core/README.md.tmpl`,
    `templates/core/APPLIED_AI_RIG_AGENT.md.tmpl`, `tests/test_modules.py`.

## Structural checker

- [x] **T20: Validate profile, manifest, paths, and checksums read-only**
  - Depends on: T19.
  - Acceptance: `--check` validates schemas, selected-file presence, manifest paths, and checksum state;
    findings are actionable and check mode performs no writes.
  - Verify: `python -m unittest tests.test_checker.ManifestCheckTests -v`.
  - Files: `applied_ai_rig/checker.py`, `applied_ai_rig/cli.py`, `tests/test_checker.py`.

- [x] **T21: Validate links, CSV headers, placeholders, and agent references**
  - Depends on: T20.
  - Acceptance: check mode detects each specified structural defect in isolation; wording never claims the
    target is compliant, secure, safe, or production-ready.
  - Verify: `python -m unittest tests.test_checker.ContentCheckTests -v`.
  - Files: `applied_ai_rig/checker.py`, `tests/test_checker.py`,
    `tests/fixtures/invalid/README.md`, `tests/fixtures/invalid/records.csv`.

## Public usability and release evidence

- [x] **T22: Document modules, triggers, safe updates, and manual removal**
  - Depends on: T19 and T21.
  - Acceptance: users can understand why each module exists, re-run safely, interpret the manifest, and
    remove generated files manually without deleting user-modified work.
  - Verify: commands and paths in documentation pass a clean temporary-directory walkthrough.
  - Files: `README.md`, `docs/modules.md`, `CONTRIBUTING.md`.

- [x] **T23: Document coexistence and explicit non-goals**
  - Depends on: T22.
  - Acceptance: documentation explains coexistence with spec workflows, agent harnesses, experiment tools,
    billing systems, and runtime policy engines; it does not imply endorsement, dependency, or replacement.
  - Verify: link review plus repository search for forbidden compliance and platform claims.
  - Files: `docs/coexistence.md`, `README.md`.

- [x] **T24: Complete cross-platform and clean-room verification**
  - Depends on: T23.
  - Acceptance: full tests pass; targets with spaces and non-ASCII names work; no generated file contains an
    absolute path, personal context, unused module, unresolved placeholder, or context from the private
    project that originally motivated the template.
  - Verify: full suite, compile check, core-only and all-modules temporary installations, and repository-wide
    forbidden-string scan.
  - Files: `tests/test_cli.py`, `tests/test_installer.py`, `tests/test_checker.py`, `tests/test_modules.py`.

- [x] **T25: Map every V1 success criterion to release evidence**
  - Depends on: T24.
  - Acceptance: a concise report maps all 14 success criteria in `docs/spec.md` to passing tests or a named
    manual review; deferred work is explicit and remains outside V1.
  - Verify: independent comparison of the report, specification, and final test output.
  - Files: `docs/verification.md`, `tasks/todo.md`.
