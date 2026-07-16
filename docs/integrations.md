# Integration recipes

Applied AI Rig keeps decision-relevant safe references. It does not duplicate runtime traces or require a
provider SDK. Use stable identifiers in both the Rig and the canonical external system so a reviewer can
follow the relationship in either direction.

## Pull requests and issues

- Put the `DEC-...` identifier in the pull-request description for a consequential change.
- Link acceptance evidence by `EVD-...` identifier and name the canonical check, run, or report.
- Put the pull request, issue, or commit URL in the applicable register's external-reference or notes field.
- Do not paste secrets, private prompts, model responses, personal data, or unrestricted incident details
  into a public issue merely to make the chain self-contained.

## Experiment trackers

This recipe applies to tools such as MLflow, Weights & Biases, Langfuse, and other experiment or
observability systems without depending on their APIs.

| Rig field | Canonical-system value |
|---|---|
| `run_id` | Stable run or trace-group identifier |
| `decision_id` | Tag or metadata value copied from `DECISIONS.md` |
| `external_system_ref` | Durable URL or organization-approved reference to the run |
| `config_ref` | Versioned configuration or artifact reference rather than a copied secret |
| `evidence_id` | Claim record that interprets the run and states its limitations |

Keep detailed prompts, responses, samples, spans, and secondary metrics in the access-controlled canonical
system. The versioned CSV retains baselines, decision-relevant variants, regressions, and cited final runs.

## Billing and model usage

- Aggregate `api_usage.csv` at the run, release, workload, or billing-period grain.
- Record whether usage and cost are measured, billed, estimated, or unknown.
- Put the dated price source or billing-report reference in `pricing_snapshot` or a canonical reference.
- Reconcile retries, failed calls, embeddings, evaluation judges, and synthetic generation when they affect
  the decision.

Do not store account identifiers, credential values, private endpoints, or provider request IDs in the
repository.

## Operations and incidents

- Link `service_register.csv` to health dashboards, alerts, runbooks, release records, rollback procedures,
  and restore-test evidence using durable safe references.
- Keep `incident_register.csv` to one reviewable summary row per incident.
- Keep full timelines, logs, chat transcripts, and sensitive evidence in the incident system.
- Link the corrective decision and evidence back to the incident so a later operator can see why behavior
  changed.

## Runtime authorization

`action_register.csv` describes intended tool boundaries. Enforcement belongs in deterministic application
code or a runtime policy system. Link the policy, denial test, audit location, and kill-switch procedure;
never treat the static register as proof that authorization is enforced.
