---
name: dist-debug
description: This skill should be used when investigating a failure whose symptom and root cause are suspected to live in different independently-deployed processes or services — a consumer failing because of something a producer did, or a downstream service acting on stale or wrong state from an upstream one. Traces backward from symptom to cause boundary and matches known distributed anti-patterns. Not for a single-process bug with a clear stack trace, and not for reviewing a diff you're about to commit — use dist-check for that.
argument-hint: "<symptom description, error message, or log snippet>"
allowed-tools: Read, Grep, Glob
---

# dist-debug — Root Cause Analysis

Start with the supplied symptom, error or log. Establish where it appears, when it happens, and relevant recent changes; ask for missing evidence that would narrow the investigation.

## Trace backward

Read producers, consumers and deployment configuration around the symptom. Use the project's optional `.dist-architect/topology.yaml` (or location in project guidance) as a cache; flag disagreements with code or deploy config and proceed from that evidence. No topology file is required.

Trace from symptom to its dependencies and the operations that produce them:

    Symptom in A <- state/data from B <- operation in C <- possible failure condition

At each hop: could state be unexpected, data stale or missing, or timing/ordering responsible? Did the operation fail, or the channel that watches it? Use [Failure mode](../../modules/failure-mode.md), [State mutation](../../modules/state-mutation.md), [Data lifecycle](../../modules/data-lifecycle.md) or [Interaction](../../modules/interaction.md) where they help. If code and deploy config allow overlapping operations, also use [Concurrency](../../modules/concurrency.md).

Match the symptom and mechanism against the [catalog index](../../catalog/INDEX.md), then read candidate entries.

## Test hypotheses

For each plausible hypothesis, state the cause boundary, mechanism, and what you expect to observe if it is right. Run a discriminating log, query or test check when available and safe within the task's authority. Report the observed result; if you cannot run it, name the exact check and why it remains unrun. Distinguish confirmed causes from hypotheses.

## Trace the fix forward

Follow the proposed fix through the same chain in reverse:

    Fix in C -> changed state/data in B -> resolved dependency in A -> symptom gone?

At each hop: does the fix resolve all data, or only new data? Identify accumulated damage and the cleanup, migration or backfill needed for existing state.

## Capture an unmatched confirmed cause

When evidence confirms a cause matching no catalog entry, write a project-agnostic pattern draft to `.dist-architect/pattern-drafts/<slug>.md` relative to the root of the project being investigated. Include shape, confirming evidence, detection, symptoms and fix, including existing-data cleanup. Avoid secrets and project-specific identifiers. If writing is unavailable, provide the draft and destination and state that it was not saved.

Promotion into the installed plugin's catalog is a manual maintainer step; do not write into the installed plugin.

## Report

Show the backward trace, hypotheses with predicted observations and check results (or unrun checks), and the forward trace including existing-data repair. Mention a matching pattern or saved draft where relevant. Keep the report proportional to the evidence, without empty sections.
