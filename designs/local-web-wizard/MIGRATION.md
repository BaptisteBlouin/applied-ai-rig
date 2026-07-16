# Local Web Wizard Migration

## Decision

Promote `design-a1b-context-inspector.html` from an illustrative prototype to the default interactive
experience for `python init.py <target>`. Keep the existing terminal wizard as an explicit fallback and keep
all non-interactive commands deterministic.

The browser is a presentation layer. The existing Python domain objects and installer remain authoritative:

- `intake.py` owns profiles, questions, module descriptions, and recommendations;
- `manifest.py` owns profile and manifest validation;
- `installer.py` owns file classification, real plans, unified diffs, approvals, staging, and rollback;
- `checker.py` continues to own structural validation;
- `cli.py` selects the interaction mode and reports the final result.

No profile, recommendation, file status, diff, or install result may be computed independently in JavaScript.

## User flows

### Quick profile

```text
Starting point -> Review modules -> Review plan -> Confirm conflicts -> Install result
```

`minimal`, `api-rag`, `agent`, and `production` provide initial module selections without inventing project
answers. The user may add or remove any optional module before planning.

### Custom assessment

```text
Starting point -> Custom assessment -> Review modules -> Review plan -> Confirm conflicts -> Install result
```

All six questions must have an explicit Boolean answer. Python calls `recommend_modules()` and returns both
the recommended modules and their reasons. The user may then add or decline modules explicitly.

### Existing project

The opening screen summarizes the validated existing profile. It offers the same choices as the terminal
wizard: keep the current answers and module selection, choose a quick profile, or run the custom assessment.
Existing answers are prefilled only when entering the custom route.

### Preview and installation

The review screen displays the actual `InstallationPlan`, never illustrative rows. It includes:

- the resolved target and selected modules;
- every planned relative path and its `NEW`, `UNCHANGED`, `MODIFIED`, or `CONFLICT` status;
- manual integration notices;
- a server-produced unified diff for each modified or conflicting UTF-8 file;
- the existing non-text-diff message for binary or non-UTF-8 content;
- explicit approval state for every modified or conflicting path.

The first confirmation approves the complete plan. A second, conflict-specific confirmation is required for
every `MODIFIED` or `CONFLICT` file, with an explicit approve-all action. Rejecting one required replacement
cancels the complete installation; it does not perform a partial install. The browser must state this before
collecting approvals.

`--dry-run` may use the browser to display the real plan and diffs, but its final action is **Close preview**;
the server exposes no install transition for that session.

## CLI behavior

The intended interface is:

```bash
python init.py <target>                  # local web wizard when a browser can be opened
python init.py <target> --terminal       # existing terminal wizard
python init.py <target> --no-browser     # local web wizard; print the local URL
python init.py <target> --dry-run        # preview only
python init.py <target> --non-interactive --modules data,evaluation
```

`--check`, `--list-modules`, `--explain`, and every `--non-interactive` invocation bypass the web server.
`--profile` remains a named starting point: interactively it opens directly at module review; with
`--non-interactive` it preserves the current exact behavior. `--modules` remains the precise automation
interface. `--terminal` and `--no-browser` are mutually exclusive.

If the browser cannot be opened, print the loopback URL and keep the server available rather than silently
changing interaction semantics. If the server cannot bind, report the error and tell the user to retry with
`--terminal`. EOF, Ctrl-C, browser cancellation, and timeout must return the established cancellation exit
code and write nothing.

## Python architecture

Add a small web package rather than expanding `cli.py`:

```text
applied_ai_rig/web_wizard/
├── __init__.py
├── application.py     # session state and domain-service calls
├── server.py          # ThreadingHTTPServer and hardened request handler
└── static/
    ├── index.html
    ├── wizard.css
    └── wizard.js
```

The static files are derived from A1b, retain its visual system and contextual inspector, and contain no
hard-coded product records. Bootstrap data comes from Python. The application layer exposes typed internal
operations that can be tested without sockets:

