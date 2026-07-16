# Modules

The initializer recommends modules from observable project risks. A recommendation explains why the module
may help; the user decides whether to install it. Declined recommendations remain visible in the project
profile so a later run can explain changes.

Use `python init.py --list-modules` for a summary or `python init.py --explain <module>` for its trigger,
coverage, and generated artifacts. Interactive setup offers editable quick profiles and a custom assessment;
`--modules` remains available for exact scripted selection.

Every optional module also installs `REGISTER_GUIDANCE.md`. It defines the two supported operating modes —
embedded register and external index — together with row grain, ownership, scale, concurrency, sensitive
content, and externalization rules. The repository-level rationale is in [registers.md](registers.md).

## Core

The core is always installed. It contains operating principles, decisions, evidence, reading order,
companion agent guidance, profile, and manifest. It deliberately excludes ticketing, branching, agent roles,
and specification workflows.

## Model API

Trigger examples:

- External generation, embedding, reranking, or multimodal APIs.
- Metered inference or credentials supplied by another organization.
- Model-based evaluation or synthetic generation.

The module records credential boundaries, model/version policy, approved data classes, provider retention,
limits, retries, structured-output validation, fallback, attributable usage, and cost. Unknown tokens or
prices remain unknown. Detailed traces can stay in an external system.

## Data

Trigger examples:

- Supplied, personal, confidential, or third-party data.
- Persisted prompts, outputs, embeddings, indexes, or evaluation artifacts.

The module covers provenance, classification, licensing, access, minimization, allowed destinations,
logs and backups, quality limits, hostile content, derived artifacts, retention, deletion verification, and
incidents. It produces engineering records, not legal conclusions.

## Evaluation

Trigger examples:

- Comparing models, prompts, retrieval strategies, or application variants.
- Publishing a quality, latency, cost, or safety claim.
- Managing behavior that can regress after model or data changes.

The module adds an evaluation plan and stable experiment index connecting decisions, code, held-out data,
model configuration, predefined thresholds, uncertainty, human or model judges, error analysis, usage, and
evidence. It can link to an experiment tracker instead of copying runtime traces.

## Agentic runtime

Trigger examples:

- Tool calls, external communication, purchases, writes, or destructive actions.
- Loops with material cost or resource consumption.

The module records authentication and permission boundaries, injection and exfiltration cases, argument and
result validation, human approval, idempotency, compensation, isolation, audit, limits, kill switches, and
escalation. It does not enforce these controls at runtime.

## Operations

Trigger examples:

- Serving users or running scheduled and long-lived processes.
- Owning releases, incidents, rollback, health, and operating limits.

The module records responsibilities, service expectations, health and alerts, runbooks, dependency and
budget limits, degraded modes, releases, rollback, backup/restore evidence, incidents, and behavioral
regressions. It does not generate deployment or monitoring infrastructure.

## Adding a module

A new module requires a specification change. It must address a distinct risk, remain provider-neutral,
generate no unused artifacts, define stable record headers, and prove absence when unselected.
