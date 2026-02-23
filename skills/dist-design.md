# dist-design — Design-Time Architecture Analysis

Analyze architecture decisions for distributed system trade-offs. Helps choose between communication patterns, component boundaries, and scaling strategies.

## Trigger
- User invokes `/dist-design` (with optional description of what's being designed)

## Skill Instructions

You are performing a distributed systems design analysis. The goal is to evaluate architectural options and their trade-offs — not to verify code correctness (that's `/dist-check`).

### Step 1: Gather Requirements

Understand what capability is being added or what design decision is being made. Ask clarifying questions if needed:
- What problem does this solve?
- What are the constraints (latency, throughput, consistency, fault tolerance)?
- What components already exist? (load topology file if available)

### Step 2: Load Project Topology

Look for a topology file. If it exists, understand the current system shape. If it doesn't, work with whatever architecture context is available.

### Step 3: Identify the Design Decision

Categorize what's being decided:

| Decision type | Examples |
|--------------|---------|
| **Communication pattern** | Stream vs queue vs RPC, push vs pull, sync vs async |
| **Component boundary** | Where to split responsibilities, what runs in same process vs separate |
| **State management** | Where state lives, who owns it, consistency model |
| **Failure strategy** | Retry policy, circuit breakers, fallback behavior, DLQ design |
| **Scaling approach** | Horizontal vs vertical, partitioning, sharding, replication |

### Step 4: Enumerate Options

For each viable option:

**a. Topology impact**
- What does the communication graph look like with this option?
- What cardinality does it introduce? (1:1, 1:N, N:M)
- Does it add new convergence points (where concurrent operations meet)?

**b. Failure analysis**
- What are the failure modes specific to this option?
- What's the blast radius of the most likely failure?
- How does recovery work?

**c. Concurrency implications**
- Does this option introduce new concurrent access to shared resources?
- What coordination mechanism would be needed?

**d. Operational cost**
- How complex is this to operate, monitor, and debug?
- What observability does it require?

### Step 5: Compare and Recommend

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
- Topology: [impact]
- Failure modes: [key risks]
- Concurrency: [concerns]
- Operational cost: [assessment]
- Best when: [conditions where this option excels]

### Recommendation
[Which option and why, given the stated constraints]

### Topology Changes
[How the topology file should be updated if this option is adopted]
```

### Step 6: Flag Unknowns

Explicitly state what you DON'T know that could change the recommendation:
- Load characteristics not yet known
- Failure rates of dependencies not measured
- Scaling requirements still undefined

These are inputs the user should validate before committing to the design.
