# AP-1: Tight Retry Loop

## Shape
Error → handler sets component state to "ready/idle" → system immediately dispatches new work → same component, same error → repeat until retries exhausted.

## Detection
Run state-mutation tick trace (3 ticks) on the error handler's state change. If tick 3 recreates tick 1 conditions with the same actor, this is a tight retry loop.

## Symptoms
- Rapid repeated failures from the same component in logs
- Retry budget burned in seconds instead of spread over recovery time
- All retries hit the same broken instance

## Fix
The component that experienced the failure must gate its own readiness. It should verify recovery (health check, reconnect) before advertising availability. The error handler should NOT set the component to "ready" — leave it in a held state until the component itself confirms recovery.
