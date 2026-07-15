# Coexistence with other tools

Applied AI Rig owns a lightweight engineering record for the AI-enabled application. It does not need to
own requirements, coding-agent workflows, detailed runtime traces, billing, or runtime enforcement.

## Specification workflows

GitHub Spec Kit and similar tools can remain the canonical source for requirements, plans, and tasks. Link
their feature or specification IDs from a Rig decision or evidence record. Do not copy full specifications
into Rig files.

## Coding-agent harnesses and standards

Agent OS, AI Engineering Harness, and project-specific agent instructions can remain authoritative for how
software changes are planned and implemented. `APPLIED_AI_RIG_AGENT.md` is a companion focused on AI-product
records. Review a proposed link manually instead of auto-merging instruction files.

## Experiment and observability platforms

Langfuse, MLflow, Weights & Biases, and equivalent systems can own detailed traces, prompts, spans, datasets,
and metrics. The evaluation module keeps only the decision-relevant index and an external reference. Never
copy sensitive traces into version control to make the index self-contained.

## Billing and model providers

Provider dashboards and cloud billing are preferable sources for billed usage. The model API module records
the attributable project view, pricing snapshot, and evidence link. It does not scrape billing systems or
invent missing costs.

## Runtime policy and authorization

Purpose-built policy engines and application authorization remain responsible for enforcement. The agentic
runtime module documents intended permissions, approvals, and escalation so reviewers can identify where
real enforcement is required.

## Existing governance files

Existing ADR directories, security policies, data policies, and incident processes stay canonical. During
installation, use manual links from the generated reading order rather than allowing two conflicting sources
of truth. Applied AI Rig never auto-merges these files.
