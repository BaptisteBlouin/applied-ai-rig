# Register model and scaling policy

Applied AI Rig uses CSV because it is portable, inspectable, diffable, supported by the Python standard
library, and useful without a platform. CSV is the default adapter for a register interface; it is not a
claim that Git is the correct operational database for every project.

The generated `REGISTER_GUIDANCE.md` is the user-facing operating contract. This document records the
repository-level design decision and evolution rules for maintainers.

## Decision

Each register supports two modes:

1. **Embedded register:** the generated CSV is the system of record for a small, slowly changing,
   non-sensitive inventory with coordinated writers.
2. **External index:** an external access-controlled system is the system of record; the CSV retains only
   decision-relevant summaries and stable references.

The interface is the same in both modes: stable record IDs connect decisions, evidence, code, data, models,
operations, and external systems. The storage implementation may change without changing those concepts.

The governing rule is:

> One row per decision-relevant record, not one row per runtime event.

## Why CSV remains the default adapter

- It works offline and adds no dependency or service.
- Humans and coding agents can inspect and edit it.
- Pull requests expose small inventory changes clearly.
- Projects can import or export it using common tools.
- It provides a useful fallback when no specialist system exists.

CSV stops earning its place when writers, volume, queries, access control, retention, or transactional
requirements dominate reviewability. At that seam, an experiment tracker, billing system, data catalog,
incident platform, observability tool, database, or other canonical system should become the adapter.

## Required semantics

Every register README or linked project decision must identify:

- the grain represented by one row;
- the system of record;
- the accountable owner;
- stable ID and reference rules;
- required, optional, controlled, and unknown values;
- creation, update, closure, supersession, archival, and reconciliation rules;
- sensitive or prohibited fields;
- the externalization threshold and reconciliation cadence.

`api_usage.csv` contains aggregates associated with decisions, runs, releases, workloads, or billing
periods. `experiments.csv` contains baselines, decision-relevant variants, regression checks, and cited final
runs. Neither file is a runtime event store.

## Externalization criteria

An external system should become canonical when:

- runtime automation produces rows continuously;
- concurrent writers create recurring merge conflicts;
- row-level access or sensitive metadata is required;
- filtering, joins, aggregation, dashboards, or retention jobs are operational needs;
- updates require transactions or immediate consistency;
- another organizational system already owns the lifecycle and audit history.

The Rig then stores a safe decision index, an external reference, or a documented pointer. It must not
duplicate detailed traces merely to preserve the CSV shape.

## Compatibility policy

CSV headers are a public generated interface. Renaming, removing, reordering, or changing the meaning of a
column requires a specification change, migration guidance, checker updates, tests, and a profile or
manifest compatibility review. Adding a register requires an explicit row grain and proof that it will not
collect runtime events or sensitive payloads by default.

Future adapters may add stronger validation or synchronization, but the initializer must remain useful
offline and must not require an external platform.
