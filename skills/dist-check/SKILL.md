---
name: dist-check
description: This skill should be used before committing a code change that crosses a boundary between independently-deployed processes or services — a new API call, a message queue producer/consumer, a database write another service reads, or a new field in a wire format. Runs a two-pass boundary-correctness and concurrency check. Not for changes confined to a single process or service (ordinary refactors, a frontend calling its own backend), and not for tracing an unknown symptom back to its root cause — use dist-debug for that.
argument-hint: "[path] | --staged | --diff <range>"
allowed-tools: Read, Grep, Glob, Bash(git:*)
---

# dist-check — Boundary Analysis

Analyze a supplied path, staged changes (`git diff --cached`), or a diff range (`git diff <range>`). With no scope supplied, use `git diff`; if it is empty, ask what change to analyze. Read callers and consumers needed to understand the changed boundary.

## Find the boundary

Which independently deployed components exchange data or react to changed state? If the change crosses no boundary, respond with one line: "No boundary crossing detected."

Read the questions relevant to the change:

| Change | Questions |
|--------|-----------|
| State/status another actor observes | [State mutation](../../modules/state-mutation.md) |
| Serialization, transfer, storage or deletion | [Data lifecycle](../../modules/data-lifecycle.md) |
| Cross-component errors, retries or timeouts | [Failure mode](../../modules/failure-mode.md) |
| Messages, API calls or events | [Interaction](../../modules/interaction.md) |

Use these questions to investigate concerns; they are prompts for reasoning, not a questionnaire to reproduce in the report.

## Can two of these run at once?

Read code and deploy configuration for concurrent requests, tasks, consumers, replicas and shared resources. If operations can overlap, read [Concurrency](../../modules/concurrency.md) after considering the individual operation.

Use the project's optional `.dist-architect/topology.yaml` (or location named by project guidance) as a cache of that reading. If it disagrees with code or deploy config, say where and use the implementation evidence. Missing topology is no barrier. If deployment information is unavailable, state the assumption about overlap and what breaks if it is wrong. Do not edit topology as part of the check.

Read the [catalog index](../../catalog/INDEX.md) and open entries matching the mechanism you find.

## Report

Report only concerns found: boundary, mechanism (with code evidence), and suggested change. State the assumption the change rests on and what breaks if it is wrong. Include topology disagreements here when they affect that assumption. If boundary analysis finds no concerns, say so briefly and state the key assumption and its failure consequence. Omit question-by-question answers, empty sections and N/A entries.
