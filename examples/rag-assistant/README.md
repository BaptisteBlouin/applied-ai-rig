# RAG assistant: choosing hybrid retrieval

This synthetic example shows how a small team records a retrieval change without copying prompts, user
questions, or full experiment traces into Git.

## Decision -> Evidence

1. [DEC-20260710-hybrid-retrieval](DECISIONS.md) defines the choice and a measurable revision threshold.
2. [EVD-20260710-recall](EVIDENCE.md) states the measured claim and its limitations.
3. [experiments.csv](experiments.csv) keeps the comparable baseline and candidate runs.
4. [model_register.csv](model_register.csv) identifies the governed model boundary.
5. [data_register.csv](data_register.csv) records the synthetic evaluation dataset and its allowed use.

The important outcome is not the `0.84` score by itself. A reviewer can see which decision it supports,
which baseline it beat, what dataset scope it covers, and which result would cause the decision to change.
