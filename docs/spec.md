# Spec: Applied AI Rig V1

## Objective

Applied AI Rig is an open-source GitHub Template that installs a lightweight, modular engineering record
into applied-AI application projects.

It helps individual developers and teams preserve enough durable evidence to understand, review, explain,
and operate an AI-enabled application without requiring a governance platform or imposing an application
stack.

The primary user clones or creates a repository from the template, runs a dependency-free Python
initializer, answers observable project-risk questions, previews the proposed files, and installs a small
core plus relevant optional modules in under five minutes.

The generated harness is useful to humans and coding agents. It remains fully functional after the
initializer repository is removed.

### Positioning

> Applied AI Rig installs a lightweight, modular engineering record for the models, data, experiments,
> costs, and decisions behind an AI-enabled application.

Applied AI Rig complements specification workflows, coding-agent harnesses, observability platforms, and
runtime policy engines. It does not replace them.

### Intended projects

The V1 targets applied-AI applications broadly. Examples include agents, recommendation systems, RAG,
document processing, classification, extraction, multimodal applications, and applications consuming or
serving models. These examples do not restrict the supported application types.

### Acceptance scenarios

1. A developer starting a new applied-AI project installs the core and recommended modules interactively in
   under five minutes.
2. A developer adds the harness to an existing repository without overwriting or silently merging existing
   instructions or governance files.
3. A CI job runs the initializer non-interactively and checks the generated harness structure.
4. A team links an experiment tracked in Langfuse, MLflow, Weights & Biases, or another system without
   duplicating runtime traces.
5. A small project declines every optional module and receives only the useful core.

## Product principles

1. **Evidence over ceremony.** Every artifact must help explain a decision, claim, risk, or operating state.
2. **Risk-triggered modules.** Ask observable questions and explain why a module is recommended.
3. **Conservative installation.** Preview changes and never overwrite or merge silently.
4. **Provider and stack neutrality.** Do not impose a model, framework, vendor, source tree, or deployment
   platform.
5. **Interop over duplication.** Link to external systems when they already own detailed telemetry or
   records.
6. **No compliance theater.** Structural checks and engineering records must not be described as proof of
   security, safety, or regulatory compliance.
7. **Dependency-free output.** Generated projects do not depend on the initializer at runtime.

## Tech stack

- Python 3.10 or later.
- Python standard library only for the initializer and checker.
- `unittest` for automated tests.
- Markdown, JSON, and CSV for generated artifacts.
- MIT license.
- English-only source, documentation, prompts, and generated content.

The project has no external network access, telemetry, package installation, or remote module catalog. Its
interactive setup may use a temporary loopback-only HTTP server implemented with the standard library.

CSV registers are a portable storage adapter for decision-relevant records, not runtime event stores. A
register may operate as an embedded system of record or as a safe index into an external canonical system.
Every register defines one-row grain, ownership, stable IDs, controlled and unknown values, prohibited
content, reconciliation, and externalization criteria. High volume, concurrent writers, advanced queries,
row-level access, retention enforcement, or transactional updates trigger externalization rather than
growth of versioned event logs.

## Commands

### Interactive installation

```bash
python init.py /path/to/project
```

The target defaults to the current directory when omitted.

When both standard input and output are interactive terminals, this command opens the local web wizard.
The server binds to `127.0.0.1` on an ephemeral port, uses an unguessable session path, loads no remote
resource, and stops after confirmation or cancellation. `--terminal` selects the text wizard explicitly;
`--no-browser` starts the local server and prints its URL without opening a browser.

### Preview without writing

```bash
python init.py /path/to/project --dry-run
```

### Explicit module selection

```bash
python init.py /path/to/project --modules model-api,data,evaluation --non-interactive
```

`--non-interactive` requires explicit module selection or a readable existing project profile. It exits
non-zero rather than guessing when required information is missing.

### Guided discovery

```bash
python init.py --list-modules
python init.py --explain agentic-runtime
python init.py /path/to/project --profile api-rag
```

Interactive setup provides `minimal`, `api-rag`, `agent`, and `production` starting profiles plus a custom
assessment. Quick profiles and custom assessment are alternative routes. Contextual detail views explain
profiles, questions, modules, artifacts, and non-goals. A final module screen shows all modules,
recommendation reasons, generated artifacts, and explicit toggles before the real file plan is built.
Existing profiles may be retained without discarding their recorded answers.

The browser receives no authority over filesystem paths. Python validates an allowlisted profile payload,
rebuilds the plan, returns statuses and text diffs, and fingerprints the complete preview. Confirmation is
accepted only for the current fingerprint and only when every modified or conflicting file is explicitly
approved. Python rebuilds the plan again before invoking the existing atomic installer.

