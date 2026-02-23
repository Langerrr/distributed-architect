# AP-3: Channel Conflation

## Shape
A monitoring/observation channel (event stream, log stream, polling connection) drops → code assumes the operation being monitored also failed → marks the operation as failed → but the operation is still running or already succeeded.

## Detection
Run failure-mode classification. If the failure is classified as "observation" but the handler treats it as "operation failure," this is channel conflation.

## Symptoms
- Operations marked as failed that actually completed successfully
- Duplicate work (operation retried because the original was falsely marked failed)
- Inconsistent state (result exists in output store but task record says "failed")

## Fix
When a monitoring channel fails, verify the operation's actual status through an independent channel (HTTP status endpoint, database query, output store check) before declaring failure. Treat observation failure and operation failure as fundamentally different error types.
