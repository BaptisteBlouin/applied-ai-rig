# Versioning and migrations

Applied AI Rig versions three related contracts separately.

## Package version

The Python package follows semantic versioning. Before `1.0.0`, a minor release may add or revise CLI
behavior and generated guidance. Patch releases fix behavior without intentionally changing stable schemas
or generated paths.

## Profile and manifest schema version

`.applied-ai-rig/profile.json` and `.applied-ai-rig/manifest.json` have their own integer
`schema_version`. Package `0.2.0` continues to read and write schema version 1. The machine-readable
contracts are in [`schemas/profile.schema.json`](../schemas/profile.schema.json) and
[`schemas/manifest.schema.json`](../schemas/manifest.schema.json).

A future schema version must include an explicit migration path, tests for the previous supported version,
and a dry-run preview before any project metadata is changed. A package-version change alone never implies
that a profile or manifest schema changed.

## Generated artifacts

Generated paths, register headers, stable module IDs, and conflict behavior are public contracts. A release
that changes them must document the compatibility impact and update procedure in the changelog. Re-running
the initializer classifies unchanged, locally modified, and conflicting files and never replaces a local
change without explicit approval.

The manifest stores original template checksums, not ownership of the user's later content. A migration or
removal procedure must never delete a path only because it appears in the manifest.

## Release preparation

Before a release:

1. Update the version and changelog.
2. Run tests, compilation, Ruff, and strict Mypy on supported Python versions.
3. Build the package and inspect its templates, web asset, schemas, and command entry point.
4. Test fresh installation, re-run, conflict, status, record preview, record append, and structural check.
5. Tag the reviewed commit and pin consumer documentation to that tag.

Publishing a package or tag is deliberately separate from merging implementation work.
The exact Trusted Publishing setup, release procedure, failure handling, and non-destructive rollback are
documented in the [release runbook](releasing.md).
