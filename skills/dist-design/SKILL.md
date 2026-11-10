---
name: dist-design
description: This skill should be used when choosing between architectural options for how independently-deployed processes or services will communicate, share state, or scale — stream vs. queue vs. RPC, splitting a monolith into services, a replication/partitioning strategy, or cross-service retry and circuit-breaker design. Runs before a specific implementation exists. Not for single-service API or schema design with no cross-service boundary, and once a concrete diff exists, use dist-check instead.
argument-hint: "<description of what's being designed>"
allowed-tools: Read, Grep, Glob
---

# dist-design — Architecture Options

Understand the proposed decision and constraints: latency, throughput, consistency, failure tolerance and operational cost. Flag missing requirements that could change the choice.

Read existing code and deploy configuration where available. Use the project's optional `.dist-architect/topology.yaml` (or location in project guidance) as a cache of that reading; flag disagreements and use implementation evidence. For a new system, work from the proposed architecture and distinguish assumptions from established facts.

Compare viable options for communication, component boundaries, state ownership, failure strategy or scaling. For each option, ask:

- What relationships, cardinality and convergence points does it introduce?
- What fails, who is affected, and how does recovery work?
- Can two operations run at once against the same resource?
- What does it cost to operate, monitor and debug?

Use relevant questions in [State mutation](../../modules/state-mutation.md), [Data lifecycle](../../modules/data-lifecycle.md), [Failure mode](../../modules/failure-mode.md) and [Interaction](../../modules/interaction.md). Use [Concurrency](../../modules/concurrency.md) if the existing or proposed code and deployment permit overlap, regardless of whether a topology file exists.

## Report

Compare options side by side on the trade-offs that decide this case. Recommend one against the stated constraints. Flag unknowns, assumptions and what evidence would change the recommendation. Describe consequential relationship or scaling changes without requiring or editing a topology file. No fixed section per option or empty categories are needed.
