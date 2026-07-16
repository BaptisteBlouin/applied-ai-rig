# Production service: degraded mode after provider latency

This synthetic example shows how an incident changes the operating decision for a classification service.
Detailed logs and the incident timeline remain in access-controlled canonical systems.

## Decision -> Evidence

1. [DEC-20260712-provider-degraded-mode](DECISIONS.md) defines the bounded fallback.
2. [EVD-20260712-incident-latency](EVIDENCE.md) separates measured impact from remaining unknowns.
3. [service_register.csv](service_register.csv) records health limits, ownership, and rollback.
4. [incident_register.csv](incident_register.csv) links the incident summary and corrective action.

The record explains why the service now returns a queued response instead of retrying indefinitely and
which latency signal would trigger that behavior again.
