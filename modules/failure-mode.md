# Failure Mode Analysis

Use when: Writing error handling, retry logic, timeout handling, or fallback paths for cross-component operations.

## Checklist

### 1. Classify the Failure
Which type is this?

| Type | Description | Typical response |
|------|------------|-----------------|
| **Infrastructure** | Component unreachable, network down, service crashed | Transient — retry is appropriate |
| **Logic/Data** | Operation rejected on its merits (bad input, validation failure) | Permanent — retry wastes resources |
| **Observation** | Monitoring channel failed, not the operation itself | Operation may still be running — verify before assuming failure |

Getting this classification wrong is the most common distributed error handling mistake.

### 2. Infrastructure Failure Checks
- Will the SAME component be selected on retry? (→ tight loop risk)
- Who manages recovery — the failed component or the caller?
- Does the retry create load on an already struggling system? (backpressure)
- Is there a circuit breaker or cooldown before retry?

### 3. Observation Failure Checks
- Is there an alternative channel to verify the operation's actual status? (e.g., polling endpoint when an event stream drops)
- What's the cost of assuming failure vs. checking?
- If the operation actually succeeded, does the error handler corrupt state? (e.g., marking a completed task as failed)

### 4. Post-Handler State
- What state is the system in after the error handler runs?
- Is this a valid state with a defined transition out?
- Does the error handler create conditions for the SAME error? (loop check — same as state-mutation tick trace)
- Is retry idempotent? Can the operation safely run twice?

### 5. Retry Amplification
- How many layers of retry exist? (application, queue/framework, infrastructure)
- Can retries from different layers compound? (3 app retries x 3 queue retries = 9 attempts)
- Is retry responsibility assigned to exactly one layer?

## Red Flags
- Monitoring channel failure treated as operation failure
- Error handler sets component to "ready" without verifying readiness
- Multiple independent retry mechanisms for the same failure path
- No distinction between "retriable" and "permanent" in the error code design
