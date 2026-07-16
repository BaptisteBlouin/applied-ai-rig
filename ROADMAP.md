# Roadmap

The roadmap is evidence-driven. New modules are not added merely because a domain is adjacent to applied
AI engineering.

## Current: prove the V2 adoption workflow

- Exercise installation and first-record creation with at least five external pilot projects.
- Target median installation under five minutes and a first real record within fifteen minutes.
- Observe whether at least three pilots update the record in a later pull request.
- Remove or simplify guidance that pilots consistently leave unused or misunderstand.

## Public-release gate

- All tests, compilation, Ruff, and strict Mypy pass on supported Python versions.
- Fresh install, safe re-run, conflict review, status, record append, and structural check are exercised on
  Linux, macOS, and Windows.
- Repository visibility, vulnerability reporting, discussions, package publishing, and release notes are
  enabled intentionally by the maintainer.
- Published commands reference a real immutable tag and package version.

## Later candidates

- More record helpers only when manual editing is a demonstrated recurring barrier.
- Import/export adapters only when stable references are insufficient for several real users.
- A new module only when a distinct risk cannot be composed from the existing five modules.

## Explicit non-roadmap

There is no planned SaaS dashboard, runtime trace store, provider abstraction, secrets vault, coding-agent
orchestrator, compliance certification, or remote module marketplace. Purpose-built canonical systems
should continue to own those responsibilities.
