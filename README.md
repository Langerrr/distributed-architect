# distributed-architect

Questions that help models catch bugs across independently deployed processes and services. The plugin works in Codex and Claude Code, with one shared copy of each skill.

## Install and use

With the `langerrr` marketplace configured in Codex:

```bash
codex plugin add distributed-architect@langerrr
```

Start a new session, then invoke `$distributed-architect:dist-check`, `$distributed-architect:dist-debug`, `$distributed-architect:dist-design`, or `$distributed-architect:async-reasoning`.

For Claude Code:

```bash
claude --plugin-dir /path/to/distributed-architect
```

Invoke `/distributed-architect:dist-check`, `/distributed-architect:dist-debug`, `/distributed-architect:dist-design`, or `/distributed-architect:async-reasoning`.

| Skill | Use |
|-------|-----|
| dist-check | Review a path, staged changes or diff range for boundary concerns and the assumptions the change rests on |
| dist-debug | Trace a symptom backward, test hypotheses against predicted observations, then trace a fix forward through existing and new data |
| dist-design | Compare architecture options and flag unknowns that could change the recommendation |
| async-reasoning | Reason about async state within one component: stale reads, init order, write-then-read gaps, races |

The skills load relevant questions from five modules: state mutation, data lifecycle, failure mode, interaction and concurrency. They consult six catalog patterns for known mechanisms. Reports focus on findings, not a filled-out questionnaire; a change crossing no boundary gets one line.

## Project topology

Code and deploy configuration answer: can two of these operations run at once? If so, dist-check considers concurrency after the individual operation.

An optional `.dist-architect/topology.yaml` (or a location named in project guidance) caches component relationships and cardinality. The skills use it when present and flag disagreements with code or deployment evidence. It is never required or automatically edited. [The topology template](templates/topology.yaml) is available for projects that want one.

## Pattern drafts

When dist-debug confirms a cause matching no catalog entry, it writes `.dist-architect/pattern-drafts/<slug>.md` in the project being investigated. Drafts contain the general failure shape, evidence, detection, symptoms and fix. If writing is unavailable, it supplies the draft and says it was not saved. Promotion into `catalog/` is a manual maintainer step after repetition or explicit confirmation.

## Layout

- `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`: host manifests.
- `skills/`: the three shared skills.
- `modules/`: questions loaded for the relevant boundary.
- `catalog/`: index and promoted patterns.
- `CLAUDE.md`: optional boundary-signal reference; Claude Code projects can import it into their own guidance.
- `templates/`: optional topology template.
- `docs/`: design rationale and case studies.

An installed plugin's `CLAUDE.md` is not automatically loaded into every Claude Code session. Invoke a skill directly, or opt into the signal reference through project guidance.

Run the portable surface checks with `python3 -m unittest discover -s tests -v`.
