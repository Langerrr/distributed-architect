# Case Study: LLM Limitations in Distributed System Design

> **This is a project-specific case study, not a generic reference.**
> Analysis from a real debugging/design session on an AI video generation platform
> (Redis Streams + FastAPI + WebSocket workers + ComfyUI GPU backend).
> The generic principles extracted from this case study live in `reasoning-framework.md`.
> Date: 2026-02-21

## System Context

```
App (React) → Engine API (FastAPI) → Redis Streams → Consumer/Dispatcher → Worker (WebSocket) → ComfyUI → S3/R2
                                                                                    ↑
                                                                              asyncio process
                                                                              manages ComfyUI
                                                                              lifecycle internally
```

PostgreSQL for job persistence. Engine API, Consumer, and Dispatcher run in the same process. Workers are separate processes on GPU servers.

## The Session: What Happened

Task: Fix Redis NOGROUP error, then improve resilience when ComfyUI (GPU backend) restarts mid-job.

What started as a simple error fix cascaded into a full error handling redesign because each fix exposed a new distributed systems issue that the LLM didn't anticipate.

### Mistakes Made (Chronological)

| # | What LLM Did | What Was Wrong | Root Cause |
|---|-------------|----------------|------------|
| 1 | Proposed `NOT_READY` worker status for ComfyUI-down | BUSY already covers this — engine doesn't need ComfyUI visibility | Leaked internal state across a boundary |
| 2 | Assumed WS disconnect = job failed | WS is monitoring only; ComfyUI may still be executing | Conflated monitoring channel with execution |
| 3 | Proposed storing QueueMessage as JSONB in jobs table | Too large for every job; business logic belongs in app layer | Didn't think about data lifecycle or ownership |
| 4 | Set worker IDLE after COMFYUI_UNREACHABLE requeue | Engine immediately re-dispatches to the same broken worker → tight retry loop | Missed second-order effect across actor boundary |
| 5 | Didn't notice resolved workflow JSON is lost after stream ACK | QueueMessage (with injected workflow) only lives in Redis stream; gone after ACK | Didn't trace data lifecycle across system boundaries |
| 6 | Didn't initially check if DLQ retries and new error-code retries overlap | Two independent retry systems (pre-dispatch vs post-dispatch) could double-count | Incomplete mental model of existing system behavior |

## Analysis: Why Distributed Systems Are Harder for LLMs

### 1. File-Scoped Reasoning vs System-Wide State

**In single-process code**: code path = state transition. Reading a function tells you everything about what state changes occur.

**In distributed systems**: state is spread across Redis, PostgreSQL, worker memory, and ComfyUI — mutated by multiple independent actors. A change in one file can create an invalid state that only manifests when another actor (in a different file, different process) reacts to it.

**Example from session**: Setting worker to IDLE in `server.py` (engine) was locally correct ("error handled, return to default"). But the consumer loop (same process, different module) sees IDLE and dispatches immediately — creating a tight retry loop against a broken worker. The bug isn't in either file alone; it's in the interaction.

**Core limitation**: LLMs reason about code they're currently reading. They don't hold a simultaneous model of all actors and their behaviors.

### 2. Synchronous Mental Models Applied to Async Systems

**Default assumption**: "If I call X and it fails, I know X failed."

**Distributed reality**: Failure of a *monitoring channel* doesn't mean failure of the *operation*. A WebSocket disconnect from ComfyUI means the monitoring connection dropped — ComfyUI's internal execution queue may still be processing the job.

**Example from session**: LLM immediately reported `job:failed` on WebSocket `ConnectionClosed`. User pointed out: must check `/history/{prompt_id}` and `/queue` via HTTP before declaring failure.

**Core limitation**: LLMs default to synchronous, tightly-coupled mental models. In distributed systems, observation and execution are often independent channels.

### 3. Local Data Tracking vs Cross-Boundary Lifecycle

