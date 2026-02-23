# distributed-architect — Distributed Systems Reasoning Plugin

A reasoning framework that helps LLMs analyze distributed system changes for correctness. Not a documentation system — a structured thinking process.

## Skills

| Command | Phase | Purpose |
|---------|-------|---------|
| `/dist-check` | Coding | Two-pass boundary + concurrency analysis on code changes |
| `/dist-design` | Design | Architecture trade-off analysis for distributed decisions |
| `/dist-debug` | Debug | Backward root-cause tracing from symptoms to cause boundary |

## Architecture

Three layers, loaded incrementally to minimize context cost:

**Layer 1 — Boundary Detector** (always loaded, ~30 lines):
Recognizes when a code change crosses a distributed boundary. Signals: state-mutation, data-lifecycle, failure-mode, interaction, concurrency.

**Layer 2 — Reasoning Modules** (loaded on demand, ~50 lines each):
Five modules covering two dimensions:
- Boundary correctness: `state-mutation`, `data-lifecycle`, `failure-mode`, `interaction`
- Concurrency correctness: `concurrency` (triggered when topology shows 1:N)

**Layer 3 — Anti-Pattern Catalog** (loaded for review/debug):
Named patterns with shape/detection/fix. Growing collection, auto-drafted on discovery.

## How It Works

### Passive Detection
The boundary detector (in `detector.md`) watches for signals during normal work. When detected, it triggers loading the relevant reasoning module before writing code.

### Active Analysis
Invoke a skill explicitly: `/dist-check`, `/dist-design`, or `/dist-debug`. The skill drives a structured analysis procedure.

### Two-Pass Analysis (coding time)
1. **Pass 1 — Boundary correctness**: Does this single operation work correctly across components?
2. **Pass 2 — Concurrency correctness**: Do simultaneous operations conflict? (Only runs when topology indicates 1:N at the boundary.)

Sequential passes — LLMs reason via chain-of-thought, not parallel intuition.

## Project Integration

### Topology File
Each project using this plugin should have a topology file (see `templates/topology.yaml`):
- Manually created during initial codebase exploration
- Auto-updated when code changes affect component relationships
- Captures: components, cardinality (fixed/dynamic/exact counts), communication mechanisms, convergence points

### Boundary Detector in Memory
Copy the content of `detector.md` into the project's Claude memory file for passive detection during normal work.

## Key Files

```
distributed-architect/
├── CLAUDE.md              # This file
├── detector.md            # Layer 1: boundary signal detector
├── modules/               # Layer 2: reasoning checklists
│   ├── state-mutation.md
│   ├── data-lifecycle.md
│   ├── failure-mode.md
│   ├── interaction.md
│   └── concurrency.md
├── catalog/               # Layer 3: anti-pattern reference
│   ├── _drafts/           # Auto-captured, pending promotion
│   └── *.md               # Promoted patterns
├── skills/                # Skill definitions
│   ├── dist-check.md
│   ├── dist-design.md
│   └── dist-debug.md
├── templates/
│   └── topology.yaml      # Project topology template
└── docs/                  # Design documents
    ├── design-philosophy.md
    ├── plugin-architecture.md
    ├── reasoning-framework.md
    └── case-study-ai-video-platform.md
```

## Anti-Pattern Catalog Learning Loop

1. New pattern encountered in a session → auto-drafted to `catalog/_drafts/`
2. Same pattern class appears again (or user confirms) → promoted to `catalog/`
3. Patterns are project-agnostic — they describe shapes, not specific systems

## Design Principles

1. Reasoning framework, not documentation system
2. Detection is cheap, reasoning is expensive — keep detection always-on, load reasoning on demand
3. Sequential two-pass analysis — boundary first, then concurrency
4. Auto-update over auto-create — topology manually created, auto-updated
5. Threshold-based learning — new patterns drafted first, promoted on repetition
