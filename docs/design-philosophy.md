# distributed-architect: Design Philosophy

> Why a reasoning framework, not a documentation system.

## The Problem with Documents

Documents work for small systems. They fail as systems grow because:

1. **Staleness**: Every code change can invalidate architecture docs. No one keeps them in sync.
2. **Context explosion**: A 10-service system with state machines, data lifecycle maps, and invariant lists for each service produces hundreds of pages. Loading them all defeats the purpose.
3. **Wrong timing**: Documents are read *before* work starts. The critical moment is *during* a change — when the LLM is about to write code that crosses a boundary. That's when distributed reasoning needs to happen.
4. **Diminishing returns**: The more complete the docs, the more time spent maintaining them instead of building. Eventually the docs *are* the project.

## The Real Insight

In the debugging session that motivated this plugin, the user caught every bug the LLM missed — not by reading docs, but by applying a **mental discipline**:

- "What does the orchestrator do when it sees this state?" (trace through observers)
- "What happens to this data after it leaves this component?" (lifecycle thinking)
- "Busy and not-ready are the same from the caller's perspective" (boundary thinking)
- "We can't assume the task failed because the monitoring channel closed" (channel independence)

These are **reasoning patterns** — reusable across any distributed system, any project, any scale. They don't require knowing the full architecture. They require asking the right questions at the right moment.

## Plugin Design Principle

**The plugin is a reasoning coach, not a knowledge base.**

It provides:
- **Structured analysis prompts** that force the LLM to reason about distributed concerns before writing code
- **Checklists triggered by context** (e.g., "you're changing state that another actor observes — trace the observers")
- **Pattern recognition** for common distributed anti-patterns (tight retry loops, data loss at boundaries, channel conflation)
- **Lightweight, project-agnostic guidance** that works whether the system has 3 components or 30

It does NOT try to:
- Replace architecture documentation
- Maintain a complete system model
- Store all state machines and data lifecycles
- Be a source of truth about any specific project

## How It Works (Conceptual)

### Phase 1: Situation Assessment
When facing a distributed system change, the LLM first characterizes what kind of change it is:
- State mutation (who else sees this state?)
- Data transformation (where does this data go next? what if it's lost here?)
- Error handling (what are all the failure modes at this boundary?)
- New interaction (what feedback loops could this create?)

### Phase 2: Guided Reasoning
Based on the change type, apply the relevant reasoning checklist:
- **State change**: Enumerate all observers. Trace 3 ticks forward from each observer's perspective.
- **Data at boundary**: Map the lifecycle — created where, stored where, consumed where, deleted where. What's lost at each transition?
- **Error path**: Distinguish infrastructure failure from logic failure. Check: does the error handler create a state that triggers the same error?
- **New actor interaction**: Check for feedback loops, race conditions, ordering assumptions.

### Phase 3: Validation
Before finalizing the change:
- State the key assumption being made (e.g., "instance will verify health before advertising availability")
- Identify what breaks if the assumption is wrong
- Check if the change is reversible or if failure is catastrophic

## What This Means for Implementation

The plugin will likely be:
1. **A set of skill prompts** that the LLM invokes when working on distributed system changes
2. **Pattern matchers** that detect when a change crosses a component boundary
3. **Reasoning templates** that structure the analysis (not system-specific content)
4. **Anti-pattern catalog** built from real mistakes (like the ones from our session)

The goal: an LLM using this plugin should catch the same bugs that an experienced distributed systems engineer would catch — not by knowing the system, but by knowing what questions to ask.