**In single-process code**: data flows through function calls. If you read the call chain, you see the data.

**In distributed systems**: data is serialized, transmitted, deserialized, and stored across multiple systems. The same logical "object" (a QueueMessage) exists in different forms at different times:
1. Created in API route (Python object)
2. Serialized to Redis stream (JSON string)
3. Read by consumer, deserialized (Python object again)
4. Dispatched to worker (subset sent via WebSocket)
5. ACKed from stream (original JSON gone)
6. Worker processes and sends result back

**Example from session**: LLM didn't notice that the resolved workflow JSON (with all injected parameters) is lost at step 5. It was reading `dispatcher.py` in isolation, not tracing the data from birth to death across all systems.

**Core limitation**: LLMs track data within the code they're reading. They don't automatically build a "where does this data exist at time T?" map across system boundaries.

### 4. Single-Hop vs Multi-Hop Effect Chains

**LLMs are good at**: "If I change X, what happens next?" (one hop)

**LLMs miss**: "If I change X, actor A reacts with Y, which causes actor B to do Z, which feeds back to X" (multi-hop feedback loops)

**Example from session**:
- Change: requeue job on COMFYUI_UNREACHABLE, set worker IDLE
- Hop 1: Engine sees worker IDLE ✓
- Hop 2: Engine dispatches next pending job to this worker ✓
- Hop 3: Same worker, same broken ComfyUI, same failure → requeue again
- Hop 4: Repeat until max_retries exhausted — all retries burned on same broken worker

The LLM traced hop 1 but not hops 2-4.

**Core limitation**: LLMs optimize for local correctness. Multi-hop reasoning across actor boundaries requires holding the full system interaction model in context simultaneously.

### 5. Under-Enumeration of Failure Modes

**In single-process code**: failure = exception. Enumerate exception types and you've covered failure modes.

