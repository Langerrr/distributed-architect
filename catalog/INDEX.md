# Anti-Pattern Index

Six patterns identified from real debugging sessions. Match the symptom shape below, then read `${CLAUDE_PLUGIN_ROOT}/catalog/<file>` for the full shape/detection/fix.

| ID | Pattern | File | Symptom shape |
|----|---------|------|----------------|
| AP-1 | Tight Retry Loop | tight-retry-loop.md | Rapid repeated failures from the same component |
| AP-2 | Lost Data at ACK | lost-data-at-ack.md | Data missing that "should be there" |
| AP-3 | Channel Conflation | channel-conflation.md | Operation marked failed but actually succeeded |
| AP-4 | Boundary State Leak | boundary-state-leak.md | Component making wrong decisions about another's internal state |
| AP-5 | Compounding Retry | compounding-retry.md | Way more retries than configured |
| AP-6 | Premature State Transition | premature-state-transition.md | Failures immediately after recovery or a state change |

A pattern encountered during a session that doesn't match any entry here goes in `_drafts/` first. Promote it to this index only after the same pattern class appears a second time, or the user explicitly confirms it.
