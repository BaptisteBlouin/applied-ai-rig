# Decisions

## DEC-20260710-hybrid-retrieval — Use hybrid retrieval for support answers

- **Decision ID:** DEC-20260710-hybrid-retrieval
- **Status:** accepted
- **Context:** Lexical retrieval missed paraphrased product questions in the synthetic held-out set.
- **Options:** Keep lexical-only retrieval; switch to embeddings only; combine lexical and embedding scores.
- **Decision:** Use hybrid retrieval with a fixed score fusion configuration documented in the experiment system.
- **Consequences:** One embedding request is added per query and index refreshes become part of release work.
- **Revision threshold:** Revisit if held-out recall@5 falls below 0.80 or measured retrieval cost exceeds EUR 20 per 100000 queries.
- **Supersedes:** None
- **Evidence:** EVD-20260710-recall
