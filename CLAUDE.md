# distributed-architect — Distributed Systems Reasoning Plugin

A reasoning framework that helps LLMs analyze distributed system changes for correctness. Not a documentation system — a structured thinking process.

## Boundary Detector (Always Active)

When working on a distributed system (multiple processes, services, or storage systems communicating), watch for these signals before writing code:

| Signal | You are... | Module |
|--------|-----------|--------|
| Changing state/status that another actor (process, human, or AI agent) reads or reacts to | `state-mutation` | modules/state-mutation.md |
| Moving data across a serialization, network, or storage boundary | `data-lifecycle` | modules/data-lifecycle.md |
| Writing error/retry/timeout handling for cross-component operations | `failure-mode` | modules/failure-mode.md |
| Adding a new message type, API call, or event between components | `interaction` | modules/interaction.md |

**Concurrency signal**: Check the project topology file. If the component you're modifying is on the **"1" side of a 1:N relationship**, also load `modules/concurrency.md`.

**Procedure**: Detect signal → read the relevant module → walk its checklist → if topology shows 1:N, run concurrency pass → flag concerns before writing code. No overhead for single-component changes.

## Skills

| Command | Phase | Purpose |
|---------|-------|---------|
| `/dist-check` | Coding | Two-pass boundary + concurrency analysis on code changes |
| `/dist-design` | Design | Architecture trade-off analysis for distributed decisions |
| `/dist-debug` | Debug | Backward root-cause tracing from symptoms to cause boundary |

## Architecture

Three layers, loaded incrementally to minimize context cost:

**Layer 1 — Boundary Detector** (above — always loaded with this file):
Recognizes when a code change crosses a distributed boundary.

**Layer 2 — Reasoning Modules** (loaded on demand, ~50 lines each):
Five modules covering two dimensions:
- Boundary correctness: `state-mutation`, `data-lifecycle`, `failure-mode`, `interaction`
- Concurrency correctness: `concurrency` (triggered when topology shows 1:N)

**Layer 3 — Anti-Pattern Catalog** (loaded for review/debug):
Named patterns with shape/detection/fix. Growing collection, auto-drafted on discovery.

## Two-Pass Analysis (coding time)
1. **Pass 1 — Boundary correctness**: Does this single operation work correctly across components?
2. **Pass 2 — Concurrency correctness**: Do simultaneous operations conflict? (Only runs when topology indicates 1:N at the boundary.)

Sequential passes — LLMs reason via chain-of-thought, not parallel intuition.

## Project Integration

### Topology File
Each project using this plugin should have a topology file (see `templates/topology.yaml`):
- Manually created during initial codebase exploration
- Auto-updated when code changes affect component relationships
- Captures: components, cardinality (fixed/dynamic/exact counts), communication mechanisms, convergence points

## Key Files

```
distributed-architect/
├── .claude-plugin/
│   └── plugin.json        # Plugin manifest
├── CLAUDE.md              # This file (includes Layer 1 detector)
├── modules/               # Layer 2: reasoning checklists
│   ├── state-mutation.md
│   ├── data-lifecycle.md
│   ├── failure-mode.md
│   ├── interaction.md
│   └── concurrency.md
├── catalog/               # Layer 3: anti-pattern reference
│   ├── _drafts/           # Auto-captured, pending promotion
│   └── *.md               # Promoted patterns
├── skills/                # Registered skills (SKILL.md per skill)
│   ├── dist-check/
│   │   └── SKILL.md
│   ├── dist-design/
│   │   └── SKILL.md
│   └── dist-debug/
│       └── SKILL.md
├── templates/
│   └── topology.yaml      # Project topology template
└── docs/                  # Design documents
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
