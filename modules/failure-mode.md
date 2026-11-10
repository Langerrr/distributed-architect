# Failure Mode Analysis

Use when: Writing error handling, retry logic, timeout handling, or fallback paths for cross-component operations.

## Questions

### 1. Classify the Failure
- Did the operation fail, or the channel that watches it?
- Was the component unreachable, or did it reject the input on its merits?
- What evidence distinguishes transient infrastructure failure from permanent logic/data failure?

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
