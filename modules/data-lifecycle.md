# Data Lifecycle Analysis

Use when: Data is crossing a system boundary — being serialized, sent, stored in another system, or deleted from one.

## Checklist

### 1. Map the Full Lifecycle
For the data object in question, trace:
- **Created**: Which component, what triggers creation?
- **Stored**: Which storage systems hold it, in what form (serialized? subset? transformed)?
- **Read**: Which components consume it, for what purpose?
- **Deleted**: What triggers removal, from which stores?

### 2. Check Each Transition for Failure
At every point where data moves between systems:
- What happens if this transition fails halfway?
- Is there another copy of this data somewhere?
- If this copy is lost, can the data be reconstructed? From what source?

### 3. Check the Deletion Trigger
- Is anything still depending on this data when it's deleted?
- Is there a window between "removed from store A" and "safely in store B"? (the gap)
- Could a retry or recovery mechanism need this data after deletion?

### 4. Ownership
- Who is the source of truth at each phase of the lifecycle?
- If two systems hold copies, which one wins on conflict?
- Is the data's lifecycle tied to a business decision (e.g., "user chooses to save") or automatic?

### 5. Size and Storage Appropriateness
- Is the data too large for the storage mechanism? (e.g., large JSON in a DB row)
- Is every-record storage justified, or should it be selective/on-demand?
- Does the storage choice match the access pattern (frequent reads vs. archival)?

## Red Flags
- Data exists in only one place with no copy before a destructive operation (ACK, delete, overwrite)
- "Source of truth" ambiguous — two systems both claim to own the data
- Automatic storage of large payloads that only matter in rare cases