`--modules` remains the exact low-level selection interface for scripts. `--profile` is mutually exclusive
with `--modules` and can be combined with `--non-interactive`.

### Structural validation

```bash
python init.py --check /path/to/project
```

The check verifies selected artifacts, manifest consistency, internal links, CSV headers, unresolved
template placeholders, and references from generated agent guidance. It does not claim that the project is
secure, compliant, production-ready, or technically correct.

### Tests

```bash
python -m unittest discover -s tests -v
```

### Syntax check

```bash
python -m compileall -q init.py applied_ai_rig tests
```

No formatter or linter dependency is required in V1. Source follows the code conventions below and is
reviewed through tests and standard-library compilation.

## Repository structure

```text
harnais-ia/
├── init.py                         # Dependency-free entry point
├── applied_ai_rig/
│   ├── __init__.py
│   ├── cli.py                      # Argument parsing and interaction
│   ├── intake.py                   # Observable questions and module recommendations
│   ├── installer.py                # Planning, rendering, conflict handling, and writes
│   ├── manifest.py                 # Profile, checksums, and installed-file metadata
│   ├── checker.py                  # Structural validation only
│   ├── web_setup.py                # Temporary loopback-only setup interface
│   ├── web/                        # Self-contained offline web assets
│   └── templates/
│       ├── core/
│       ├── shared/
│       └── modules/
│           ├── model-api/
│           ├── data/
│           ├── evaluation/
│           ├── agentic-runtime/
│           └── operations/
├── tests/
│   ├── fixtures/
│   ├── test_cli.py
│   ├── test_intake.py
│   ├── test_installer.py
│   ├── test_manifest.py
│   ├── test_modules.py
│   └── test_checker.py
├── docs/
│   ├── spec.md
│   ├── modules.md
│   ├── coexistence.md
│   └── research/
│       └── landscape.md
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

The repository itself is suitable for GitHub Template use. Generated projects receive rendered artifacts,
not the initializer source or unused modules.

## Generated project structure

```text
target-project/
├── .applied-ai-rig/
│   ├── profile.json                # Intake answers and selected modules
│   └── manifest.json               # Rig version, generated files, and original checksums
├── docs/
│   └── applied-ai-rig/
│       ├── README.md               # Reading order and module inventory
│       ├── OPERATING_PRINCIPLES.md # Concise core for humans and agents
│       ├── DECISIONS.md            # Stable decision IDs and supersession
│       ├── EVIDENCE.md             # Claim-to-evidence index
│       ├── WORKLOG.md              # Chronological facts, attempts, and handoff state
│       ├── DELIVERY_CHECKLIST.md    # Evidence-backed delivery review
│       └── modules/                # Only selected module artifacts
└── APPLIED_AI_RIG_AGENT.md         # Companion agent instructions
```

If no `AGENTS.md` exists, the initializer may offer to create a minimal one that points to
`APPLIED_AI_RIG_AGENT.md`. If an agent instruction file already exists, the initializer never edits or
merges it automatically. It prints a proposed snippet for human review.

The harness does not impose an application source directory, test framework, model provider, or data
layout. Optional module records may link to existing project locations or external systems.

## Core artifacts

The core is always installed and contains:

1. Concise human and agent operating principles.
2. Decision records with stable IDs, status, consequences, revision thresholds, and supersession links.
3. Claim-to-evidence rules that distinguish measured, estimated, and unknown values.
4. A reading order and links to selected modules.
5. A chronological worklog for material observations, failed attempts, deviations, and handoff state.
6. A delivery checklist covering acceptance criteria, evidence, residual risk, cost, tests, and recovery.
7. Agent guidance for work before, during, and after implementation.
8. A profile and installation manifest.
9. Update, conflict, and manual removal guidance.

The core does not require users to adopt a specification workflow, ticket process, branching model, or
agent role hierarchy.

## Optional modules and triggers

The initializer asks observable questions. Each affirmative answer recommends a module and explains the
reason. Users may accept or decline recommendations.

| Module | Observable trigger examples | Generated concerns |
|---|---|---|
| `model-api` | External model APIs, paid inference, or credentials are used | Credential boundaries, model inventory, provider retention, version policy, API usage, tokens, cost, timeout/retry limits, output validation, fallback, and change review |
| `data` | Third-party, personal, confidential, supplied, or persisted data is processed | Provenance, classification, access, licensing, minimization, allowed destinations, logs/backups, quality, derived artifacts, retention, deletion verification, and incidents |
| `evaluation` | Quality claims are made, variants are compared, or AI behavior can regress | Predefined protocols and thresholds, held-out data, uncertainty, human/model judge limits, adversarial cases, stable runs, error analysis, and external references |
| `agentic-runtime` | The application can call tools or take actions with side effects | Authentication/authorization, injection and exfiltration boundaries, approvals, validation, idempotency, compensation, sandboxing, audit, kill switches, and misuse cases |
| `operations` | The application will run in production or serve users | Ownership, service levels, health and alerts, budgets, degraded modes, releases, rollback, backup/restore, incident review, and behavioral regression |

RAG, voice, document processing, and providers are examples composed from these modules rather than
first-class modules in V1.

The saved profile records question IDs, answers, accepted and declined recommendations, and the Rig
version. A later run explains changes and recommends newly relevant modules without enabling them silently.

## Traceability model

Templates use stable, human-readable identifiers and links to connect:

```text
decision -> experiment/run -> code revision -> dataset/version
         -> model/config -> metrics -> usage/cost -> evidence
