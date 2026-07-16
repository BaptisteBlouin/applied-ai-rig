# Evidence

## EVD-20260711-denial-tests — Unapproved sends are denied in staged tests

- **Evidence ID:** EVD-20260711-denial-tests
- **Claim:** The deterministic mail tool denies staged send attempts without a current approval bound to the exact arguments.
- **Status:** measured
- **Source:** TEST-email-denial-20260711 in the access-controlled CI report.
- **Scope:** Nominal send, changed recipient, changed body, expired approval, duplicate call, and injected document cases.
- **Limitations:** Does not prove the email provider or identity system is unavailable to other code paths.
- **Related decisions:** DEC-20260711-email-approval
