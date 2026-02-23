# distributed-architect

A reasoning framework plugin for [Claude Code](https://claude.ai/code) that helps LLMs catch distributed system bugs before they reach production.

## The Problem

LLMs reason about code **locally** — they read a function, understand its logic, and suggest changes that are locally correct. Distributed systems require **globally correct** changes: every state mutation must be valid from every observer's perspective, including under partial failure.

This gap produces specific, recurring mistakes:
- Setting a service to "idle" without checking if the system will immediately re-dispatch to the same broken instance (tight retry loops)
- Assuming a monitoring channel failure means the operation failed (channel conflation)
- Losing data at acknowledgment boundaries because the only copy was in the queue
- Missing feedback loops that span multiple components

These aren't knowledge gaps — they're reasoning gaps. The LLM knows about distributed systems. It just doesn't systematically apply that knowledge at the moment of writing code.

## How It Works

**Three layers, loaded incrementally to minimize context cost:**

| Layer | What | When Loaded | Context Cost |
|-------|------|-------------|-------------|
| Boundary Detector | Recognizes when a change crosses a distributed boundary | Always (~30 lines in memory) | Near zero |
| Reasoning Modules | Checklists for specific concern types (5 modules) | On signal detection | ~50 lines each |
| Anti-Pattern Catalog | Named patterns with shape/detection/fix | Review or debug mode | ~10 lines each |

**Two-pass analysis at coding time:**
1. **Boundary correctness** — Does this single operation work correctly across components?
2. **Concurrency correctness** — Do simultaneous operations conflict? (Triggered by project topology)

**Three entry points for different phases:**
- `/dist-check` — Coding time: verify changes before committing
- `/dist-design` — Design time: evaluate architecture trade-offs
- `/dist-debug` — Debug time: trace symptoms backward to root cause

## Project Topology

Each project creates a lightweight topology file that captures component relationships and cardinality. This drives analysis decisions:

```yaml
topology:
  - from: api-gateway
    count: 1 (fixed)
    to: task-runner
    count: N (dynamic)
    via: message queue
    notes: "1:N — concurrency on the gateway side"

  - from: task-runner
    count: 1 (fixed)
    to: execution-backend
    count: 1 (fixed, per-runner)
    via: HTTP + event stream
    notes: "1:1 tight coupling"
```

Cardinality determines which analysis is triggered:
- **1:N** — Concurrency analysis mandatory on the "1" side
- **1:1** — Failure cascade analysis
- **N:1** — Bottleneck / SPOF analysis

## Anti-Pattern Catalog

Six patterns identified from real debugging sessions, with more added over time:

| Pattern | Shape |
|---------|-------|
| Tight Retry Loop | Error handler sets state to "ready" -> system immediately retries -> same error |
| Lost Data at ACK | Data only in queue -> consumer ACKs -> data gone -> needed later |
| Channel Conflation | Monitoring channel drops -> assume the monitored operation failed |
| Boundary State Leak | Component exposes internal state across its interface |
| Compounding Retry | Multiple retry layers multiply into retry storms |
| Premature State Transition | Advertise new state before preconditions are verified |

## Usage

Load as a Claude Code plugin:

```bash
claude --plugin-dir /path/to/distributed-architect
```

Skills are registered as `/distributed-architect:dist-check`, etc. Use them during your work:
- `/distributed-architect:dist-check` before committing distributed system changes
- `/distributed-architect:dist-design` when evaluating architecture options
- `/distributed-architect:dist-debug` when investigating cross-component failures

For passive detection, copy `detector.md` content into your project's Claude memory file.

## Design Philosophy

This is a **reasoning coach, not a knowledge base**. It doesn't try to document your system — it teaches the LLM what questions to ask at the right moment. Documents go stale; reasoning patterns don't.

See `docs/design-philosophy.md` for the full rationale.

## Structure

```
distributed-architect/
├── .claude-plugin/
│   └── plugin.json        # Plugin manifest
├── CLAUDE.md              # Plugin instructions (LLM reads this)
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
├── skills/                # Registered skills (SKILL.md per skill)
│   ├── dist-check/
│   │   └── SKILL.md
│   ├── dist-design/
│   │   └── SKILL.md
│   └── dist-debug/
│       └── SKILL.md
├── templates/
│   └── topology.yaml      # Project topology template
└── docs/                  # Design documents & case studies
```
