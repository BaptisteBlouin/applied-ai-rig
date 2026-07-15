# Contributing

Applied AI Rig is developed from the requirements in `docs/spec.md` and the dependency-ordered work in
`tasks/todo.md`.

Before proposing a change:

1. Explain the applied-AI engineering problem it solves.
2. Prefer a risk-triggered optional module over expanding the core.
3. Update the specification before changing stable IDs, schemas, generated paths, or conflict behavior.
4. Add a failing test before changing behavior.
5. Run `python -m unittest discover -s tests -v`.

Do not add providers, frameworks, telemetry, network access, or dependencies without prior discussion.
