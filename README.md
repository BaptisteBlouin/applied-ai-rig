# Applied AI Rig

Applied AI Rig installs a lightweight, modular engineering record for the models, data, experiments,
costs, and decisions behind an AI-enabled application.

It gives humans and coding agents enough durable evidence to understand why an applied-AI system was built
the way it was, without requiring a governance platform or imposing an application stack.

## What it generates

Every installation includes a small core:

- Operating principles for humans and agents.
- Decision records with status, consequences, revision thresholds, and supersession.
- A claim-to-evidence index that distinguishes measured, estimated, and unknown values.
- A chronological worklog for observations, failed attempts, deviations, and handoff context.
- A delivery checklist for acceptance criteria, residual risks, costs, tests, and recovery expectations.
- A project profile and checksum manifest for safe re-runs.
- Companion agent instructions covering work before, during, and after implementation.

Optional modules are recommended from observable project risks:

| Module | Use it when |
|---|---|
| `model-api` | Credentials, model inventory, usage/cost, limits, retries, validation, fallback, and provider changes |
| `data` | Provenance, access, destinations, derivatives, quality, retention, backups, and verified deletion |
| `evaluation` | Evaluation plans, held-out data, thresholds, uncertainty, human/model judges, runs, and error analysis |
| `agentic-runtime` | Permissions, injection/exfiltration, approvals, idempotency, compensation, isolation, and misuse cases |
| `operations` | Ownership, service levels, limits, alerts, runbooks, releases, recovery, incidents, and regressions |

Module CSV files are small decision-relevant registers, not runtime event stores. They may be the system of
record for low-volume projects or safe indexes into external canonical tools for larger projects. See the
[register model and scaling policy](docs/registers.md).

## Quick start

Applied AI Rig requires Python 3.10 or later and uses only the standard library.

```bash
git clone https://github.com/BaptisteBlouin/applied-ai-rig.git
cd applied-ai-rig
python init.py /path/to/your-project
```

On systems where the launcher is named `python3` (most Linux and macOS installations), run
`python3 init.py …` in place of `python init.py …` throughout this guide.

To install it as a reusable command instead of running from a clone:

```bash
pipx install git+https://github.com/BaptisteBlouin/applied-ai-rig.git
applied-ai-rig /path/to/your-project
```

The installed `applied-ai-rig` command accepts the same arguments as `python init.py`.

Review the proposed modules and files before confirming. For a preview that writes nothing:

```bash
python init.py /path/to/your-project --dry-run
```

For scripted installation with explicit modules:

```bash
python init.py /path/to/your-project \
  --modules model-api,data,evaluation \
  --non-interactive
```

Use `--modules none` for a core-only installation.

## Guided setup

![The guided web setup: a starting-point step with quick profiles on the left and a contextual explanation panel on the right](docs/images/web-setup.png)

On an interactive terminal, setup opens a temporary local web interface. It is served only from
`127.0.0.1`, works offline, uses no external assets, and stops after confirmation or cancellation. The
interface offers four quick profiles plus a custom risk assessment:

1. Minimal core.
2. API or RAG application.
3. Agent with tools.
4. Production AI service.
5. Custom assessment.

Quick profiles and the custom assessment are alternative starting routes. Both lead to an explicit module
review, followed by the real file plan and readable diffs. Contextual explanations describe when each
choice applies, what it generates, and what it does not provide. Changed or conflicting files require
individual approval before the plan can be confirmed.

Use the terminal wizard when a browser is unavailable or undesirable:

```bash
python init.py /path/to/your-project --terminal
```

For SSH and remote environments, start the web interface without attempting to open a browser, then open
the printed loopback URL through the environment's normal forwarding mechanism:

```bash
python init.py /path/to/your-project --no-browser
```

When standard input or output is not a TTY, the initializer keeps the deterministic terminal behavior.
`--non-interactive`, `--modules`, checks, and automation never start a local server.

Inspect the choices without starting the wizard:

```bash
python init.py --list-modules
python init.py --explain evaluation
```

Use a quick profile directly, interactively or in automation:

```bash
python init.py /path/to/your-project --profile api-rag
python init.py /path/to/your-project --profile production --non-interactive
```

Named profiles are starting points, not claims about the project. Review the resulting modules and decline
anything that does not apply.

## Structural check

```bash
python init.py --check /path/to/your-project
```

The check validates the installed manifest, selected files, internal links, CSV headers, and unresolved
template placeholders. It is a structural check, not a security assessment or compliance certification.

## Safe by default

- `--dry-run` builds the complete plan without changing the target.
- Existing files are never overwritten silently.
- Changed generated text receives a readable diff before interactive approval.
- Non-interactive conflicts fail without changing the target.
- Existing agent instructions and canonical project policies are never merged automatically.
- Installation writes are staged and rolled back on failure.
- The initializer performs no network request, telemetry, stack inference, or target-code execution.
- The optional local setup server binds only to `127.0.0.1`, validates session, host, origin, payload size,
  profile fields, modules, plan digest, and conflict approvals, and makes no external request.

The generated project has no runtime dependency on Applied AI Rig.

## Re-running and updating

Run the same initializer command again. The installed profile records selected modules, while the manifest
records generated paths and original checksums. Unchanged files are skipped. User-modified generated files
require explicit review.

V1 has no automatic removal command. To remove the Rig, inspect `.applied-ai-rig/manifest.json`, review each
listed path, delete only files that you no longer need, then remove `.applied-ai-rig/`. Do not delete a file
solely because it appears in the manifest: it may contain project-owned changes.

## Interoperability

Applied AI Rig complements specification workflows, coding-agent harnesses, experiment trackers, cloud
billing, and runtime policy tools. It links to those canonical systems instead of duplicating their traces.
See [coexistence guidance](docs/coexistence.md).

## Non-goals

Applied AI Rig does not scaffold application code, orchestrate coding agents, trace models at runtime, store
secrets, enforce runtime permissions, provide legal advice, or certify compliance. It does not impose a
provider, framework, source tree, deployment platform, or observability vendor.

## Development

The tool itself uses only the standard library. Linting and type checking use `ruff` and `mypy`, declared
as an optional `dev` extra and enforced in CI:

```bash
pip install -e ".[dev]"

python -m unittest discover -s tests -v      # tests
python -m compileall -q init.py applied_ai_rig tests
ruff check init.py applied_ai_rig tests      # lint
mypy                                         # strict type check (configured in pyproject.toml)
```

Tests run on Linux, macOS, and Windows against Python 3.10 and 3.13.

The approved V1 requirements are in [the specification](docs/spec.md), with implementation sequencing in
[the plan](tasks/plan.md).
