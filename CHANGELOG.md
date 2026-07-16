# Changelog

All notable changes to Applied AI Rig are recorded here. Dates are added when a release is published.

## [0.2.0] - Unreleased

### Added

- Safe `status`, `add decision`, `add evidence`, and `add experiment` workflows.
- Default record previews, explicit `--yes` writes, duplicate-ID protection, and atomic appends.
- First-fifteen-minute guidance and progressive register completion without changing CSV headers.
- Filled RAG, tool-agent, and production-service examples.
- Composite structural-check action, integration recipes, JSON schemas, and community templates.

### Changed

- The README now leads with the engineering problem and a decision-to-evidence example.
- Linux and macOS source commands use `python3` in user-facing documentation.
- Successful installation prints exact status and first-decision commands.

### Compatibility

- Profile and manifest schema version remains 1.
- V1 module IDs, generated paths, register headers, conflict behavior, and offline operation remain stable.

## [0.1.0] - Unreleased

- Initial modular engineering record, guided setup, safe installer, structural checker, and five risk modules.
