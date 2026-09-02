---
name: dist-debug
description: This skill should be used when investigating a failure whose symptom and root cause are suspected to live in different independently-deployed processes or services — a consumer failing because of something a producer did, or a downstream service acting on stale or wrong state from an upstream one. Traces backward from symptom to cause boundary and matches known distributed anti-patterns. Not for a single-process bug with a clear stack trace, and not for reviewing a diff you're about to commit — use dist-check for that.
argument-hint: "<symptom description, error message, or log snippet>"
allowed-tools: Read, Grep, Glob
---

# /dist-debug — Debug-Time Root Cause Analysis

Trace distributed system failures backward from symptom to root cause. In distributed systems, the symptom component and the cause component are often different. Trace backward, don't just fix where it hurts.

## Arguments

- `$ARGUMENTS` may contain a symptom description, error message, or log snippet

## Step 1: Gather Symptoms

From `$ARGUMENTS` or by asking the user:
- What's the observable behavior? (error message, unexpected state, performance issue)
- Which component reported the error? (this is the symptom component)
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

Read `${CLAUDE_PLUGIN_ROOT}/catalog/INDEX.md`, match the symptom shape against its "Symptom shape" column, then open the matching entry file for the full shape/detection/fix.

## Step 6: Hypothesis Formation

Form 1-3 hypotheses based on the backward trace and anti-pattern match:

```
Hypothesis 1 (highest confidence):
  Root cause: [what's actually wrong]
  Boundary: [which boundary the issue crosses]
  Mechanism: [how the cause produces the symptom]
  Verification: [how to confirm — specific log, query, or test]
```

## Step 7: Forward Trace the Fix

For each hypothesis, take the proposed fix and trace it **forward** through the same path the backward trace established. The backward trace gave you the chain; now run the fix through it in the opposite direction:

```
Fix applied at: [root cause component]
   -> Does it change: [state/data at component Y]?
      -> Does that resolve: [the dependency at component X]?
         -> Does the symptom disappear?
```

At each hop, ask: **does this resolve for all data, or only for new data?**

If any hop answers "only going forward" — the fix leaves accumulated damage from the bug's lifetime. Flag what cleanup is needed (purge, migration, backfill) and whether it can run at startup, as a one-off script, or requires a migration.

## Step 8: Output

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

### Forward Trace
[For top hypothesis: trace the fix forward through the same path. Flag any hop where the fix only addresses future data, not existing state.]

### Immediate Investigation Steps
1. [Most targeted check to confirm/deny top hypothesis]
2. [Next check]
3. [Fallback investigation if above don't confirm]
```
