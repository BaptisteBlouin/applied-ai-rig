# Local Web Wizard Implementation Checklist

## 1. Preserve the current behavior

- [ ] Add characterization tests for quick profiles, custom recommendations, existing-profile reuse,
  module ordering, declined recommendations, real plans, diffs, conflict cancellation, and exit codes.
- [ ] Extract interaction-independent profile construction from `cli.py` without changing serialized profiles.
- [ ] Keep the terminal wizard callable as a standalone interaction adapter.
- [ ] Run the current unit suite and standard-library compilation before introducing the server.

## 2. Build the application layer

- [ ] Add a web-wizard session state machine with quick, custom, module-review, plan-review, approval,
  installed, cancelled, and expired states.
- [ ] Serialize canonical profiles, questions, module information, and existing-profile context from Python.
- [ ] Validate complete custom answer maps and call `recommend_modules()` in Python.
- [ ] Validate selected modules and construct `Profile` with canonical selected and declined ordering.
- [ ] Load validated manifest checksums and call `build_plan()`.
- [ ] Serialize every real plan row, status, manual integration, and safe summary.
- [ ] Serve requested diffs through `unified_diff()` using opaque plan-row identifiers.
- [ ] Fingerprint plans and reject stale approvals after any profile, selection, or filesystem change.
- [ ] Translate validated per-file approvals into the existing `install_plan()` approver.
- [ ] Guarantee one final install call and safe cancellation on every earlier exit.

## 3. Implement the hardened local server

- [ ] Bind `ThreadingHTTPServer` to `127.0.0.1` and port `0` only.
- [ ] Generate a per-session `secrets` token and keep it out of logs and storage.
- [ ] Require the token, exact loopback `Host`, and exact same-origin `Origin` on API mutations.
- [ ] Disable CORS and cookies.
- [ ] Add CSP, no-sniff, no-referrer, same-origin resource policy, and no-store headers.
- [ ] Allow only fixed static routes and explicit JSON API routes.
- [ ] Enforce content type, URL/header/body/count limits, timeouts, and structured safe errors.
- [ ] Reject unsupported methods, arbitrary paths, unknown JSON keys, and invalid state transitions.
- [ ] Lock session mutations and make duplicate/concurrent install requests harmless.
- [ ] Shut down and clear session data after success, cancellation, timeout, or interruption.

## 4. Convert A1b into production assets

- [ ] Split the prototype into CSP-compatible HTML, CSS, and JavaScript assets with no inline code.
- [ ] Remove hard-coded profiles, questions, recommendations, modules, and illustrative plan rows.
- [ ] Populate all product data and plan results from validated API responses.
- [ ] Preserve the A1b palette, spacing correction, contextual inspector, and quiet visual hierarchy.
- [ ] Implement the three-step quick route and four-step custom route with dynamic numbering.
- [ ] Add existing-profile summary and keep/reassess choices.
- [ ] Display real status counts, paths, manual integrations, and lazily loaded real diffs.
- [ ] Require complete-plan confirmation and explicit modified/conflict approvals.
- [ ] Add loading, validation, cancellation, stale-plan, expired-session, install-failure, and success states.
- [ ] Complete keyboard, focus, screen-reader, mobile, contrast, and reduced-motion behavior.

## 5. Integrate the CLI

- [ ] Add `--terminal` and `--no-browser` with clear mutual-exclusion validation.
- [ ] Make the web wizard the default only for interactive installation paths.
- [ ] Keep `--check`, `--list-modules`, `--explain`, `--modules --non-interactive`, and
  `--profile --non-interactive` server-free and behavior-compatible.
- [ ] Preserve interactive `--profile` as a shortcut to web module review.
- [ ] Make web `--dry-run` structurally incapable of installing.
- [ ] Open the tokenized local URL only after binding; print it for `--no-browser` or launch failure.
- [ ] Report bind failure with an actionable `--terminal` fallback.
- [ ] Preserve cancellation and conflict exit codes and ensure Ctrl-C writes nothing.

## 6. Verify behavior and security

- [ ] Unit-test the state machine, validation, profile construction, plan fingerprints, approvals, and
  cancellation.
- [ ] Integration-test HTTP routes with `http.client` and temporary target directories.
- [ ] Test token, Host, Origin, content type, method, route, body-limit, unknown-field, and traversal rejection.
- [ ] Test quick, custom, existing-profile, dry-run, conflict, cancellation, stale-plan, timeout, and success
  flows end to end.
- [ ] Test concurrent and repeated install requests for at-most-once behavior.
- [ ] Assert all served assets are offline, fixed-path, and compatible with the restrictive CSP.
- [ ] Re-run installer rollback, idempotency, manifest, checksum, checker, and Windows-path tests unchanged.
- [ ] Manually verify browser launch, no-browser, terminal fallback, keyboard use, mobile layout, and shutdown
  on Linux, macOS, and Windows.

## 7. Update canonical documentation

- [ ] Update `README.md` quick start, command examples, interaction modes, and security summary.
- [ ] Update `docs/spec.md` with the local web flow and unchanged installation guarantees.
- [ ] Update `docs/verification.md` with automated evidence and clean-room walkthroughs.
- [ ] Update `tasks/plan.md` and `tasks/todo.md` rather than leaving the design checklist as the release record.
- [ ] Update `--help` text for browser, terminal, dry-run, and non-interactive behavior.
- [ ] Record any schema or public CLI decision in the canonical decision documentation if implementation
  requires a compatibility change.

## Definition of done

- [ ] The default interactive command opens A1b as a temporary offline loopback application.
- [ ] Quick and custom routes match the documented three-step and four-step flows.
- [ ] Every recommendation, profile, plan row, status, and diff comes from Python domain logic.
- [ ] No project write is possible before validated final confirmation and conflict approvals.
- [ ] Atomic installation, rollback, idempotency, checksum, and non-interactive guarantees are preserved.
- [ ] Terminal and automation fallbacks remain fully functional.
- [ ] The complete test matrix and documented clean-room verification pass.

