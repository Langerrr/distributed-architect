# Plugin Architecture

## The Core Problem

Loading everything → context explosion, diminishing returns.
Loading nothing → LLM reasons with single-process mental models, misses distributed concerns.

The sweet spot: **detect that a distributed concern exists, then load only the relevant reasoning module.**

This mirrors how experienced engineers think — they don't mentally recite a 50-page architecture doc before every change. They have a lightweight "smell detector" that fires when something crosses a boundary, then they focus deep reasoning on that specific concern.

## Design Principles

1. **Reasoning framework, not documentation system.** The plugin teaches the LLM *how to think*, not *what to know*. Documents go stale; reasoning patterns don't.
2. **Detection is cheap, reasoning is expensive.** Keep detection always-on, load reasoning on demand.
3. **Sequential two-pass analysis.** LLMs are chain-of-thought reasoners. Don't attempt interleaved boundary + concurrency analysis. Run them as two sequential passes.
4. **Auto-update over auto-create.** Topology and project artifacts are manually created (needs human judgment), but updates are auto-triggered when code changes affect them.
5. **Threshold-based learning.** New anti-patterns are auto-captured, but promoted to the catalog only after repeated occurrence or explicit user confirmation. Reduces noise.

## Architecture: Three Layers

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: Boundary Detector (always loaded)          │
│  ~30 lines in memory file — near-zero context cost   │
│  "Am I crossing a boundary? What kind?"              │
├─────────────────────────────────────────────────────┤
│  Layer 2: Reasoning Modules (loaded on demand)       │
│  One module per concern type, ~50 lines each         │
│  "Here's how to think through this specific case"    │
├─────────────────────────────────────────────────────┤
│  Layer 3: Anti-Pattern Catalog (reference)           │
│  Loaded during review, debugging, or when stuck      │
│  "Known traps to watch for"                          │
└─────────────────────────────────────────────────────┘
```

### Layer 1: Boundary Detector (Always-On)

Lives in **memory file** (more reliable than CLAUDE.md per testing). Hybrid passive + active triggering:
- **Passive**: Compact signal list in memory file, fires during normal work
- **Active**: Explicit skill invocation for deliberate analysis

Its ONLY job is recognition — it doesn't contain the reasoning itself, just the triggers.

```
BOUNDARY SIGNALS:
- Changing state/status that another process reads → [state-mutation]
- Data leaving one component for another (serialize, send, store) → [data-lifecycle]
- Writing error handling for cross-component operations → [failure-mode]
- Adding new communication between components → [interaction]
- Multiple actors accessing the same resource → [concurrency]

When detected: load the reasoning module for that signal type before writing code.
```

### Layer 2: Reasoning Modules (On-Demand)

Five modules, covering two dimensions of distributed correctness:

**Dimension 1 — Boundary Correctness** (single operation, traced across components):
```
modules/
  state-mutation.md      # Observer trace, tick-forward analysis
  data-lifecycle.md      # Boundary crossing, loss points, ownership
  failure-mode.md        # Classification, retry analysis, loop detection
  interaction.md         # New communication path analysis
```

**Dimension 2 — Concurrency Correctness** (multiple operations, overlapping in time):
```
modules/
  concurrency.md         # Write-write conflicts, read-write races,
                         # ordering assumptions, atomicity gaps
```

Each module is self-contained (~50 lines), project-agnostic, structured as questions not information.

Analysis runs as **two sequential passes**:
1. Pass 1: Boundary correctness (which of the 4 modules applies?)
2. Pass 2: Concurrency correctness (does the topology indicate concurrent actors here?)

Pass 2 is triggered by the **topology file** — if the component being modified is on the "1" side of a 1:N relationship, concurrency analysis is mandatory.

### Layer 3: Anti-Pattern Catalog (Reference)

Growing collection of named patterns with shape/detection/fix:

```
catalog/
  tight-retry-loop.md
  lost-data-at-ack.md
  channel-conflation.md
  boundary-state-leak.md
  compounding-retry.md
  premature-state-transition.md
