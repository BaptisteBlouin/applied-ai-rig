# Evidence

## EVD-20260712-incident-latency — Retries amplified request latency during the incident

- **Evidence ID:** EVD-20260712-incident-latency
- **Claim:** Synchronous retries increased p95 request latency from 1.2 seconds to 14.8 seconds during the synthetic incident window.
- **Status:** measured
- **Source:** METRIC-classifier-latency and INC-20260712-provider-latency in canonical operations systems.
- **Scope:** Synthetic service traffic between 10:00 and 10:25 UTC on 2026-07-12.
- **Limitations:** Does not establish provider root cause or predict queue behavior at higher traffic volumes.
- **Related decisions:** DEC-20260712-provider-degraded-mode
