---
name: Verification and Research (learned)
globs: ["memory-bank/creative/*.md", "memory-bank/reflection/*.md"]
paths: ["memory-bank/creative/"]
topics: ["verification", "audit", "analysis", "research", "subagents", "tooling"]
priority: low
auto_generated: true
derived_from: [audit-partner-credit-warning-invariants]
evidence_count: 1
last_validated: 2026-11-03
---

# Verification and Research

- Before treating an analysis or audit document as authoritative, verify each claim about how the framework works (caching, `sudo`/context propagation, ORM inverses, translation lookup) against the framework source. Use an independent agent whose prompt asks it to refute the claim and lets it read code only. Claims about what the code does survive review much better than claims about why or how it works.
- In sub-agents searching a large repo, use `git grep` or path-scoped searches instead of repo-wide file-type greps, which time out and leave gaps in the evidence.
