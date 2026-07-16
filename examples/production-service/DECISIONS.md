# Decisions

## DEC-20260712-provider-degraded-mode — Queue work after provider latency exceeds the limit

- **Decision ID:** DEC-20260712-provider-degraded-mode
- **Status:** accepted
- **Context:** Repeated synchronous retries amplified a provider latency incident and exhausted request workers.
- **Options:** Continue bounded synchronous retries; fail immediately; queue the classification and return a pending result.
- **Decision:** After one bounded retry or a 5-second total deadline, queue the request and return a pending result.
- **Consequences:** Some users receive delayed results and the queue requires an explicit age and depth limit.
- **Revision threshold:** Revisit if queued completion falls below 99 percent within five minutes or duplicate processing exceeds 0.1 percent.
- **Supersedes:** None
- **Evidence:** EVD-20260712-incident-latency
