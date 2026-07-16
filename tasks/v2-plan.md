# V2 implementation plan

## 1. Workflow seam

- [x] Add failing tests for command dispatch, post-install guidance, and status output.
- [x] Add failing tests for decision, evidence, and experiment preview/write safety.
- [x] Implement a focused record-workflow module with atomic writes and duplicate checks.
- [x] Preserve all legacy initializer command forms.

## 2. Progressive adoption

- [x] Add a fifteen-minute first-use path to the generated core README.
- [x] Label minimum useful register fields without changing CSV schemas.
- [x] Add exact next commands to successful installation output.

## 3. Proof of value

- [x] Rework the repository README around outcome, fit, and one concrete scenario.
- [x] Add filled RAG, tool-agent, and production-service examples.
- [x] Link examples, CI, integrations, and versioning from the README.

## 4. Ecosystem readiness

- [x] Add a composite structural-check action and consumer documentation.
- [x] Add provider-neutral integration recipes.
- [x] Add profile and manifest JSON schemas.
- [x] Add changelog, versioning/migration policy, roadmap, and community templates.

## 5. Verification and branch handoff

- [x] Run focused tests throughout implementation.
- [x] Run full tests, compilation, Ruff, and Mypy.
- [x] Review against repository standards and the V2 specification.
- [x] Commit complete implementation history to `v2`.
- [ ] Integrate on `main`, remove `docs/v2-spec.md` and `tasks/v2-plan.md`, and commit the production surface.
