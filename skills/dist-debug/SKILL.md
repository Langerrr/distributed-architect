---
name: dist-debug
description: Backward root-cause tracing from symptoms to cause boundary in distributed systems. Use when investigating cross-component failures or production incidents.
---

# /dist-debug — Debug-Time Root Cause Analysis

Trace distributed system failures backward from symptom to root cause. In distributed systems, the symptom component and the cause component are often different. Trace backward, don't just fix where it hurts.

## Arguments

- `$ARGUMENTS` may contain a symptom description, error message, or log snippet

## Step 1: Gather Symptoms

From `$ARGUMENTS` or by asking the user:
- What's the observable behavior? (error message, unexpected state, performance issue)
- Which component reported the error? (this is the SYMPTOM component)
- When does it happen? (always, intermittently, under load, after a specific event)
- Any recent changes? (new code, config change, scaling event)

## Step 2: Load Project Topology

Load the topology file to understand the communication graph. The root cause is almost always at a boundary — knowing the boundaries narrows the search.

## Step 3: Identify the Symptom Boundary

From the topology:
- What components feed into the symptom component?
- What data/state does the symptom component depend on from other components?
- What communication paths lead to the symptom component?

## Step 4: Backward Trace

Starting from the symptom, trace backward through the topology:

```
Symptom: [what's observed, in which component]
   <- Depends on: [state/data from component X]
      <- Which depends on: [operation in component Y]
         <- Which could fail if: [condition in component Z]
```

At each hop, ask:
- Could this component be in an unexpected state?
- Could the data arriving here be stale, missing, or corrupted?
- Could timing/ordering explain the symptom?

## Step 5: Anti-Pattern Match

Read the catalog entries from the plugin's `catalog/` directory and check the symptom shape:

| Symptom shape | Likely anti-pattern |
|--------------|-------------------|
| Rapid repeated failures from same component | AP-1: Tight Retry Loop |
| Data missing that "should be there" | AP-2: Lost Data at ACK |
| Operation marked failed but actually succeeded | AP-3: Channel Conflation |
| Component making wrong decisions about another's state | AP-4: Boundary State Leak |
| Way more retries than configured | AP-5: Compounding Retry |
| Failures immediately after recovery | AP-6: Premature State Transition |

## Step 6: Hypothesis Formation

Form 1-3 hypotheses based on the backward trace and anti-pattern match:

```
Hypothesis 1 (highest confidence):
  Root cause: [what's actually wrong]
  Boundary: [which boundary the issue crosses]
  Mechanism: [how the cause produces the symptom]
  Verification: [how to confirm — specific log, query, or test]
```

## Step 7: Output

```
## Distributed Debug Analysis

**Symptom**: [description]
**Symptom component**: [where it manifests]
**Probable cause component**: [where it originates]
**Boundary involved**: [which inter-component boundary]

### Backward Trace
[The chain from symptom to probable cause]

### Anti-Pattern Match
[Matching pattern, or "no known pattern match"]

### Hypotheses
[Ranked by confidence with verification steps]

### Immediate Investigation Steps
1. [Most targeted check to confirm/deny top hypothesis]
2. [Next check]
3. [Fallback investigation if above don't confirm]
```
