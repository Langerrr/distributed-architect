---
name: dist-check
description: Two-pass boundary + concurrency analysis on distributed system code changes. Use before committing changes that cross component boundaries.
---

# /dist-check — Coding-Time Boundary Analysis

Analyze code changes for distributed system correctness issues. Runs a two-pass analysis: boundary correctness, then concurrency correctness (if topology indicates).

## Arguments

- `$ARGUMENTS` may contain: a file/dir path, `--staged`, or `--diff <range>`

## Step 1: Gather Changes

Based on `$ARGUMENTS`:
- If a file/dir path is given, read those files
- If `--staged`, run `git diff --cached`
- If `--diff <range>`, run `git diff <range>`
- If no arguments, run `git diff` for uncommitted changes
- If no diff at all, ask the user what change to analyze

Identify which components are being modified.

## Step 2: Load Project Topology

Look for a topology file in the project (`.dist-architect/topology.yaml`, or check project CLAUDE.md for location). If none exists, note this and proceed with what you can infer from the code.

## Step 3: Classify the Change

For each modified component, determine which boundary signal applies:

| Signal | Condition |
|--------|-----------|
| `state-mutation` | Changing state/status that another process reads |
| `data-lifecycle` | Data crossing a serialization, network, or storage boundary |
| `failure-mode` | Error handling for cross-component operations |
| `interaction` | New message type, API call, or event between components |

If none apply (purely internal, single-component change), report "No boundary crossing detected" and stop.

## Step 4: Pass 1 — Boundary Correctness

Read the relevant reasoning module from the plugin's `modules/` directory and walk through its checklist. Answer each question concretely for the specific change. Do not skip questions.

Document:
- Each checklist question and your answer
- Any concerns found
- Any assumptions the change makes about other components

## Step 5: Pass 2 — Concurrency Correctness

Check the topology: is the component being modified on the "1" side of a 1:N relationship?

- **If yes**: Read `modules/concurrency.md` from the plugin directory and walk through its checklist.
- **If no**: Skip this pass. Note: "No concurrency concern at this boundary (1:1 or N-side)."

## Step 6: Anti-Pattern Scan

Check if the change matches any known anti-pattern shapes. Read the catalog entries from the plugin's `catalog/` directory:
- Tight retry loop (AP-1)
- Lost data at ACK (AP-2)
- Channel conflation (AP-3)
- Boundary state leak (AP-4)
- Compounding retry (AP-5)
- Premature state transition (AP-6)

## Step 7: Output

Report findings in this format:

```
## Distributed Systems Analysis

**Components involved**: [list]
**Boundary type**: [state-mutation | data-lifecycle | failure-mode | interaction]
**Topology**: [cardinality at this boundary]

### Pass 1: Boundary Correctness
[Checklist results — concerns or "clean"]

### Pass 2: Concurrency
[Checklist results, or "skipped — no 1:N at this boundary"]

### Anti-Pattern Check
[Matches found, or "none"]

### Recommendations
[Specific changes needed, or "no issues found"]

### Topology Update
[Does the topology file need updating? If yes, what changed.]
```
