---
name: dist-design
description: Architecture trade-off analysis for distributed system design decisions. Use when choosing between communication patterns, component boundaries, or scaling strategies.
---

# /dist-design — Design-Time Architecture Analysis

Evaluate architectural options and their trade-offs for distributed system decisions.

## Arguments

- `$ARGUMENTS` may contain a description of what's being designed

## Step 1: Gather Requirements

Understand from `$ARGUMENTS` or by asking the user:
- What problem does this solve?
- What are the constraints (latency, throughput, consistency, fault tolerance)?
- What components already exist? (load topology file if available)

## Step 2: Load Project Topology

Look for a topology file. If it exists, understand the current system shape. If it doesn't, work with whatever architecture context is available.

## Step 3: Identify the Design Decision

Categorize what's being decided:

| Decision type | Examples |
|--------------|---------|
| **Communication pattern** | Stream vs queue vs RPC, push vs pull, sync vs async |
| **Component boundary** | Where to split responsibilities, same process vs separate |
| **State management** | Where state lives, who owns it, consistency model |
| **Failure strategy** | Retry policy, circuit breakers, fallback behavior, DLQ design |
| **Scaling approach** | Horizontal vs vertical, partitioning, sharding, replication |

## Step 4: Enumerate Options

For each viable option, analyze:

**a. Topology impact** — What cardinality does it introduce? New convergence points?
**b. Failure analysis** — What fails, blast radius, recovery mechanism?
**c. Concurrency implications** — New concurrent access to shared resources?
**d. Operational cost** — Complexity to operate, monitor, debug?

## Step 5: Compare and Recommend

Present options side by side:

```
## Design Analysis: [decision description]

### Option A: [name]
- Topology: [impact]
- Failure modes: [key risks]
- Concurrency: [concerns]
- Operational cost: [assessment]
- Best when: [conditions where this option excels]

### Option B: [name]
- [same structure]

### Recommendation
[Which option and why, given the stated constraints]

### Topology Changes
[How the topology file should be updated if adopted]
```

## Step 6: Flag Unknowns

Explicitly state what you DON'T know that could change the recommendation:
- Load characteristics not yet known
- Failure rates of dependencies not measured
- Scaling requirements still undefined
