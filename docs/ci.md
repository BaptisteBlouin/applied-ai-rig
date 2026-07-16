# Consumer CI check

The structural check can run in a consuming repository after installation. It verifies the manifest,
selected files, internal links, Markdown headings, CSV headers, and unresolved template placeholders. It
does not establish that the application is secure, compliant, production-ready, or technically correct.

## Composite GitHub Action

The repository includes a composite `action.yml`. It becomes consumable by external repositories after the
Applied AI Rig repository is public and a release tag exists.

```yaml
name: Applied AI Rig

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  check-rig:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - uses: BaptisteBlouin/applied-ai-rig@v0.2.0
        with:
          target: .
```

Pin a release tag rather than `main` so a consumer chooses when checker behavior changes. The action runs
the checked-out release's `init.py`; it does not install a dependency or send project content over the
network.

## Direct command

When the CLI is already available in CI, run:

```bash
applied-ai-rig --check .
```

Treat structural errors as a failed quality gate. Warnings mean a generated file differs from its original
template and should be reviewed before a future update; they do not fail the command.
