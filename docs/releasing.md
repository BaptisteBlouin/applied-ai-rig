# Release and rollback runbook

Publishing is intentionally separate from merging. A GitHub Release triggers the dedicated workflow,
which rebuilds and verifies the tagged source before the protected `pypi` environment can publish it. The
publish job uses PyPI Trusted Publishing; do not create a `PYPI_TOKEN` repository or environment secret.

## One-time setup

Complete these settings only when the project is ready for its first package release:

1. In GitHub, create an environment named `pypi`. Restrict deployments to version tags such as `v*` and,
   when the repository plan and visibility support it, add a required reviewer and prevent self-review.
   Do not store a PyPI credential in the environment.
2. On PyPI, register a pending Trusted Publisher for project `applied-ai-rig` with owner
   and repository `BaptisteBlouin/applied-ai-rig`, workflow `.github/workflows/release.yml`, and environment
   `pypi`. A pending publisher does not reserve the package name until the first successful upload.
3. Protect matching release tags in GitHub and require the normal CI and `Security / Secret history /
   Gitleaks` checks on `main` before a release is created.

The PyPI publisher identity must match all four configured values exactly. The environment is part of the
OIDC identity even though it contains no publishing secret.

## Before publishing

1. Finish pilot feedback and the public-release gate in the roadmap.
2. Set the package version, replace `Unreleased` with the release date in the changelog, and ensure the tag
   will be exactly `v<package-version>`.
3. Review the complete diff, confirm CI is green on the commit, and run a local history scan from a full
   clone with a checksum-verified Gitleaks binary:

   ```bash
   gitleaks git . --log-opts=--all --redact
   ```

4. Install the fixed tool versions with `python -m pip install -r requirements/release.txt`, build with
   `python -m build --no-isolation`, run `python -m twine check --strict dist/*`, then run
   `python tools/verify_package.py dist` for distribution inspection and a clean-environment smoke test.
5. Create the version tag and publish a GitHub Release only after the reviewed commit is final. Creating a
   draft release is safe: the workflow listens only for the `published` event.

The workflow checks out the release tag, requires it to equal `v{version}`, reruns the tests, compilation,
Ruff, Mypy, build, distribution inspection, metadata check, and installed-wheel workflow smoke test, then
uploads one artifact. The separate publish job downloads that artifact and uses only `id-token: write` plus
the official PyPA publishing action. Trusted Publishing creates a short-lived credential and the action
produces PyPI attestations by default.

The security workflow runs the explicit full-history command on every push to `main`, every pull request,
each scheduled run, and every manual run. Its Gitleaks v8.30.1 Linux archive and SHA-256 are fixed together;
update and verify both values when upgrading the scanner.

## If publishing fails

- If no file reached PyPI, correct infrastructure or Trusted Publisher configuration and rerun the failed
  workflow for the unchanged tag. Do not move the tag to different source.
- If any file reached PyPI, never reuse or overwrite that version. Finish the incident assessment and
  publish a corrected patch version with a new tag and GitHub Release.
- A mismatch between the publisher owner, repository, workflow filename, or environment must be corrected
  on PyPI or GitHub before retrying. Do not work around OIDC with a long-lived API token.

## Rollback after publication

PyPI publication is not a reversible deployment. For a broken, incompatible, or vulnerable release, yank
the entire release from its PyPI release-management page and record a clear reason. Yanking is preferred to
deletion because it preserves provenance and exact pins can still resolve with a warning. Then publish a
fixed patch release; never reuse the affected version.

Update the GitHub Release with the impact and replacement version, but retain the tag and evidence needed
for investigation. Delete a PyPI release only for exceptional cases after assessing downstream breakage;
deletion is permanent and disruptive.

If a real secret is found anywhere in Git history, revoke and rotate it first. Removing the current line is
not remediation: coordinate any history rewrite separately, notify affected users, and rerun the complete
history scan before releasing.

## Sources

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [PyPI Trusted Publisher security model](https://docs.pypi.org/trusted-publishers/security-model/)
- [PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [PyPI yanking](https://docs.pypi.org/project-management/yanking/)
- [GitHub secure use of Actions](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub deployment environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Gitleaks Git scanner](https://github.com/gitleaks/gitleaks)
