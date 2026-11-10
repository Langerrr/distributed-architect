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
4. **Optional topology cache.** Read code and deploy configuration; use topology when present and flag disagreements without editing it.
5. **Draft confirmed discoveries.** dist-debug saves unmatched confirmed causes in the project; maintainers promote patterns manually after repetition or explicit confirmation.

## Architecture: Three Layers

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: Boundary Signal Reference (opt-in)         │
│  ~30 lines — @-imported into a project's CLAUDE.md,  │
│  or read directly by the skills                      │
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

### Layer 1: Boundary Signal Reference

Lives in `CLAUDE.md`. Claude Code doesn't auto-load an installed plugin's `CLAUDE.md` into every session, so this layer only runs passively when a project `@`-imports it into its own `CLAUDE.md`. Two triggering modes either way:
- **Passive**: signal table present in a project's own `CLAUDE.md` (via `@`-import), fires during normal work
- **Active**: explicit skill invocation (Codex `$distributed-architect:dist-check`, Claude Code `/distributed-architect:dist-check`, and the corresponding dist-debug or dist-design names) for deliberate analysis

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

Each module is self-contained (~50 lines), project-agnostic, structured as prompts for investigation, not required report fields.

Analysis runs as **two sequential passes**:
1. Pass 1: Boundary correctness (which of the 4 modules applies?)
2. Pass 2: Concurrency correctness (can operations overlap according to code and deploy configuration?)

Pass 2 follows evidence of possible overlap in code and deploy configuration, including within one instance. Topology is an optional cache, not a gate; disagreements are reported.

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
1. **Check mode** (`/dist-check`): Scan changes against full catalog
2. **Debug mode** (`/dist-debug`): Pattern-match symptoms to known anti-patterns
3. **Stuck mode**: When a fix keeps breaking something else

Each entry is ~10 lines. Full catalog is ~60 lines — acceptable when loaded.

**Learning loop**: dist-debug writes unmatched confirmed causes to `.dist-architect/pattern-drafts/<slug>.md` in the project being investigated. Promotion into `catalog/` is manual after repetition or explicit confirmation.

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
**Reasoning**: Two-pass analysis (boundary correctness → concurrency correctness), guided by relevant questions; reports contain concerns and assumptions rather than every answer.
**When**: Before committing distributed system changes. Can be auto-triggered by passive detector.

### `/dist-debug` — Debug Time
**Direction**: Backward-looking root cause tracing.
**Question**: "What state across which boundary caused this symptom?"
**Reasoning**: Trace failure backwards through components, check state at each boundary, distinguish symptom component from cause component. Match against anti-pattern catalog.
**When**: Investigating production incidents, fixing bugs that span components.

## Project Topology File

An optional cache of component relationships read from code and deploy configuration. Use it when present, report disagreements and follow implementation evidence. No skill requires or automatically edits it.

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

Cardinality suggests concerns; code and deploy configuration determine whether operations can overlap, even in a 1:1 relationship:

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

1. **Creation**: Optional and manual, requested separately by the user
2. **Updates**: Maintained separately by the project; skills flag disagreements without editing it
3. **Validation**: Plugin checks if topology file is stale when entering a distributed system task

## Skill Flows

### `/dist-check` (Coding Time)

```
1. READ recent changes (git diff or specified files)

2. READ code and deploy config; use project topology as an optional cache

3. CLASSIFY changes against implementation evidence:
   → Which components are involved?
   → What type of boundary crossing? (state/data/error/interaction)
   → What is the cardinality at this boundary?

4. PASS 1 — Boundary Correctness:
   → Load relevant reasoning module (1 of 4)
   → Use relevant questions to investigate concerns

5. PASS 2 — Concurrency Correctness:
   → Read code and deploy config: can two operations run at once?
   → If yes: load concurrency module, analyze race conditions
   → If no: skip; if unknown, state the overlap assumption and its failure consequence

6. OUTPUT concerns: boundary, mechanism, suggested change.
   State the assumption the change rests on and what breaks if it is wrong.
   Flag topology disagreements affecting that assumption.
   No boundary crossing: one line.
```

### `/dist-debug` (Debug Time)