**In distributed systems**, failure includes:
- Network partition (message lost or delayed)
- Partial completion (step N succeeded, step N+1 didn't)
- State divergence (two actors have inconsistent views)
- Stale reads (reading old state while another actor has already changed it)
- Ordering violations (events arrive out of order)
- Cascading failures (one failure triggers others)
- Resource exhaustion under retry storms

**Example from session**: LLM handled the `ConnectionClosed` exception but didn't consider the *partial completion* case: ComfyUI finished the job successfully, but the monitoring WebSocket dropped before the completion message arrived.

**Core limitation**: LLMs enumerate failure modes they've seen in training data. Distributed systems produce combinatorial failure modes that require systematic enumeration at every boundary.

## Proposed Mitigations (Skill/Plugin Design Targets)

### A. System State Machine Document

A structured file listing every entity, possible states, valid transitions, and who triggers each transition:

```yaml
entities:
  worker:
    states: [IDLE, BUSY, OFFLINE]
    transitions:
      IDLE → BUSY: "dispatcher assigns job"
      BUSY → IDLE: "job:completed or job:failed (permanent)"
      BUSY → BUSY: "job:failed (requeued) — stays BUSY until ComfyUI recovers"
      * → OFFLINE: "heartbeat timeout"
    invariants:
      - "BUSY always has exactly one current_job_id"
      - "IDLE never has a current_job_id"

  job:
    states: [QUEUED, PROCESSING, COMPLETED, FAILED]
    transitions:
      QUEUED → PROCESSING: "dispatcher sends to worker"
      PROCESSING → COMPLETED: "worker reports success"
      PROCESSING → FAILED: "worker reports permanent failure"
      PROCESSING → QUEUED: "requeued on transient failure"
    invariants:
      - "PROCESSING always has a worker_id"
      - "QUEUED job's QueueMessage exists in Redis stream OR in-flight cache"
```

**Purpose**: Before making a change, check if it creates a state that violates an invariant or has no valid transition out.

### B. Data Lifecycle Map

For each key data object, document its full lifecycle across system boundaries:

```
QueueMessage lifecycle:
  1. CREATED in API route (adapter builds workflow, serializes to QueueMessage)
  2. STORED in Redis stream via XADD (JSON string)
  3. READ by consumer via XREADGROUP (deserialized to Python)
  4. CACHED in Redis key job:msg:{id} (for requeue on transient failure)
  5. SUBSET sent to worker via WebSocket (JobDispatch — workflows + assets only)
  6. ACKED from stream after successful dispatch (stream copy gone)
  7. DELETED from cache on job:completed or permanent job:failed

  FAILURE POINTS:
  - Between 3→5: no worker available → message stays pending in stream (safe)
  - Between 5→6: worker crashes → cached copy enables requeue
  - After 6: stream copy gone, only cache remains
  - After 7: QueueMessage fully gone — resolved workflow lost forever

  IMPLICATION: If cloning/recreation needed, must persist before step 7
```

**Purpose**: Before changing any component, check what data it holds and what's lost if it fails.

### C. Failure Mode Checklist (Per Boundary)

A systematic prompt to enumerate failures at each inter-component boundary:

```
Boundary: Engine Dispatcher → Worker (WebSocket)
  □ Network: WebSocket send fails silently?
  □ Network: Worker receives but crashes before processing?
  □ Partial: Worker starts job but ComfyUI rejects it?
  □ Stale: Worker was IDLE when selected but became BUSY before message arrived?
  □ Concurrent: Two dispatchers select the same worker simultaneously?
  □ Crash: Worker process dies after receiving dispatch?
  □ Feedback: What does engine do if it never hears back? (timeout)
```

**Purpose**: Force systematic enumeration instead of relying on intuition.

### D. Interaction Trace Validator

Given a change, trace 3-5 system "ticks" forward — not just the happy path:

```
Change: "On COMFYUI_UNREACHABLE, requeue job and set worker IDLE"

Tick 1: Engine receives job:failed with error_code=COMFYUI_UNREACHABLE
Tick 2: Engine requeues job to stream, sets worker IDLE
Tick 3: Consumer reads stream, finds pending job, worker is IDLE → dispatches
Tick 4: Worker receives job, tries ComfyUI → still down → COMFYUI_UNREACHABLE
Tick 5: Back to Tick 1 — LOOP DETECTED ⚠️

Fix: Keep worker BUSY, let worker poll ComfyUI health before sending IDLE
```

**Purpose**: Catch feedback loops and cascading effects before they reach production.

### E. Invariant Registry

System-wide invariants that must hold at all times:

```
INV-1: A job in PROCESSING has exactly one assigned worker in BUSY state
INV-2: A stream message is ACKed only after the worker confirms receipt
INV-3: A requeued job always has its QueueMessage available (cache or stream)
INV-4: A worker in IDLE has no current_job_id and is safe to receive new work
INV-5: Worker sends IDLE only when it can actually accept and execute a job
INV-6: Data required for retry/requeue is never deleted before the operation it enables
```

**Purpose**: Checklist to validate changes against. If a change can violate any invariant, it needs redesign.

## Key Takeaway

The fundamental gap is: **LLMs reason about code locally but distributed systems require global reasoning**. The solution isn't to make the LLM smarter — it's to externalize the system model (state machines, data lifecycles, invariants) so the LLM can check its local reasoning against global correctness.

Every mistake in this session could have been caught by one of these artifacts:
- Mistake 1 (NOT_READY status): State machine shows BUSY already covers "can't accept work"
- Mistake 2 (WS = execution): Data lifecycle shows WS is observation, not execution
- Mistake 3 (JSONB storage): Data lifecycle shows ownership and size concerns
- Mistake 4 (IDLE after requeue): Interaction trace catches the feedback loop at tick 3
- Mistake 5 (workflow JSON lost): Data lifecycle map shows post-ACK data loss
- Mistake 6 (DLQ overlap): Failure mode checklist forces enumeration of all retry paths
