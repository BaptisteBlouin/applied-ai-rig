# Applied AI Rig V1 implementation plan

## Goal

Build the dependency-free initializer specified in `docs/spec.md`, together with a small but complete set of
core and optional templates. Validate the product through temporary-directory integration tests before
expanding public documentation.

The implementation follows vertical slices. Each checkpoint must produce a usable behavior, not only an
internal abstraction.

## Dependency map

```text
project skeleton
      |
      v
domain types and template inventory
      |
      +-------------------+
      v                   v
intake and profile    rendering and file classification
      |                   |
      +---------+---------+
                v
       installation planning
                |
                v
    preview and atomic installation
                |
                v
      manifest and safe re-runs
                |
                v
        structural --check mode
                |
                v
     public templates and documentation
```

The CLI remains a thin adapter over these components. Filesystem writes begin only after planning,
classification, preview, and approval are complete.

## Phase 1: establish the executable skeleton

### Outcome

A user can run `python init.py --help`, the package imports on Python 3.10+, and the test suite executes
without dependencies or network access.

### Work

- Add repository metadata: `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and `.gitignore`.
- Add `init.py` as a minimal entry point delegating to `applied_ai_rig.cli`.
- Create the package and test layout defined by the specification.
- Establish exit-code and error-message conventions.
- Add smoke tests for help, invalid arguments, and importability.

### Checkpoint

```bash
python init.py --help
python -m compileall -q init.py applied_ai_rig tests
python -m unittest discover -s tests -v
```

No installation behavior is implemented in this phase.

## Phase 2: model intake, modules, and profiles

### Outcome

Injected answers produce deterministic module recommendations with human-readable reasons. Profiles can be
serialized and reloaded without losing declined recommendations or schema information.

### Work

- Define immutable question, recommendation, profile, and module metadata types.
- Encode the stable V1 question and module IDs.
- Implement the trigger matrix for `model-api`, `data`, `evaluation`, `agentic-runtime`, and `operations`.
- Separate recommendations from user selections.
- Serialize `.applied-ai-rig/profile.json` with a schema version and Rig version.
- Reject unknown or malformed non-interactive input rather than guessing.

### Checkpoint

- Every affirmative trigger recommends the intended module and explains why.
- A user can decline a recommendation without losing the reason in the saved profile.
- Profile round trips are deterministic.
- No prompt rendering or target-project inspection occurs yet.

## Phase 3: render a minimal core through a pure installation plan

### Outcome

Given a target and profile, the program produces a complete in-memory plan for a core-only installation and
can display it through `--dry-run` without writing.

### Work

- Add the core template inventory and a deliberately small placeholder renderer.
- Implement path validation and reject template destinations escaping the target.
- Define planned-file statuses and conflict metadata.
- Classify new files and untracked conflicts.
- Detect common brownfield artifacts without reading project data or environment variables.
- Generate proposed manual integrations for existing agent instructions.
- Render `.applied-ai-rig/profile.json` and the initial manifest content in memory.
- Implement deterministic preview output.

### Checkpoint

```bash
python init.py /tmp/example --modules none --non-interactive --dry-run
```

- The target remains byte-for-byte unchanged.
- Only core files appear in the plan.
- Existing `AGENTS.md` is reported as a manual integration and is never edited.
- Invalid or escaping destinations fail before any write.

## Phase 4: install atomically and support safe re-runs

### Outcome

An approved plan installs the core, writes a checksum manifest, and can be re-run safely. Conflicts never
cause silent replacement or partial installation.

### Work

- Write planned files through a target-local staging area.
- Approve the complete plan before replacing any destination.
- Use atomic file replacement where supported by the standard library.
- Finalize the manifest with original generated checksums.
- Classify unchanged generated files, user-modified generated files, and untracked conflicts on re-run.
- Produce unified diffs for changed text files.
- Implement interactive per-file decisions and an explicit apply-to-all choice.
- Make non-interactive conflicts fail without changes.
- Clean staging artifacts after success or failure.

### Checkpoint

- Fresh installation succeeds.
- Unchanged re-run produces no content changes.
- Modified generated files produce a diff and require approval.
- Simulated failure leaves the target in its pre-run state.
- Existing canonical files remain untouched.

This is the highest-risk phase. It is complete only after destructive and conflict branches have dedicated
integration tests.

## Phase 5: add optional modules as end-to-end slices

### Outcome

Each selected module adds only its own coherent artifacts, internal links, stable record headers, and agent
guidance. Unselected modules leave no files or references behind.

### Order

1. `model-api`
2. `data`
3. `evaluation`
4. `agentic-runtime`
5. `operations`

The first three prove cross-record traceability. The final two prove that the module mechanism supports
behavioral and operational risks without becoming runtime enforcement.

### Work per module

- Add the minimum human-readable policy or procedure.
- Add record templates only when the module needs durable evidence.
- Add stable IDs and links to core decisions and evidence.
- Add optional links to external canonical systems instead of duplicating their telemetry.
- Extend generated reading order and agent guidance.
- Add a fresh-install and absence-when-unselected integration test.

### Checkpoint

- A project selecting all modules produces a coherent linked harness.
- A core-only project remains small.
- CSV headers and internal links match their documented schemas.
- No module contains provider, framework, RAG, or observability-vendor requirements.

## Phase 6: implement structural checking

### Outcome

`python init.py --check <target>` verifies the installed harness structure without modifying the target or
making security or compliance claims.

### Work

- Load and validate profile and manifest schema versions.
- Verify selected artifact presence and recorded checksums without treating user modifications as automatic
failures when the manifest policy permits them.
- Validate required Markdown headings and internal relative links.
- Validate generated CSV headers.
- Detect unresolved template placeholders.
- Verify that generated agent guidance references existing generated files.
- Return stable non-zero exit codes and actionable findings.

### Checkpoint

- A valid generated harness passes.
- Each defect class has an isolated failing fixture.
- Check mode performs no writes and no network or target-code execution.
- Output consistently says `structural check`, never `compliant`, `secure`, or `production-ready`.

## Phase 7: complete public usability and coexistence documentation

### Outcome

A new user can understand, install, inspect, update, manually remove, and contribute to Applied AI Rig
without knowledge of the project that inspired it.

### Work

- Finish the README with positioning, quick start, module selection, examples, and limitations.
- Document every module and its trigger questions.
- Document coexistence with Spec Kit, Agent OS, coding-agent harnesses, Langfuse, MLflow, Weights & Biases,
  cloud billing, and runtime policy tools.
- Document safe re-runs, conflicts, manifest semantics, and manual removal.
- Add maintainer guidance for stable IDs and schema changes.
- Verify that no generated or public-facing file contains names, private paths, or context from the project
  that originally motivated the template.

### Checkpoint

- A clean-room walkthrough completes in under five minutes.
- Documentation commands match the implemented CLI exactly.
- All examples use synthetic, provider-neutral content.
- The full suite and compile check pass.

## Phase 8: release-readiness review

### Outcome

The repository is internally consistent and ready for an initial public release, without publishing or
creating external resources automatically.

### Work

- Run the complete test suite on a clean temporary target.
- Test paths containing spaces and non-ASCII characters.
- Review every filesystem mutation and conflict branch.
- Review generated files for unresolved placeholders and accidental personal context.
- Compare the implementation against every success criterion in `docs/spec.md`.
- Record any deferred work as explicit post-V1 scope rather than hidden TODOs.

### Checkpoint

Produce a concise verification report mapping all 14 success criteria to evidence. Publishing the GitHub
repository, creating releases, or configuring external CI remains a separate user-authorized action.

## Parallel work

The following work can proceed independently after the relevant interface is stable:

- Core and optional template prose after the template context contract is defined.
- Checker fixtures after manifest and generated-path schemas are defined.
- Public coexistence documentation after module boundaries are stable.

The following must remain sequential:

- Manifest schema after profile and module IDs.
- Writes after pure planning and conflict classification.
- Safe re-runs after manifest checksums.
- Check mode after the generated structure stabilizes.
- Final documentation after CLI behavior stabilizes.

No parallel branch may edit stable IDs, schemas, generated paths, or conflict semantics without first
updating the specification.

## Main risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Initializer overwrites user work | Data loss and immediate loss of trust | Pure plans, dry-run, conservative conflicts, atomic writes, destructive-branch tests |
| The core becomes bureaucratic | Low adoption and conflict with the product promise | Core-only golden fixture, artifact value test, optional risk modules |
| Templates duplicate observability platforms | Maintenance burden and noisy records | Stable links and fallback indexes, not runtime trace replication |
| Brownfield integration corrupts instructions | Agent behavior changes unexpectedly | Report and propose snippets; never auto-merge canonical files |
| Structural check implies compliance | False assurance | Restricted wording, explicit limitations, test forbidden claims |
| Stable IDs drift after release | Broken profiles and evidence chains | Schema versions, maintainer rules, compatibility tests |
| Cross-platform writes differ | Broken checksums or partial installs | UTF-8 and `\n`, `pathlib`, temporary-directory tests, atomic-write abstraction |
| Public template leaks originating context | Privacy and credibility failure | Clean-room content review and repository-wide forbidden-string checks |

## Verification gates

1. **Skeleton gate:** CLI help, imports, and tests work dependency-free.
2. **Intake gate:** deterministic recommendations and profile round trips.
3. **Planning gate:** complete dry-run with no target changes.
4. **Safety gate:** atomic install, idempotence, diffs, and conflict protection.
5. **Module gate:** selected-only generation and traceability links.
6. **Check gate:** precise read-only structural validation.
7. **Usability gate:** clean-room installation in under five minutes.
8. **Release gate:** every V1 success criterion mapped to test or review evidence.
9. **Local web gate:** browser and terminal routes produce the same validated profiles and plans; localhost
   security controls, stale-plan rejection, conflict approval, fallback behavior, and clean-room
   installation all pass without external resources.

Implementation does not advance past a gate while its acceptance checks fail.

## Phase 9: local web setup

### Outcome

Interactive users receive a calm, contextual local web wizard while the existing deterministic terminal
and non-interactive contracts remain available.

### Work

- Serve the self-contained A1b interface from an ephemeral loopback-only standard-library server.
- Keep quick profiles and custom assessment as alternative routes that converge on module review.
- Render the actual installation plan and text diffs from the existing planner.
- Require explicit approval for every modified or conflicting file and reject stale confirmations.
- Rebuild the confirmed plan before passing browser approvals to the atomic installer.
- Preserve terminal, no-browser, redirected-output, and non-interactive workflows.
- Verify HTTP boundaries, browser assets, CLI compatibility, clean-room installation, and structural checks.

### Checkpoint

The local server makes no external request, shuts down after confirmation or cancellation, and cannot
select a target path, module ID, profile field, or replacement outside Python's allowlisted plan.