- create a session snapshot from the target and optional existing profile;
- select a quick profile;
- validate custom answers and compute recommendations;
- validate final module selection and construct a `Profile`;
- load trusted checksums and build a real plan;
- serialize plan summaries and requested diffs;
- validate approvals and invoke `install_plan()` once;
- cancel or expire the session.

Keep one mutable session per process. Use a lock around every state transition and installation. The state
machine rejects skipped, repeated, stale, or out-of-order transitions. Building a new plan invalidates all
previous plan identifiers, diffs, and approvals.

Before installation, rebuild the plan from current disk state and compare a server-generated plan fingerprint
covering the profile, paths, statuses, checksums, and known checksums. If anything changed after preview,
invalidate approvals and return to review with a clear stale-plan message.

## HTTP contract

Use JSON only for dynamic operations and serve fixed static assets with exact paths.

```text
GET  /                         static shell
GET  /assets/wizard.css       fixed stylesheet
GET  /assets/wizard.js        fixed script
GET  /api/bootstrap           canonical profiles, questions, modules, existing profile, session state
POST /api/assessment          validated complete answer map -> recommendations
POST /api/plan                route, answers, selected module IDs -> real plan summary and plan ID
GET  /api/plan/<id>/diff/<n>  server-selected diff by opaque row index
POST /api/install             plan ID, complete-plan confirmation, per-file approvals -> result
POST /api/cancel              terminate without writes
```

Exact endpoint names may change during implementation, but the following rules are mandatory:

- accept only `application/json` for POST requests;
- enforce a small request-body limit before reading the body;
- reject malformed JSON, unknown keys, wrong types, duplicate or unknown module IDs, unknown question IDs,
  incomplete custom answers, invalid route names, invalid plan IDs, and invalid approval paths;
- never accept a target path, template path, destination path, diff path, timestamp, checksum, status,
  recommendation reason, or generated content from the browser;
- derive declined modules as recommended modules that are not selected;
- preserve canonical `MODULE_IDS` ordering in profiles and responses;
- return structured errors with a stable code and safe user-facing message, without tracebacks or local file
  contents;
- apply `Cache-Control: no-store` to HTML and API responses.

## Localhost security boundary

The server is offline and session-scoped, but a hostile webpage in another browser tab is still in scope.

- Bind only to `127.0.0.1` on an operating-system-assigned port. Do not bind to `0.0.0.0`, `::`, or a fixed
  port.
- Generate a high-entropy session token with `secrets`. Put it in the URL fragment used by the client, not
  in normal request logs or generated files. Require it in a custom header for every API request.
- Require an exact `Host` value matching the selected loopback host and port.
- For mutating requests, require an exact `Origin` matching the generated local origin. Reject absent,
  `null`, cross-origin, and unexpected origins.
- Do not enable CORS. Do not use cookies. Do not persist the token in local storage or session storage.
- Send a restrictive CSP such as `default-src 'none'; script-src 'self'; style-src 'self'; connect-src
  'self'; img-src 'self'; font-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`.
  Keep scripts and styles external so `unsafe-inline` is unnecessary.
