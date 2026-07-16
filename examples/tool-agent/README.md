# Tool agent: approval before external email

This synthetic example shows how a team records a side-effect boundary for an agent that can draft and send
support email. No real recipient, message, credential, or provider request identifier is included.

## Decision -> Evidence

1. [DEC-20260711-email-approval](DECISIONS.md) defines the approval boundary.
2. [EVD-20260711-denial-tests](EVIDENCE.md) records the tested claim and limitations.
3. [action_register.csv](action_register.csv) describes deterministic authorization and recovery controls.
4. [misuse_cases.csv](misuse_cases.csv) preserves the representative prompt-injection denial path.

The record makes “the agent asks first” reviewable: the resource scope, approval point, idempotency behavior,
kill switch, denial test, and residual risk all connect to one decision.