```
1. GATHER symptoms (user description, error logs, behavior)

2. READ code and deploy config; use project topology as an optional cache

3. IDENTIFY the symptom component (where the error manifests)

4. TRACE BACKWARDS through topology:
   → What components feed into the symptom component?
   → What state could each upstream component be in?
   → At which boundary could the actual cause live?

5. CHECK anti-pattern catalog:
   → Do symptoms match a known pattern shape?

6. TEST hypotheses: predict observations, run available checks or name unrun checks.
   TRACE the fix forward: does each hop repair existing data as well as new data?
   DRAFT unmatched confirmed causes in the project pattern-drafts directory.

7. OUTPUT:
   - Symptom vs probable cause component
   - Boundary where the issue likely originates
   - Anti-pattern match (if any)
   - Predicted observations and check results or named unrun checks
   - Forward trace and existing-data repair; saved draft when relevant
```

### `/dist-design` (Design Time)

```
1. GATHER requirements (what capability is being added)

2. READ code and deploy config; use project topology as an optional cache (if exists)

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
   - Relationship changes if adopted; unknowns that could change the recommendation
```

## Context Budget

| Component | Lines | When Loaded |
|-----------|-------|-------------|
| Layer 1 (signal reference) | ~30 | Only if `@`-imported into a project's `CLAUDE.md` |
| Project topology file | ~30 | When present |
| One reasoning module | ~50 | On signal detection |
| Concurrency module (pass 2) | ~50 | When code/deploy config permit overlap |
| Full anti-pattern catalog | ~60 | Review/debug mode only |
| **Typical coding session** | **~110** | **Detector + topology + one module** |
| **Typical with concurrency** | **~160** | **Above + concurrency module** |
| **Full review/debug** | **~220** | **All loaded** |

Compare to loading full architecture docs: 500-2000+ lines.

## Directory Structure

```
distributed-architect/
├── .codex-plugin/plugin.json       # Codex manifest
├── .claude-plugin/plugin.json      # Claude Code manifest
├── CLAUDE.md                       # Optional boundary signal reference
├── docs/                           # Design docs
│   ├── case-study-ai-video-platform.md
│   ├── design-philosophy.md
│   ├── reasoning-framework.md      # Detailed reasoning reference
│   └── plugin-architecture.md      # This file
├── modules/                        # Layer 2: Reasoning modules
│   ├── state-mutation.md
│   ├── data-lifecycle.md
│   ├── failure-mode.md
│   ├── interaction.md
│   └── concurrency.md
├── catalog/                        # Layer 3: Anti-pattern entries
│   ├── tight-retry-loop.md
│   ├── lost-data-at-ack.md
│   ├── channel-conflation.md
│   ├── boundary-state-leak.md
│   ├── compounding-retry.md
│   └── premature-state-transition.md
├── skills/                         # Shared Claude Code and Codex skills
│   ├── dist-check/
│   │   └── SKILL.md               # Coding-time analysis
│   ├── dist-design/
│   │   └── SKILL.md               # Design-time analysis
│   └── dist-debug/
│       └── SKILL.md               # Debug-time analysis
└── templates/                      # Project artifact templates
    └── topology.yaml               # Template for project topology file
```

## Resolved Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Where does detector live? | Optional `CLAUDE.md` reference; skills have their own entry prompts | Skills are the only trigger Claude Code loads automatically; a project that wants passive detection `@`-imports this file's table into its own `CLAUDE.md` |
| Auto-create or manual-create topology? | Optional cache; flag disagreements | Code and deploy config are the evidence |
| How to handle race conditions? | Separate concurrency module (5th module), triggered by possible overlap in code/deploy config | Concurrency is a distinct dimension, not an overlay on boundary analysis |
| Sequential or interleaved analysis? | Sequential two-pass (boundary → concurrency) | LLMs use chain-of-thought; parallel/interleaved analysis produces shallow results on both |
| Learning loop for new patterns? | Draft unmatched confirmed causes in the project; manual promotion after repetition or confirmation | Reduces noise while still capturing patterns |
| How many entry points? | Three: `/dist-design`, `/dist-check`, `/dist-debug` | Design (forward/trade-offs), coding (forward/correctness), debugging (backward/root-cause) are different reasoning directions |
| Fixed vs dynamic cardinality? | Document precisely — fixed counts matter for failure analysis | `3 nodes, 2 replicas` gives different reasoning than just `N` |

## Open Questions

1. **Topology staleness signal**: What code patterns should trigger "your topology may be stale"? New connection handler? New queue client? Import of a new service client?
2. **Cross-project portability**: When loaded on a 5-10x more complex project, does the topology format scale, or does it need hierarchy/grouping?
3. **Abstraction verification**: Periodically check that modules, catalog, and skills remain project-agnostic. Case-study-specific content belongs in `docs/case-study-*.md` files only.
