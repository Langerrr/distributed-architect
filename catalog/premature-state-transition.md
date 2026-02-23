# AP-6: Premature State Transition

## Shape
Component advertises a new state (e.g., "ready", "idle", "available") before it can actually fulfill the contract of that state. Other actors react to the advertised state and send work or requests that the component can't handle yet.

## Detection
Run state-mutation checklist step 4 (timing check). Check whether the preconditions for the new state are verified before the transition.

## Symptoms
- Immediate failures after state transitions ("just said it was ready, now it's failing")
- Race between "advertising ready" and "actually becoming ready"
- Intermittent failures that depend on timing

## Fix
Only transition state after verifying preconditions. Example: don't send "IDLE" after an infrastructure failure — first verify the infrastructure is back (health check, reconnect), then send "IDLE". The state transition is the last step, not the first.
