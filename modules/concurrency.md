# Concurrency Analysis

Use when: Code and deploy configuration show operations can overlap or multiple actors access the same resource. Optional topology caches that reading; flag disagreements and follow the code and configuration.

Consider concurrency after boundary correctness. Each operation may be individually correct but break when overlapping in time.

## Questions

### 1. Identify Concurrent Actors
From code and deploy configuration, with topology as an optional cache:
- Which components can send to this component simultaneously?
- How many instances can be active? (N dynamic? fixed count?)
- What triggers concurrent operations? (e.g., two service instances completing tasks at the same time)

### 2. Write-Write Conflicts
- Can two actors modify the same state/record/resource simultaneously?
- What's the resolution? Last-write-wins? Atomic operation? Lock?
- If last-write-wins: can a stale write overwrite a newer one?

### 3. Read-Write Races
- Can one actor read state while another is changing it?
- If yes: does the reader make decisions based on potentially stale data?
- What's the consequence of acting on stale data?

Example: Actor reads "instance status: available", assigns a task. But the instance transitioned to "busy" from another assignment a millisecond earlier. Result: two tasks assigned to the same instance.

### 4. Ordering Assumptions
- Does the code assume events arrive in a specific order?
- Across network boundaries, ordering is NOT guaranteed unless the transport enforces it.
- Can "completed" arrive before "started"? Can "retry 2" arrive before "retry 1"?

### 5. Atomicity Gaps
- Is there a multi-step operation that isn't atomic?
- Can another actor see intermediate state between steps?
- Example: "check if available" then "mark as busy" — another actor can check between the two steps.

### 6. Resource Contention
- Can concurrent operations exhaust a shared resource? (connection pool, queue depth, memory)
- Under load, does contention cause timeouts that trigger retries that cause more contention? (thundering herd)
