# Contributing

Applied AI Rig is developed from the requirements and dependency-ordered task history kept on the `v1`
branch for the original product and the `v2` branch for the adoption workflow. The `main` branch keeps the
reviewed production surface without internal implementation plans.

Start with the [roadmap](ROADMAP.md), current issues, and [worked examples](examples/README.md). Small
changes that solve a demonstrated applied-AI engineering problem are preferred over new abstractions or
broader governance scope.

Before proposing a change:

1. Explain the applied-AI engineering problem it solves.
2. Prefer a risk-triggered optional module over expanding the core.
3. Update the specification before changing stable IDs, schemas, generated paths, or conflict behavior.
4. Add a failing test before changing behavior.
5. Run the tests and quality gates: `python3 -m unittest discover -s tests -v`, `ruff check init.py
   applied_ai_rig tests tools`, and `mypy` (install the tools with `pip install -e ".[dev]"`).

For behavior changes, add a failing test first and show the red-to-green result. For templates and user
guidance, add a focused content or worked-example test when the promise is important enough to preserve.
Keep pull requests scoped, describe compatibility effects, and update the changelog for user-visible
changes.

Do not add providers, frameworks, telemetry, network access, or runtime dependencies without prior
discussion. `ruff`, `mypy`, and `packaging` are development-only tools, not runtime dependencies.

By participating, contributors agree to follow the [code of conduct](CODE_OF_CONDUCT.md). Security reports
must follow [SECURITY.md](SECURITY.md), not a public issue.