```

The generated records are a fallback and an index. They may link to Langfuse, MLflow, Weights & Biases,
cloud billing, issue trackers, ADR systems, or other canonical tools. They must not require duplicate copies
of detailed runtime traces.

Templates never require prompts, responses, secrets, personal data, confidential data, or private endpoints
to be recorded in version control.

## Installation behavior

### Planning and preview

The initializer builds an in-memory installation plan before writing. The preview classifies every proposed
path as:

- new file;
- unchanged generated file;
- changed generated file;
- untracked conflict with an existing file;
- proposed manual integration.

`--dry-run` prints the complete plan and writes nothing.

### Conflict policy

- Never overwrite silently.
- Skip an unchanged generated file.
- Show a unified diff for a changed generated file.
- In interactive mode, require an explicit choice for each conflict, with an optional explicit apply-to-all
  choice.
- In non-interactive mode, exit non-zero on conflicts. V1 provides no global force-overwrite flag.
- Never auto-merge agent instructions, security policies, ADR indexes, or other canonical project files.
- Write atomically after the full plan is approved.

### Manifest

`.applied-ai-rig/manifest.json` contains:

- manifest schema version;
- Applied AI Rig version;
- installation timestamp;
- selected modules;
- generated paths;
- original SHA-256 checksum for every generated file;
- status of proposed manual integrations.

The manifest contains no project data, secrets, absolute paths, user identity, or telemetry identifier.

### Brownfield scan

V1 scans only for conflicts and common canonical artifacts:

- `AGENTS.md`, `CLAUDE.md`, and common agent instruction files;
- existing ADR or decision directories;
- `SECURITY.md` and data-handling policies;
- existing experiment or observability tooling references;
- paths that the installer proposes to create.

The scan reports findings and suggested links. It does not infer the application stack, parse business
data, execute project code, inspect environment variables, or send repository content anywhere.

## Initializer output and interaction

Interactive prompts use observable language rather than governance terminology. Example:

```python
Question(
    id="external_model_api",
    prompt="Will this project call an external model or embedding API?",
    recommends=("model-api",),
    reason="Track credential boundaries, model usage, and attributable cost.",
)
```

Conventions:

- Question IDs and module IDs are stable public interfaces.
- Prompts state why an answer matters.
- Defaults are conservative and visible.
- Output separates facts, recommendations, warnings, and write actions.
- Interactive cancellation writes nothing.
- Error messages identify the path or field and a concrete recovery action.
- Quick profiles remain editable and are never presented as inferred facts.
- `?` explains a question, `b` navigates backward, and `q` cancels before writes.
- Module selection presents both triggered and untriggered modules and preserves explicit declines.

## Testing strategy

All tests use `unittest`, temporary directories, and deterministic fixtures. No test uses the network,
system credentials, the user's home directory, or the current repository as a target.

### Unit tests

- Intake answer to module recommendation mapping.
- Profile and manifest serialization.
- SHA-256 checksum calculation.
- Template placeholder detection.
- CSV header validation.
- Internal-link normalization.
- Conflict classification.

### Integration tests

- Fresh interactive-equivalent installation with injected answers.
- Fresh non-interactive installation with explicit modules.
- `--dry-run` makes no filesystem changes.
- Re-running an unchanged installation is idempotent.
- Modified generated files produce a diff and no silent overwrite.
- Existing `AGENTS.md` is never modified.
- Atomic failure leaves the target unchanged.
- `--check` passes a valid generated harness and reports each structural defect precisely.
- Paths containing spaces work on Linux, macOS, and Windows path semantics.

### Golden tests

Small expected generated trees verify filenames, required headings, CSV headers, manifest fields, and absence
of unselected module files. Golden fixtures avoid full-document snapshots when assertions on structure and
semantics are clearer.

No coverage percentage is required. Tests must cover every destructive or conflict-handling branch.

## Code style

- Type hints on public functions and data structures.
- `dataclasses` for immutable plans, questions, and manifest entries.
- `pathlib.Path` for filesystem operations.
- Pure planning functions separated from writes and terminal interaction.
- Explicit exceptions with recovery context.
- No generic utility modules, framework-style registries, or speculative plugin abstractions.
- UTF-8 text with `\n` generated consistently across platforms.
- Functions remain small enough to describe with one responsibility.

Representative style:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlannedFile:
    source: Path
    destination: Path
    status: str
    original_checksum: str | None = None


def classify_file(destination: Path, rendered: bytes, known_checksum: str | None) -> str:
    if not destination.exists():
        return "new"
    if destination.read_bytes() == rendered:
        return "unchanged"
    if known_checksum is None:
        return "conflict"
    return "modified"
```

