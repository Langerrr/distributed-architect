# Anti-Pattern Index

Six patterns identified from real debugging sessions. Match the symptom shape below, then read the linked entry relative to this index for the full shape/detection/fix.

| ID | Pattern | File | Symptom shape |
|----|---------|------|----------------|
| AP-1 | Tight Retry Loop | [tight-retry-loop](tight-retry-loop.md) | Rapid repeated failures from the same component |
| AP-2 | Lost Data at ACK | [lost-data-at-ack](lost-data-at-ack.md) | Data missing that "should be there" |
| AP-3 | Channel Conflation | [channel-conflation](channel-conflation.md) | Operation marked failed but actually succeeded |
| AP-4 | Boundary State Leak | [boundary-state-leak](boundary-state-leak.md) | Component making wrong decisions about another's internal state |
| AP-5 | Compounding Retry | [compounding-retry](compounding-retry.md) | Way more retries than configured |
| AP-6 | Premature State Transition | [premature-state-transition](premature-state-transition.md) | Failures immediately after recovery or a state change |

A confirmed cause with no matching entry is drafted by dist-debug to `.dist-architect/pattern-drafts/<slug>.md` in the project being investigated. Promotion into this catalog and index is a manual maintainer step after repetition or explicit confirmation.
