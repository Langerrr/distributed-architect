# Distributed Systems Reasoning Framework

> Systematic reasoning patterns for LLMs working on distributed systems.
> Project-agnostic. Scale-independent. Applied at the moment of making changes.

## Core Principle

**Every distributed system bug is a failure to reason across a boundary.**

A boundary exists wherever:
- Two processes communicate (network, IPC, shared storage)
- State is observed by more than one actor
- Data crosses a serialization/deserialization point
- An operation's success is reported through a different channel than execution

The framework is organized around **boundary-aware reasoning**: detecting when you're at a boundary and applying the right analysis.

---

## Part 1: Change Classification

Before writing code, classify the change. Most distributed bugs come from one of these change types being handled with single-process thinking.

### Type A: State Mutation Observed by Multiple Actors

**Detection**: You're changing a field/status/flag that another component reads or reacts to.

**Examples**:
- Setting a service instance status to IDLE (scheduler/dispatcher reads this)
- Updating a task status to FAILED (UI polls this, retry logic reads this)
- Deleting a cache key (another process might be reading it)

**Required reasoning**: → Go to Checklist 1 (Observer Trace)

### Type B: Data Crossing a System Boundary

**Detection**: Data is being sent to, stored in, or read from a different component/storage system.

**Examples**:
- Serializing a message to a queue or stream
- Sending a network message to a downstream service
- Acknowledging a queue message (removing data from the queue)
- Writing results to object storage

**Required reasoning**: → Go to Checklist 2 (Data Lifecycle)

### Type C: Error/Failure Handling

**Detection**: You're writing catch/except blocks, retry logic, fallback paths, or timeout handling for cross-component operations.

**Examples**:
- Handling a connection drop to a downstream service
- Retrying a failed task
- Falling back when a dependency is unavailable

**Required reasoning**: → Go to Checklist 3 (Failure Mode Analysis)

### Type D: New Interaction Between Components

**Detection**: You're adding a new message type, API call, or event that creates communication between two components that didn't interact this way before.

**Examples**:
- Adding a health-check ping from orchestrator to service instances
- Adding a callback from a service to the orchestrator on dependency status change
- Adding a new message channel for a different priority level

**Required reasoning**: → Go to Checklist 4 (Interaction Analysis)

---

## Part 2: Reasoning Checklists

### Checklist 1: Observer Trace (State Mutations)

When you change state that other actors observe:

```
1. LIST all actors that read or react to this state.
   (Not just the ones in the current file — think about consumers,
   schedulers, health checkers, UI polling, etc.)

2. For EACH observer, answer:
   a. What does this observer do when it sees the new state value?
   b. Does that action create a side effect?
   c. Does that side effect feed back to the original state? (loop check)

3. TRACE forward 3 ticks:
   Tick 1: State changes to X
   Tick 2: Observer A sees X, does Y
   Tick 3: Y causes... ?
   → If tick 3 leads back to tick 1 conditions: FEEDBACK LOOP detected.

4. CHECK timing: Can an observer see this state BEFORE the operation
   that justified the state change is complete?
   (e.g., instance appears IDLE before it's actually ready to accept work)
```

**Anti-pattern this catches**: Tight retry loops, premature state transitions, cascading state changes.

**Real example**: Setting instance IDLE after requeue → dispatcher assigns new task → same broken instance → same failure → loop.

### Checklist 2: Data Lifecycle (Boundary Crossings)

When data crosses a boundary:

```
1. MAP the full lifecycle of this data:
   - Where is it CREATED? (which component, what triggers creation)
   - Where is it STORED? (which storage systems, in what form)
   - Who READS it? (which components, for what purpose)
   - When is it DELETED? (what triggers removal, from which stores)

2. At EACH transition point, ask:
   a. What happens if this transition fails halfway?
   b. Is there another copy of this data? Where?
   c. If this copy is lost, can the data be reconstructed? From what?

3. CHECK the deletion trigger:
   - Is anything still depending on this data when it's deleted?
   - Is there a window between "no longer in store A" and "safely in store B"?

4. OWNERSHIP: Who is the source of truth for this data at each phase?
   - If two systems hold copies, which one wins on conflict?
```

**Anti-pattern this catches**: Data loss at ACK boundaries, orphaned references, premature cleanup.

**Real example**: Resolved payload lost after queue ACK — only copy was in the queue message, gone once acknowledged.

### Checklist 3: Failure Mode Analysis (Error Handling)

When writing error handling for cross-component operations:

