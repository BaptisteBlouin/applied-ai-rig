# Private pilot playbook

This playbook prepares a cohort of five genuine external pilots. It is a procedure for collecting useful
evidence before a public release; it is not evidence that any pilot has already happened.

## Evidence boundary

A genuine external pilot is run by a person who did not build Applied AI Rig, on an active applied-AI
project they own or maintain, using a real decision from that project. Use five different projects and
pre-register the cohort as `P01` through `P05` before the first session. Do not replace an unsuccessful
participant to improve the result.

Maintainer dry runs, automated tests, demonstrations, friends following coached steps, and sessions on the
repository's three example projects are rehearsals. Rehearsals are not external evidence. Label them as
such and never include them in pilot adoption totals.

## Recruit and invite

Recruit maintainers who have Python 3.10 or later, an active application using models, data, evaluations,
tools, or production AI services, and a project decision they can safely document. Aim for different
project shapes rather than five users from the same team. Participation is voluntary; a participant may
skip a question or withdraw at any time. If compensation is offered, do not make it conditional on
finishing, meeting a timing target, or giving positive feedback.

Use a short invitation such as:

> We are privately testing Applied AI Rig, an offline tool for keeping AI engineering decisions and safe
> evidence in a repository. The session takes about 30 minutes, followed by one question two weeks later.
> You will use a disposable branch or copy of your own project and keep its contents. We collect only
> timings, completion states, and your sanitized feedback—no source code, prompts, responses, credentials,
> or telemetry. Participation is optional and you can stop or withdraw your feedback at any time. Would
> you like to take part?

Before scheduling, confirm that the participant understands the purpose, the data boundary, and the later
follow-up; ask for explicit consent again before starting the timer. Assign only the pseudonymous pilot ID
to the result sheet. If they withdraw, stop, delete their row and notes, and report only one anonymous
`withdrawn` cohort slot. Do not recruit a replacement; a withdrawal therefore leads to **Hold**.

## Safe setup

1. Give the participant time-limited access to the private repository or a maintainer-provided source
   archive, plus the normal README. Do not send credentials in chat or put access tokens in commands.
2. Ask them to use a disposable branch or local copy of their real project, not a production working tree.
   Their decision should be real, but its wording may be locally sanitized.
3. Ask them to remove or replace secrets, personal data, prompts, responses, private endpoints, customer
   names, and confidential identifiers before showing any screen or excerpt.
4. Let the participant choose a documented setup path. The facilitator may observe and take timings, but
   should not operate the terminal or explain a step until the participant declares that they are stuck.
   Record each intervention as friction.
5. Finish by removing temporary repository access if applicable. The pilot keeps or deletes the generated
   files; Applied AI Rig sends nothing back.

No telemetry is added or enabled for the pilot. The participant can run offline after obtaining the source,
and the maintainer never needs a copy of the generated Rig.

## Measure one session

Use a monotonic stopwatch and record whole seconds. Keep the raw five rows so the cohort can be audited;
do not record project names. Do not discard failed or abandoned attempts, except to honor a withdrawal.
Mark an unfinished measure `not completed`, retain the elapsed time at the stop, and record the blocker.

### Installation elapsed time

- Start immediately before the participant runs their chosen documented installation command. Package
  installation, prompts, reading during the flow, corrections, and retries are included.
- Stop when the Rig has been written to the target and `python3 init.py --check <target>` (or the equivalent
  installed command) first succeeds.
- The pilot-level target is less than 300 seconds. Record `installation_seconds`, completion state, setup
  path, operating system, Python version, and every facilitator intervention.

### First-real-record elapsed time

- Start at the installation stop, without resetting the project or pre-writing content for the participant.
- Stop when the participant saves a project-specific decision with a stable ID and meaningfully completes
  its context, real options, selected or proposed decision, consequences, and revision threshold. A blank
  template, generated skeleton, or example copy does not count.
- The pilot-level target is less than 900 seconds. Record `record_seconds`, completion state, whether the
  CLI or manual editing was used, and the first point of confusion.

### Later pull-request update

Fourteen calendar days after the session, ask once whether the participant added or changed any Rig record
in a later pull request motivated by normal project work. Record `yes`, `no`, or `not observed`; do not ask
for a repository URL or private diff. A follow-up PR created only to satisfy the pilot does not count. The
adoption target is at least three of five pilots with `yes`. Record `followup_elapsed_days` as a whole
number; a `yes` counts toward that target only when the follow-up happened at least 14 days after the timed
session.

For every pilot, retain only this sanitized row:

| Field | Allowed value |
|---|---|
| Pilot | `P01`–`P05` |
| Kind | `external` or `rehearsal` |
| Environment | OS, Python version, setup path |
| Installation | seconds or `not completed`, plus safe blocker |
| First real record | seconds or `not completed`, plus editing path |
| Follow-up interval | whole elapsed days; at least `14` for an adoption `yes` to count |
| Later update | `yes`, `no`, or `not observed` |
| Feedback | safe themes, unused guidance, and suggested simplification |

## Structured feedback

Immediately after the timed session, ask the same questions in the same order:

1. What were you trying to record, in generic terms?
2. At which step did you first hesitate or need help?
3. Which generated guidance or field did you leave unused, and why?
4. What felt duplicated, too heavy, or missing?
5. Could a teammate understand when this decision should be revisited?
6. Would you use the Rig for the next consequential AI change? Why or why not?

The participant or facilitator may submit the sanitized answers through the
[pilot feedback issue form](../.github/ISSUE_TEMPLATE/pilot_feedback.yml). Treat a private GitHub issue as
potentially public later: use only the pilot ID and safe summaries. Keep observations separate from
interpretation, then group repeated friction only after all five sessions.

## Privacy and retention

Do not collect private project content: source code, generated records, repository URLs, decision text,
prompts, responses, model inputs or outputs, datasets, secrets, personal data, private endpoints, account
IDs, screenshots, or recordings. Do not paste terminal output unless the participant has sanitized it. The
participant owns all project content and can request deletion of their feedback.

Store the five sanitized rows and issue references in a maintainer-controlled private location. Publish
only aggregate timings, completion counts, recurring themes, and changes made in response. Delete raw
session notes after the release decision or within 30 days of the final follow-up, whichever comes first;
retain a deletion request only as a count, not an identity.

## Go or Hold

Make the decision only after the fourteen-day follow-up for all five pre-registered external pilots.

**Go** when all five completed installation and a first real record, median installation time is under five
minutes, median first-real-record time is under fifteen minutes, at least three of five pilots have a Later
pull-request update of `yes`, there is no unresolved safety or privacy issue, and recurring confusion has
either been simplified or explicitly accepted with a reason. Report the two medians, the number meeting
each pilot-level timing target, completion totals, adoption total, and safe themes.

**Hold** when fewer than five genuine external pilots were observed, any completion or cohort threshold is
missed, facilitator help is routinely required, a privacy or safety concern remains, or recurring confusion
has not been addressed. Fix the smallest demonstrated barrier and run a new pre-registered cohort. Keep the
earlier result as evidence and do not relabel rehearsals or omit unsuccessful attempts.