```

Loaded in three scenarios:
1. **Review mode** (`/dist-review`): Scan changes against full catalog
2. **Debug mode** (`/dist-debug`): Pattern-match symptoms to known anti-patterns
3. **Stuck mode**: When a fix keeps breaking something else

Each entry is ~10 lines. Full catalog is ~60 lines — acceptable when loaded.

**Learning loop**: New patterns are auto-drafted to a scratch area. Promoted to catalog after: (a) same pattern class appears a second time, or (b) user explicitly confirms. First occurrence = draft, second = catalog entry.

## Three Entry Points

Different reasoning for different phases of work:

### `/dist-design` — Design Time
**Direction**: Forward-looking trade-off analysis.
**Question**: "Which pattern/architecture fits this requirement?"
**Reasoning**: Compare communication patterns, evaluate failure modes of each option, assess scaling characteristics.
**When**: Choosing between architectures, adding new components, deciding communication mechanisms.

### `/dist-check` — Coding Time
**Direction**: Forward-looking correctness verification.
**Question**: "Does this change break anything across boundaries?"
**Reasoning**: Two-pass analysis (boundary correctness → concurrency correctness), checklist-driven.
**When**: Before committing distributed system changes. Can be auto-triggered by passive detector.

### `/dist-debug` — Debug Time
**Direction**: Backward-looking root cause tracing.
**Question**: "What state across which boundary caused this symptom?"
**Reasoning**: Trace failure backwards through components, check state at each boundary, distinguish symptom component from cause component. Match against anti-pattern catalog.
**When**: Investigating production incidents, fixing bugs that span components.

## Project Topology File

A compact, information-dense artifact that drives analysis decisions. **Manually created** on first exploration, **auto-updated** when code changes affect topology-relevant paths.

### Format

```yaml
# .dist-architect/topology.yaml (or project-specific location)
topology:
  - from: api-gateway
    count: 1 (fixed)
    to: task-runner
    count: N (dynamic)
    via: message queue (consumer group)
    notes: "1:N — gateway produces, runners consume. Concurrency on consumer side."

  - from: task-runner
    count: N (dynamic)
    to: api-gateway
    count: 1 (fixed)
    via: persistent connection (events)
    notes: "N:1 — concurrent status events hit single gateway. Race on shared state."

  - from: task-runner
    count: 1 (fixed)
    to: execution-backend
    count: 1 (fixed, per-runner)
    via: HTTP + event stream
    notes: "1:1 tight coupling — backend down = runner down"

  - from: api-gateway
    count: 1 (fixed)
    to: message-broker
    count: 3 nodes, 2 replicas (fixed)
    via: streams + key-value
    notes: "SPOF for task queue, data loss risk if cluster fails"

  - from: client
    count: N (dynamic)
    to: api-gateway
    count: 1 (fixed)
    via: HTTP + event stream
    notes: "fan-in on gateway, broadcast fan-out for status updates"
```

### Cardinality as Decision Table

The cardinality directly determines which analysis is triggered:

| Pattern | Primary concern | Analysis triggered |
|---------|----------------|-------------------|
| 1:N (dynamic) | Concurrency on the "1" side | Race conditions, resource contention, scaling |
| 1:1 (fixed) | Failure coupling | Cascade analysis, health propagation |
| N:1 | Bottleneck / SPOF | Availability, backpressure, failover |
| N:M | All of the above | Full analysis |
| Fixed count (e.g., 3+2) | Known failure scenarios | Quorum, partition tolerance |

### Three Dimensions Per Relationship

1. **Who ↔ Who** — components involved
2. **Via what** — communication mechanism (persistent connections, HTTP, message streams, shared DB, etc.)
3. **How many** — cardinality with precision:
   - `1 (fixed)` — singleton, won't scale
   - `N (dynamic)` — scales up/down, count unknown at design time
   - `3 nodes, 2 replicas (fixed)` — known redundancy, specific failure tolerance
   - `1 (fixed, per-instance)` — 1:1 binding to parent component

### Lifecycle

1. **Creation**: Manual, triggered by user during initial codebase exploration or `/dist-design`
2. **Updates**: Auto-detected when code changes touch topology-relevant paths (new service, new communication channel, cardinality change)
3. **Validation**: Plugin checks if topology file is stale when entering a distributed system task

## Skill Flows

### `/dist-check` (Coding Time)

```
1. READ recent changes (git diff or specified files)

2. LOAD project topology file

3. CLASSIFY changes against topology:
   → Which components are involved?
   → What type of boundary crossing? (state/data/error/interaction)
   → What is the cardinality at this boundary?

4. PASS 1 — Boundary Correctness:
   → Load relevant reasoning module (1 of 4)
   → Walk through checklist with concrete answers for this change