## Boundaries

### Always

- Build a complete in-memory plan before writing.
- Preview selected modules and target paths.
- Keep all operations local and dependency-free.
- Preserve existing files unless the user explicitly approves a replacement.
- Use stable IDs and schema versions for generated machine-readable artifacts.
- Test every conflict and destructive branch.
- Describe checks as structural validation only.
- Keep generated projects independent from the initializer.

### Ask first

- Change a generated path or stable module/question identifier after release.
- Change manifest or profile schema compatibility.
- Add a dependency, network call, telemetry, or remote catalog.
- Add an automatic migration or removal operation.
- Add a new V1 module or make an optional module part of the core.
- Modify the conflict or overwrite policy.
- Add automatic edits to existing project instructions or policies.

### Never

- Read or print secrets, environment variables, prompts, responses, or project data.
- Execute target-project code or install its dependencies.
- Send target-project content over the network.
- Silently overwrite, delete, or merge an existing file.
- Claim legal compliance, security, safety, or production readiness.
- Implement runtime tracing, policy enforcement, secret storage, cost dashboards, or agent orchestration.
- Impose a provider, AI framework, application stack, source layout, or observability vendor.
- Generate unused optional modules.

## Success criteria

1. `python init.py <empty-target>` completes an interactive-equivalent default installation in under five
   minutes for a first-time user following the README.
2. `python init.py <target> --dry-run` produces a complete readable plan and changes no target file.
3. Re-running an unchanged installation produces no content changes.
4. Changed or conflicting files are never overwritten without explicit interactive approval.
5. Non-interactive conflicts return a non-zero exit code and leave the target unchanged.
6. The generated manifest lists the installed Rig version, selected modules, paths, and original checksums.
7. Each intake trigger recommends the expected module and explains why.
8. Declining every optional module generates only the core.
9. `python init.py --check <target>` detects missing artifacts, bad internal links, incorrect CSV headers,
   unresolved placeholders, and manifest inconsistencies without making compliance claims.
10. Existing `AGENTS.md`, `CLAUDE.md`, security policies, and ADR structures are not modified automatically.
11. The traceability templates can link a decision to code, data, model, metrics, cost, and external evidence
    through stable IDs without embedding sensitive content.
12. The full test suite passes without network access or third-party packages.
13. A generated project contains no unused module, initializer source, absolute path, telemetry identifier,
    personal information, or reference to the original author's environment.
14. Documentation explains coexistence with Spec Kit, Agent OS, coding-agent harnesses, Langfuse, MLflow,
    Weights & Biases, and runtime policy tools.

## Explicitly out of scope for V1

- Academic research workflow and distributed model training.
- GPU cluster operation and model-serving infrastructure.
- Application source-code scaffolding.
- Specification-to-code workflows.
- Coding-agent roles, skills, orchestration, or marketplaces.
- Runtime model tracing or observability.
- Runtime authorization or policy enforcement.
- Secret vaults and credential brokers.
- Compliance certification or legal advice.
- Cost dashboards or billing ingestion.
- Provider-specific, RAG-specific, voice-specific, or framework-specific modules.
- Automatic stack inference.
- Remote module catalogs and plugins.
- Automatic merge of existing agent instructions.
- Automatic migration, uninstall, or destructive cleanup.

## Open questions

None blocking for V1. Any new module, automatic migration behavior, or remote integration requires a spec
revision before implementation.
