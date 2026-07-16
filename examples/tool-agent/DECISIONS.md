# Decisions

## DEC-20260711-email-approval — Require approval before sending external email

- **Decision ID:** DEC-20260711-email-approval
- **Status:** accepted
- **Context:** Drafting is reversible but sending a message is an externally visible side effect.
- **Options:** Allow autonomous sends; require approval for every send; disable sending and allow drafts only.
- **Decision:** Allow drafts automatically and require a named human approval for the exact recipient and body before every send.
- **Consequences:** Response time includes a human step and unattended workflows stop at the approval boundary.
- **Revision threshold:** Revisit only after an approved risk review and a measured false-send rate of zero over a representative staged trial.
- **Supersedes:** None
- **Evidence:** EVD-20260711-denial-tests
