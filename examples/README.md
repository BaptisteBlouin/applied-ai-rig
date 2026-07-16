# Worked examples

These examples are synthetic, contain no real credentials or private endpoints, and focus on the smallest
record chain that changed an engineering decision. They are illustrative excerpts rather than complete
generated projects.

- [RAG assistant](rag-assistant/README.md): a retrieval change supported by comparable evaluation runs.
- [Tool-using agent](tool-agent/README.md): an approval boundary supported by denial-path tests.
- [Production service](production-service/README.md): a degraded mode revised after a provider incident.

Each example follows the same review path:

`decision -> evidence -> risk-specific register -> canonical external detail`

Copy the shape, not the synthetic values. A real project should use its own stable IDs, acceptance criteria,
measurements, owners, and access-controlled external references.
