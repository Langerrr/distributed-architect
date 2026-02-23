# Distributed System Boundary Detector

When working on a distributed system (multiple processes, services, or storage systems communicating), watch for these signals before writing code:

## Boundary Signals

| Signal | You are... | Module |
|--------|-----------|--------|
| Changing state/status that another process reads or reacts to | `state-mutation` | modules/state-mutation.md |
| Moving data across a serialization, network, or storage boundary | `data-lifecycle` | modules/data-lifecycle.md |
| Writing error/retry/timeout handling for cross-component operations | `failure-mode` | modules/failure-mode.md |
| Adding a new message type, API call, or event between components | `interaction` | modules/interaction.md |

## Concurrency Signal

Check the project topology file. If the component you're modifying is on the **"1" side of a 1:N relationship** (e.g., one orchestrator handling N service instances), also load `modules/concurrency.md`. Multiple actors can hit this component simultaneously.

## Procedure

1. Detect signal → load the relevant module
2. Walk the module's checklist against your specific change
3. If topology shows 1:N at this boundary → run concurrency pass (second module)
4. Flag concerns before writing code

If no boundary signal is detected, proceed normally — this framework adds no overhead for single-component changes.