- Send `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and `Cross-Origin-Resource-Policy:
  same-origin`. Use explicit content types and `charset=utf-8`.
- Support only `GET`, `HEAD`, and `POST`; return `405` for every other method. Do not expose directory
  listings, arbitrary filesystem reads, redirects supplied by the client, uploads, or file URLs.
- Cap URL length, header count/size where practical, JSON body size, answer/module counts, and concurrent
  requests. Use socket and session deadlines.
- Shut down after success, explicit cancellation, parent interruption, or an inactivity timeout. Clear the
  token and in-memory plan on shutdown.
- Open the browser only after the server is listening. Quote no shell command; use `webbrowser.open()`.

The interface must continue to remind users that no secret, prompt, response, sensitive payload, or private
endpoint should be entered. The assessment accepts Booleans only.

## Installation semantics

The web path must not weaken existing guarantees:

1. Parse and validate any existing profile and manifest before starting.
2. Read known checksums only from the validated manifest.
3. Construct `Profile` through its existing validator.
4. Call `build_plan()` with the same template root and checksums as the CLI.
5. Display all files and real diffs before accepting the complete-plan confirmation.
6. Convert validated browser approvals into an approver callable keyed only by planned relative paths.
7. Call `install_plan()` once with the server-generated UTC timestamp.
8. Preserve its staging, replacement, rollback, manifest, and idempotency behavior.
9. Return success only after installation completes; on failure, show a safe error and retain no false
   success state.

No endpoint may write project files before the final install transition. Static extraction, caches, logs,
or session state must not be written into the target.

## Accessibility and interaction

Retain the A1b contextual inspector, corrected title/description spacing, calm visual hierarchy, responsive
layout, and reduced-motion support. Add:

- semantic headings, fieldsets, legends, tables, buttons, and status regions;
- complete keyboard operation and visible focus;
- inspector updates on hover, focus, and selection without making hover the only source of information;
- inline explanations on narrow screens;
- clear status text in addition to color;
- focus placement on validation errors and route changes;
- confirmation labels that name the effect and target;
- a disconnected/expired-session state that never implies installation succeeded.

## Test strategy

Use `unittest` and the standard library only.

### Domain and application tests

- quick profiles produce the existing selections and no factual answers;
- custom assessment requires all canonical questions and returns canonical recommendation reasons;
- module review records selected and declined recommendations in canonical order;
- existing profiles are summarized, retained, or reassessed correctly;
- plan serialization matches `build_plan()` statuses and manual integrations;
- diff responses equal `unified_diff()` output;
- stale plan fingerprints invalidate approvals;
- cancellation, rejected replacement, dry-run, timeout, and repeated install write nothing;
- install calls preserve atomic rollback and idempotent reruns.

### HTTP tests

Start the server on loopback with a temporary target and exercise it through `http.client`:

- static shell and assets have correct types, CSP, security headers, and no external references;
- token, Host, Origin, method, route, content type, body limit, JSON schema, and state-transition checks reject
  invalid requests;
- unknown paths cannot read files and query/path values cannot select a destination or diff file;
- a complete quick route and custom route reach the real plan;
- approved installation succeeds and shuts down;
- cancellation and expiry shut down without writes;
- concurrent or duplicate installation requests result in at most one install.

### CLI tests

- default interactive mode launches the web runner with the resolved target;
- `--terminal` uses the existing prompt flow;
- `--no-browser` prints a usable loopback URL without invoking `webbrowser.open()`;
- `--check`, metadata commands, and non-interactive commands never start a server;
- option conflicts and bind/browser failures have stable exit behavior;
- `--dry-run` cannot transition to installation.

### Browser asset tests

Without introducing a browser dependency, verify that required landmarks, labels, step names, asset paths,
and CSP-compatible markup exist; compile JavaScript with an available runtime only as an optional developer
check. The primary contract remains Python integration tests plus a documented manual Linux, macOS, and
Windows walkthrough for keyboard, responsive layout, browser launch, no-browser mode, and shutdown.

## Documentation and release gates

Update `README.md`, `docs/spec.md`, `docs/verification.md`, command help, and the canonical task files when
the implementation lands. Document that the server is loopback-only, offline, temporary, dependency-free,
and not a remotely hosted application. Document `--terminal`, `--no-browser`, timeout/cancellation behavior,
and the exact fallback instructions.

Before release:

- all existing tests continue to pass;
- new application, HTTP, CLI, and security tests pass on Python 3.10 and 3.13 across Linux, macOS, and
  Windows;
- standard-library compilation passes;
- clean-room quick, custom, existing-project, dry-run, conflict, cancellation, and no-browser walkthroughs
  pass;
- `--check` reports zero errors and warnings after a full-module install;
- the repository and served assets contain no external dependency, CDN, telemetry, or network call;
- the generated file set and schemas remain backward compatible unless separately specified.

