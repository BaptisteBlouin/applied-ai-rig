# Contributing

Applied AI Rig is developed from the requirements in `docs/spec.md` and the dependency-ordered work in
`tasks/todo.md`.

Before proposing a change:

1. Explain the applied-AI engineering problem it solves.
2. Prefer a risk-triggered optional module over expanding the core.
3. Update the specification before changing stable IDs, schemas, generated paths, or conflict behavior.
4. Add a failing test before changing behavior.
5. Run the tests and quality gates: `python -m unittest discover -s tests -v`, `ruff check init.py
   applied_ai_rig tests`, and `mypy` (install the tools with `pip install -e ".[dev]"`).

Do not add providers, frameworks, telemetry, network access, or runtime dependencies without prior
discussion. `ruff` and `mypy` are development-only tools, not runtime dependencies.
