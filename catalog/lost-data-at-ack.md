# AP-2: Lost Data at ACK

## Shape
Data exists only in a message queue → consumer reads and processes → ACKs the message (queue deletes it) → later, data is needed for retry, audit, or reproduction → data is gone.

## Detection
Run data-lifecycle map. Look for a deletion trigger (ACK, TTL expiry, overwrite) where downstream consumers or recovery mechanisms still need the data.

## Symptoms
- Retry attempts fail because the original payload can't be reconstructed
- Features that need historical data (cloning, replay, audit) find nothing
- "Data was there a moment ago" mysteries

## Fix
Before the destructive operation (ACK/delete), ensure the data is persisted elsewhere if any future use is possible. Options: cache with TTL (for retry window), persistent store (for long-term needs), or explicit "save" that copies data to durable storage on demand.
