# Modules

The initializer recommends modules from observable project risks. A recommendation explains why the module
may help; the user decides whether to install it. Declined recommendations remain visible in the project
profile so a later run can explain changes.

## Core

The core is always installed. It contains operating principles, decisions, evidence, reading order,
companion agent guidance, profile, and manifest. It deliberately excludes ticketing, branching, agent roles,
and specification workflows.

## Model API

Trigger examples:

- External generation, embedding, reranking, or multimodal APIs.
- Metered inference or credentials supplied by another organization.
- Model-based evaluation or synthetic generation.

The module records credential boundaries and attributable usage. Unknown tokens or prices remain unknown.
Detailed traces can stay in an external system.

## Data

Trigger examples:

- Supplied, personal, confidential, or third-party data.
- Persisted prompts, outputs, embeddings, indexes, or evaluation artifacts.

The module covers provenance, classification, minimization, allowed destinations, derived artifacts,
retention, deletion, and incidents. It produces engineering records, not legal conclusions.

## Evaluation

Trigger examples:

- Comparing models, prompts, retrieval strategies, or application variants.
- Publishing a quality, latency, cost, or safety claim.
- Managing behavior that can regress after model or data changes.

The module creates a stable experiment index connecting decisions, code, datasets, model configuration,
metrics, usage, and evidence. It can link to an experiment tracker instead of copying runtime traces.

## Agentic runtime

Trigger examples:

- Tool calls, external communication, purchases, writes, or destructive actions.
- Loops with material cost or resource consumption.

The module records permission boundaries, argument validation, human approval points, limits, and escalation.
It does not enforce these controls at runtime.

## Operations

Trigger examples:

- Serving users or running scheduled and long-lived processes.
- Owning releases, incidents, rollback, health, and operating limits.

The module records responsibilities and links to operational systems. It does not generate deployment or
monitoring infrastructure.

## Adding a module

A new module requires a specification change. It must address a distinct risk, remain provider-neutral,
generate no unused artifacts, define stable record headers, and prove absence when unselected.
