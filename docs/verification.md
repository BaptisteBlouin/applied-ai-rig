# V2 verification record

This internal record captures the red-to-green evidence for the V2 work. It is
kept on the `v2` branch with the implementation specification and plan; it is
not part of the public-facing project surface on `main`.

## Initial red phase

The focused tests failed before implementation for the expected missing
capabilities:

- `tests.test_records` could not import `applied_ai_rig.records`.
- The CLI rejected the new `status` and `add` commands.
- Successful installation output did not contain an exact next step.
- Generated module documentation did not identify the minimum useful fields.
- The worked-example tests failed because `examples/` did not exist.
- Project-surface tests failed because the reusable action, schemas, integration
  documentation, and community files did not exist.

## Review regression red phase

Regression tests reproduced every behavioural issue found during the first
standards/specification review:

- `add decision --status accepted` incorrectly succeeded.
- A legacy project target named `status` was parsed as the workflow command and
  exited with code 2.
- `status` on a partially damaged project aborted instead of reporting an
  unhealthy state.
- Bare `status` outside an installed project fell back to the installer instead
  of returning an actionable read-only error.
- A readable profile with a missing manifest was reported as `core only` with
  zero counters instead of recovering the still-readable modules and records.
- Schema assertions exposed missing overlap and compatibility constraints.

## Green phase

The final V2 tree passed:

- `python3 -m unittest discover -s tests -v`: 110 tests, 6.303 seconds, `OK`.
- `python3 -m compileall -q init.py applied_ai_rig tests`: success.
- `ruff check init.py applied_ai_rig tests`: all checks passed.
- `mypy`: success across the 9 configured source files, including `init.py`.
- JSON schema syntax and behaviour checks, including profile overlap rejection
  and legacy manifest compatibility.
- YAML parsing for the composite action and issue forms.
- Wheel build and content inspection for version `0.2.0`, including the CLI,
  record workflow, templates, and web assets.
- Installed end-to-end smoke test in a clean temporary target: install, add a
  decision, add evidence, add an experiment, report status, and run the
  structural check successfully.

The smoke check produced three expected template-drift warnings after the test
intentionally edited generated project records.
