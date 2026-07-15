# Applied AI Rig: landscape review

_Research date: 2026-07-15. Sources are official repositories and documentation._

## Conclusion

Applied AI Rig is not a duplicate of the closest projects reviewed. Existing tools largely cover one of three adjacent concerns: spec-driven delivery, coding-agent configuration, or runtime AI governance. None of them installs a small, provider-neutral project harness that connects applied-AI decisions, data handling, experiments, model/API usage, cost, and safe instructions for coding agents.

The strongest opportunity is therefore not to compete with Spec Kit or Agent OS. Applied AI Rig should be a composable governance layer that can coexist with them. Its V1 should stay artifact-first, dependency-free after generation, and useful without an observability platform.

## Closest projects

| Project | What it actually owns | Useful overlap | Gap relative to Applied AI Rig |
|---|---|---|---|
| [AI Engineering Harness](https://github.com/adrielp/ai-engineering-harness) | Installs prompts, skills, sub-agents and a ticket-plan-implement-validate workflow for Claude Code, OpenCode, Gemini CLI and Pi. Its installer supports dry-run, interactive component selection, safe re-runs, diffs for modified files, and leaves real files rather than a runtime dependency. | The installer experience is the clearest precedent for preview, selective installation, conflict handling and self-contained output. | It governs coding-agent workflow and context, not the lifecycle of an AI-enabled application. It does not provide data classification, API/model inventories, experiment-to-decision traceability, or product inference cost accounting. |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | A full spec-driven workflow: constitution, specification, clarification, plan, tasks, analysis and implementation, with 30+ agent integrations. It has extensions, presets, project-local overrides and bundles with explicit precedence. | Its constitution and layered customization model validate the idea of a small mandatory core plus optional modules. Cross-artifact analysis and pre-implementation clarification are valuable patterns. | It governs how software requirements become code. It does not specialize in model/data risk, evaluation datasets, model/API usage, inference cost, or the provenance of AI experiments. Its installed workflow and CLI ecosystem are much broader than the proposed lightweight harness. |
| [Agent OS](https://github.com/buildermethods/agent-os) | Discovers codebase conventions, documents and indexes standards, injects relevant standards, and shapes specs across coding tools. | Brownfield onboarding should respect existing project conventions; generated agent guidance should point to canonical project standards instead of duplicating them. | The public scope is coding standards and specifications, not applied-AI governance or operational evidence. |
| [AI Project Governance](https://github.com/ai-godfather/ai-project-governance) | Installs a process contract for AI-assisted development: 16 roles, approval and audit gates, failure patterns, evidence rules, changelogs, ADRs, validation workflows and Cursor adapters. It exposes minimal, standard and enterprise adoption levels and supports migration with backups. | It demonstrates the value of an explicit adoption level, install validation, removal/migration guidance, evidence-backed claims and a documented reading order for agents. | It is intentionally process-heavy, role-centric and largely about governing AI coding assistants. Its own guidance says the overhead is inappropriate for throwaway or solo projects. Applied AI Rig should govern the application being built and remain useful to a small team without enforcing a multi-role workflow. |
| [Cookiecutter Data Science](https://github.com/drivendataorg/cookiecutter-data-science) | Generates a standardized but configurable data-science project structure, including separate raw/interim/processed data areas, notebooks, models, reports and reproducible environment files. | It is a mature example of asking configuration questions once and generating only the relevant structure. Its separation of data stages is a useful optional pattern for data-heavy projects. | It scaffolds project code and data directories and requires a separately installed CLI. It does not define decision, secret, model API, cost, experiment-governance or coding-agent policies. Applied AI Rig should not impose a source tree or ML stack. |
| [Project Starfish](https://projectstarfish.ca/) | Runtime policy enforcement for AI agents, with policy decisions around identities, tools and resources. | Its explicit subject-action-resource policy model is relevant when an application operates autonomous agents with meaningful permissions. | This is enforcement infrastructure for running agents, not a repository governance template. Recreating runtime authorization in Markdown would create false assurance; Applied AI Rig should instead record when a real policy/enforcement layer is required. |

## What to adopt in V1

### 1. Make installation behavior a product feature

Adopt the safe ergonomics demonstrated by AI Engineering Harness: `--dry-run`, explicit module selection, idempotent re-runs, and a readable diff before replacing a modified file. Add a machine-readable installation manifest containing the Applied AI Rig version, selected modules, generated files and their original checksums. That enables later inspection or removal without keeping the initializer installed.

For V1, conflict behavior should be deliberately conservative:

- never overwrite silently;
- skip an unchanged generated file;
- show a diff for a changed generated file;
- require an explicit per-file or global overwrite choice;
- never auto-merge `AGENTS.md` or equivalent agent instruction files.

### 2. Use a true core/module boundary

Borrow the concept, not the machinery, of Spec Kit's layered extensions and AI Project Governance's adoption levels. The initializer should explain _why_ it recommends a module, then let the user accept or reject it.

Suggested V1 core:

- concise agent/human operating principles;
- decision records with status and supersession;
- claim/evidence rules;
- installation manifest and update/removal guidance.

Suggested conditional modules:

- external model APIs, credentials, usage and cost;
- supplied or sensitive data and derived artifacts;
- evaluation and significant experiment records;
- agentic/runtime permissions and human approval boundaries;
- production operations and incident handling.

RAG, document processing and specific providers should be examples or profiles composed from these risk modules, not first-class silos.

### 3. Add a lightweight project intake and risk trigger matrix

The initializer should ask observable questions rather than ask users to choose governance jargon: Will external model APIs be called? Will third-party or personal data be processed? Will prompts or outputs be persisted? Can the application take actions with side effects? Are evaluation claims intended for users or stakeholders? Will it run in production?

Each affirmative answer should map transparently to a recommended module. Save the answers locally in a small project profile so a future re-run can explain drift and propose newly relevant modules.

### 4. Define links between artifacts, not duplicate telemetry

Applied AI Rig's important differentiator is a minimal traceability chain:

`decision -> experiment/run -> code revision -> dataset/version -> model/config -> metrics -> usage/cost -> evidence`

Templates should use stable IDs and permit links to external systems such as Langfuse, MLflow, Weights & Biases or cloud billing. The generated CSV/Markdown files are a fallback and decision index, not a requirement to duplicate detailed traces. A module should state this explicitly.

### 5. Support brownfield projects from day one

Agent OS and Spec Kit both treat existing project context as important. Applied AI Rig should scan only for conflicts and common canonical files (`AGENTS.md`, `CLAUDE.md`, ADR directories, security policy, existing experiment tooling); it should not infer the application stack in V1. The preview should distinguish new files, conflicts and suggested links to existing artifacts.

### 6. Validate the generated harness

Add `python init.py --check <target>` (or an equivalent check mode) that performs structural checks only: selected artifacts exist, internal links and CSV headers are valid, placeholders are resolved, and generated agent instructions reference real files. It must not claim that the project is compliant or secure.

## Explicit V1 rejections

- **Do not build another spec-to-code workflow.** Spec Kit and Agent OS already serve that problem well; provide coexistence notes instead.
- **Do not ship specialized coding-agent roles or orchestration.** The AI Engineering Harness and AI Project Governance already explore that space, and role proliferation would obscure the product-governance purpose.
- **Do not implement runtime tracing, policy enforcement, a secrets vault, or a cost dashboard.** Integrate by reference with purpose-built tools; static templates cannot enforce runtime controls.
- **Do not impose a project directory, model provider, evaluation framework, RAG architecture or observability vendor.** Cookiecutter Data Science is useful precisely because its structure fits its domain; Applied AI Rig's domain is cross-cutting governance.
- **Do not promise regulatory compliance.** Generate prompts for ownership, classification, retention and escalation, but label them as engineering records rather than legal controls.
- **Do not create an extension marketplace or remote catalog in V1.** Keep modules in the repository, version them together and prove the core installation/update semantics first.
- **Do not auto-edit existing agent instructions.** Produce a proposed snippet or companion file and require human review, because instruction precedence differs across tools.

## Positioning

Recommended one-line positioning:

> Applied AI Rig installs a lightweight, modular engineering record for the models, data, experiments, costs and decisions behind an AI-enabled application.

This distinguishes it from "build with agents" products and from compliance frameworks. The key promise is not more process; it is enough durable evidence to understand, review and operate an applied-AI system without requiring a platform.

## Source notes

- AI Engineering Harness documents selective install, dry-run, safe re-runs, diffs and self-contained copied files in its [official README](https://github.com/adrielp/ai-engineering-harness#quick-start).
- Spec Kit documents its constitution-to-implementation workflow and customization precedence in its [official repository](https://github.com/github/spec-kit#%EF%B8%8F-get-started) and [extensions documentation](https://github.github.io/spec-kit/extensions/overview/).
- Agent OS describes standards discovery, deployment, indexing and spec shaping in its [official README](https://github.com/buildermethods/agent-os#agents-that-build-the-way-you-would).
- AI Project Governance documents its installed-artifact model, governance levels, evidence rules and migration behavior in its [official README](https://github.com/ai-godfather/ai-project-governance#this-repo-is--is-not).
- Cookiecutter Data Science documents its configurable generated layout in its [official repository](https://github.com/drivendataorg/cookiecutter-data-science#cookiecutter-data-science).
- Project Starfish describes its runtime policy model in its [official documentation](https://projectstarfish.ca/).