5. PASS 2 — Concurrency Correctness:
   → Check topology: is this component on the "1" side of a 1:N?
   → If yes: load concurrency module, analyze race conditions
   → If no: skip (1:1 doesn't need concurrency analysis at this boundary)

6. OUTPUT structured analysis:
   - Boundary type + module applied
   - Concerns found (or "none")
   - Anti-patterns matched (if any)
   - Topology update needed? (if change affects component relationships)
```

### `/dist-debug` (Debug Time)

```
1. GATHER symptoms (user description, error logs, behavior)

2. LOAD project topology file

3. IDENTIFY the symptom component (where the error manifests)

4. TRACE BACKWARDS through topology:
   → What components feed into the symptom component?
   → What state could each upstream component be in?
   → At which boundary could the actual cause live?

5. CHECK anti-pattern catalog:
   → Do symptoms match a known pattern shape?

6. NARROW to likely root cause boundary

7. OUTPUT:
   - Symptom vs probable cause component
   - Boundary where the issue likely originates
   - Anti-pattern match (if any)
   - Suggested investigation steps
```

### `/dist-design` (Design Time)

```
1. GATHER requirements (what capability is being added)

2. LOAD project topology file (if exists)

3. IDENTIFY design decision needed:
   → New component? New communication path? Scaling change?

4. FOR EACH option under consideration:
   → What cardinality does it introduce?
   → What failure modes does this cardinality create?
   → What concurrency concerns does it add?
   → Does it create new convergence points in the topology?

5. COMPARE options on:
   - Failure isolation
   - Concurrency complexity
   - Operational overhead
   - Scaling characteristics

6. OUTPUT:
   - Options compared with trade-offs
   - Recommended option with rationale
   - Topology changes if adopted
```

## Context Budget

| Component | Lines | When Loaded |
|-----------|-------|-------------|
| Layer 1 (detector in memory) | ~30 | Always |
| Project topology file | ~30 | On skill invocation |
| One reasoning module | ~50 | On signal detection |
| Concurrency module (pass 2) | ~50 | When topology indicates 1:N |
| Full anti-pattern catalog | ~60 | Review/debug mode only |
| **Typical coding session** | **~110** | **Detector + topology + one module** |
| **Typical with concurrency** | **~160** | **Above + concurrency module** |
| **Full review/debug** | **~220** | **All loaded** |

Compare to loading full architecture docs: 500-2000+ lines.

## Directory Structure

```
distributed-architect/
├── CLAUDE.md                       # Plugin instructions + Layer 1 detector
├── docs/                           # Design docs
│   ├── case-study-ai-video-platform.md
│   ├── design-philosophy.md
│   ├── reasoning-framework.md      # Full framework (source of truth)
│   └── plugin-architecture.md      # This file
├── modules/                        # Layer 2: Reasoning modules
│   ├── state-mutation.md
│   ├── data-lifecycle.md
│   ├── failure-mode.md
│   ├── interaction.md
│   └── concurrency.md
├── catalog/                        # Layer 3: Anti-pattern entries
│   ├── _drafts/                    # Auto-captured, not yet promoted
│   ├── tight-retry-loop.md
│   ├── lost-data-at-ack.md
│   ├── channel-conflation.md
│   ├── boundary-state-leak.md
│   ├── compounding-retry.md
│   └── premature-state-transition.md
├── skills/                         # Claude Code skill definitions
│   ├── dist-check.md               # Coding-time analysis
│   ├── dist-design.md              # Design-time analysis
│   └── dist-debug.md               # Debug-time analysis
├── templates/                      # Project artifact templates
│   └── topology.yaml               # Template for project topology file
└── detector.md                     # Layer 1 source (copied to memory/CLAUDE.md)
```

## Resolved Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Where does detector live? | Memory file (hybrid passive + active) | More reliable than CLAUDE.md per testing |
| Auto-create or manual-create topology? | Manual create, auto-update | Initial mapping needs human judgment; updates can be detected |
| How to handle race conditions? | Separate concurrency module (5th module), triggered by topology cardinality | Concurrency is a distinct dimension, not an overlay on boundary analysis |
| Sequential or interleaved analysis? | Sequential two-pass (boundary → concurrency) | LLMs use chain-of-thought; parallel/interleaved analysis produces shallow results on both |
| Learning loop for new patterns? | Auto-draft on first occurrence, promote on second or user confirmation | Reduces noise while still capturing patterns |
| How many entry points? | Three: `/dist-design`, `/dist-check`, `/dist-debug` | Design (forward/trade-offs), coding (forward/correctness), debugging (backward/root-cause) are different reasoning directions |
| Fixed vs dynamic cardinality? | Document precisely — fixed counts matter for failure analysis | `3 nodes, 2 replicas` gives different reasoning than just `N` |

## Open Questions

1. **Passive detection reliability**: Need real-world testing of memory-file-based detection. How often does the LLM miss signals vs catch them?
2. **Topology auto-update trigger**: What code patterns should trigger "your topology may be stale"? New connection handler? New queue client? Import of a new service client?
3. **Cross-project portability**: When loaded on a 5-10x more complex project, does the topology format scale, or does it need hierarchy/grouping?
4. **Abstraction verification**: Periodically check that modules, catalog, and skills remain project-agnostic. Case-study-specific content belongs in `docs/case-study-*.md` files only.