```
1. CLASSIFY the failure:
   - Infrastructure failure: the component is unreachable/broken
     → Likely transient, may recover. Retry is appropriate.
   - Logic/data failure: the operation was rejected on its merits
     → Permanent for this input. Retry wastes resources.
   - Observation failure: the monitoring channel failed, not the operation
     → Operation may still be running. DO NOT assume failure.

2. For infrastructure failures, check:
   a. Will the same component be selected on retry? (→ tight loop risk)
   b. Who manages recovery? (the failed component, or the caller?)
   c. Is there backpressure? (does the retry create load on a struggling system?)

3. For observation failures, check:
   a. Is there an alternative channel to verify the operation's actual status?
   b. What's the cost of assuming failure vs. the cost of checking?
   c. If the operation actually succeeded, does the error handling corrupt state?

4. For ALL failures:
   a. What state is the system in after the error handler runs?
   b. Is this a valid state that has a defined transition out?
   c. Does the error handler create conditions for the SAME error? (loop check)
   d. Is retry idempotent? (Can the operation safely run twice?)

5. CHECK retry amplification:
   - How many layers of retry exist? (application, framework, infrastructure)
   - Can retries from different layers compound?
     (e.g., 3 app retries × 3 infra retries = 9 total attempts)
```

**Anti-pattern this catches**: Channel conflation (monitoring ≠ execution), retry storms, non-idempotent retries, error handlers that trigger themselves.

**Real example**: Event stream disconnect assumed task failed — but the execution backend was still processing. Should verify via status endpoint before declaring failure.

### Checklist 4: Interaction Analysis (New Communication Paths)

When adding new inter-component communication:

```
1. DIRECTION: Is this one-way (fire-and-forget) or request-response?
   - One-way: What if the message is lost? Is that acceptable?
   - Request-response: What's the timeout? What happens on timeout?

2. ORDERING: Does this message have ordering requirements with other messages?
   - Can it arrive before a message it logically depends on?
   - Can it arrive after a message that supersedes it?

3. CONCURRENCY: Can this message arrive while the receiver is processing
   something else?
   - Does the handler need to be re-entrant?
   - Can two instances of this message arrive simultaneously?

4. FEEDBACK: Does the receiver's reaction to this message cause further
   messages back to the sender?
   - Map the full round-trip. Does it converge or oscillate?

5. FAILURE ISOLATION: If this new communication path fails, what's the
   blast radius?
   - Does it affect only the two communicating components?
   - Or does it cascade to other components?
```

**Anti-pattern this catches**: Message ordering bugs, re-entrancy issues, cascading failures from new dependencies, ping-pong message loops.

---

## Part 3: Quick Validation (Pre-Commit Check)

Before finalizing any distributed system change, answer these three questions:

```
Q1: ASSUMPTION — What is the key assumption this change makes about
    other components' behavior?
    (e.g., "instance will verify health before advertising availability")

Q2: VIOLATION — What happens if that assumption is violated?
    (e.g., "instance advertises available immediately → tight dispatch loop")

Q3: DETECTION — How would we know if the assumption is violated
    in production?
    (e.g., "rapid failure events for the same instance in logs")
```

If you can't answer Q2, you don't understand the change well enough.
If Q2 describes a catastrophic outcome and Q3 has no answer, the change needs redesign.

---

## Part 4: Common Anti-Patterns Reference

Quick-reference catalog of distributed anti-patterns, built from real mistakes.

### AP-1: The Tight Retry Loop
**Shape**: Error → handler sets state to "ready" → system immediately retries → same error
**Detection**: Checklist 1 tick trace shows loop back to initial conditions
**Fix**: The component that failed should gate its own readiness (health check before advertising availability)

### AP-2: The Lost Data at ACK
**Shape**: Data exists only in message queue → consumer processes and ACKs → data gone → later need it for retry/audit/clone
**Detection**: Checklist 2 shows deletion before all consumers are done with the data
**Fix**: Cache or persist before ACK. Define explicit lifecycle end condition.

### AP-3: The Channel Conflation
**Shape**: Monitoring channel drops → assume the operation it was monitoring also failed
**Detection**: Checklist 3 classification reveals "observation failure" treated as "operation failure"
**Fix**: Verify operation status through an independent channel before declaring failure.

### AP-4: The Boundary State Leak
**Shape**: Component A exposes internal implementation state to Component B, coupling them unnecessarily
**Detection**: State values that only make sense to one component appear in the interface between components
**Fix**: Expose abstract states (IDLE/BUSY) not implementation states (DEPENDENCY_X_DOWN). Let each component manage its own internals.

### AP-5: The Compounding Retry
**Shape**: Multiple retry layers (app retry × queue retry × infra retry) multiply into retry storms
**Detection**: Checklist 3 step 5 reveals multiple independent retry mechanisms for the same failure
**Fix**: Clearly assign retry responsibility to exactly one layer. Other layers should fail-fast or propagate.

### AP-6: The Premature State Transition
**Shape**: Component advertises new state before it can actually fulfill the contract of that state
**Detection**: Checklist 1 step 4 — observer acts on state before the component is ready
**Fix**: Only transition state after the preconditions for the new state are verified (e.g., health check before IDLE).
