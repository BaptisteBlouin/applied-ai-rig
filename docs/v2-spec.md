# Applied AI Rig V2: adoption workflow

## Objective

Make the existing V1 engineering record useful within the first fifteen minutes and easy to maintain in
normal project work. V2 keeps the generated paths, profile schema, register headers, offline behavior, and
provider-neutral scope stable.

V2 is prepared on a private branch. Repository visibility, package publication, release creation, and
remote GitHub settings are explicitly outside this work.

## Product promise

Applied AI Rig makes consequential AI changes reviewable. The decision, supporting evidence, data and
permission boundaries, cost, and recovery expectations remain understandable in the repository after a
conversation or coding-agent session ends.

The primary audience is an individual developer or small team building an AI-enabled application with
models, data, evaluations, tools, or production operations. The product is an engineering-memory and
review aid, not a compliance product.

## Compatibility constraints

- Keep profile and manifest schema version 1 readable.
- Keep the V1 core paths and all CSV headers unchanged.
- Do not add a runtime dependency, network call, telemetry, provider integration, or new risk module.
- Keep old installation and check command forms working.
- Keep generated projects useful without the initializer installed.

## Required outcomes

### Discoverable value

- The repository README leads with the problem solved and a short before/after scenario.
- The first documented command works on supported Linux and macOS environments by using `python3`.
- Three worked examples demonstrate complete decision-to-evidence chains for a RAG change, a tool-using
  agent, and a production incident.
- Documentation states clearly when the Rig is too much and when not to use it.

### Progressive adoption

- The generated core README gives one first action and a fifteen-minute path to value.
- Register guidance distinguishes the minimum useful fields from fields completed when risk requires them.
- Installation ends with the exact next commands for the target.
- Rich schemas remain available without requiring every field on the first entry.

### Daily workflow

- `applied-ai-rig status [target]` reports selected modules, structural health, record counts, and the next
  useful action without changing files.
- `applied-ai-rig add decision [target]` previews or appends a safe proposed decision skeleton.
- `applied-ai-rig add evidence [target]` previews or appends a measured, estimated, or unknown evidence
  skeleton linked to a decision.
- `applied-ai-rig add experiment [target]` previews or appends a schema-valid experiment row when the
  evaluation module is installed.
- Record creation refuses duplicate IDs, refuses missing installations or modules, previews by default,
  and requires `--yes` before writing in automation.
- Writes are atomic and remain within the target project.

### Ecosystem readiness

- A composite GitHub Action can run the structural check after the repository becomes public.
- Integration recipes describe stable-reference mappings for pull requests, experiment trackers, billing,
  and observability without adding vendor dependencies.
- Machine-readable profile and manifest schemas document the existing JSON contracts.
- Versioning and migration policy plus a changelog exist before the first public release.
- Issue, pull-request, and module-proposal templates guide future community contributions.

## Verification

- New behavior is developed test-first.
- Unit and CLI integration tests cover previews, writes, invalid targets, missing modules, duplicate IDs,
  record counts, next-action output, and legacy command compatibility.
- Static tests validate examples, JSON schemas, the composite action, and public-facing links.
- The full unit suite, compilation, Ruff, and strict Mypy pass.
- A final review checks standards, security boundaries, and this specification before integration.

## Adoption signals after publication

Because the tool has no telemetry, early validation is opt-in and qualitative. Target signals are five
external pilot repositories, median installation under five minutes, a first real record within fifteen
minutes, and at least three pilots updating a record in a later pull request.
