# distributed-architect

A shared Codex and Claude Code plugin for reasoning about distributed boundaries. Install in Codex from the configured `langerrr` marketplace with `codex plugin add distributed-architect@langerrr`, then start a new session. See [README](README.md) for both hosts' usage.

## Boundary signals

This is an optional reference. Claude Code projects can import it into their own guidance; installing the plugin does not make this file passive guidance in every session.

| Change | Questions |
|--------|-----------|
| State/status observed by another process, human or AI agent | [State mutation](modules/state-mutation.md) |
| Data crosses serialization, network, storage or deletion boundaries | [Data lifecycle](modules/data-lifecycle.md) |
| Cross-component errors, retries or timeouts | [Failure mode](modules/failure-mode.md) |
| New message, API call or event | [Interaction](modules/interaction.md) |
| Code and deploy configuration permit overlapping operations | [Concurrency](modules/concurrency.md) |

Consider the boundary first, then concurrency if operations can overlap. An optional project topology file caches the reading of code and deploy configuration. Use it when present, flag disagreements, and follow implementation evidence; neither creating nor editing topology is part of the skills.

## Skills

| Skill | Purpose |
|-------|---------|
| dist-check | Concerns with boundary, mechanism, suggested change, and the change's assumption and failure consequence; one line if no boundary is crossed |
| dist-debug | Backward cause trace, hypotheses with predicted observations and checks, forward fix trace including existing-data cleanup |
| dist-design | Option comparison, recommendation against constraints, and unknowns that could change it |

In Codex invoke `$distributed-architect:dist-check` (or the other skill name); in Claude Code use `/distributed-architect:dist-check`.

The shared [skills directory](skills/) points to [modules](modules/) and the [catalog index](catalog/INDEX.md) using paths relative to each referring file. The host manifests both describe version 0.3.0; Codex's skill root is `./skills/` relative to the plugin root.

## Pattern learning

After confirming a cause matching no catalog entry, dist-debug writes `.dist-architect/pattern-drafts/<slug>.md` in the project being investigated. If writing is unavailable, it provides the draft without claiming it was saved. Drafts describe general patterns and supporting evidence, without secrets or project-specific identifiers. Promotion to `catalog/` and its index is a manual maintainer step after repetition or explicit confirmation.

The [topology template](templates/topology.yaml) is optional. Questions guide investigation; reports do not reproduce every question and answer.
