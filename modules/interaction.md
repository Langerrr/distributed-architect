# Interaction Analysis

Use when: Adding a new message type, API call, event, or communication path between components.

## Checklist

### 1. Direction and Delivery
- Is this one-way (fire-and-forget) or request-response?
- **One-way**: What if the message is lost? Is that acceptable? Who detects the loss?
- **Request-response**: What's the timeout? What state is the caller in during the wait?

### 2. Ordering
- Does this message have ordering requirements with other messages?
- Can it arrive before a message it logically depends on?
- Can it arrive after a message that supersedes it?
- If ordering matters: is it enforced by the transport, or assumed?

### 3. Receiver State
- Can this message arrive while the receiver is processing something else?
- Does the handler need to be re-entrant (safe to run concurrently with itself)?
- What if the receiver is in an unexpected state when the message arrives?

### 4. Feedback Loops
- Does the receiver's reaction cause a message back to the sender?
- Map the full round-trip: A sends → B reacts → B sends → A reacts → ...
- Does the chain converge (stabilize) or oscillate (ping-pong)?

### 5. Failure Isolation
- If this new communication path fails, what's the blast radius?
- Does it affect only the two components, or cascade to others?
- Does adding this path create a new dependency that didn't exist before?
- Can the system degrade gracefully if this path is unavailable?

### 6. Topology Impact
- Does this change the project topology? (new edge in the communication graph)
- Does it change cardinality? (e.g., now N components send this message type)
- Update the topology file if the communication graph changes.

## Red Flags
- Bidirectional messaging without a convergence guarantee (possible ping-pong)
- Ordering assumed but not enforced by the transport mechanism
- New dependency path that makes a previously independent component coupled
- Message handler that modifies shared state without considering concurrent delivery
