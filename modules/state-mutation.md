# State Mutation Analysis

Use when: You're changing a state/status/flag that another process, service, or component reads or reacts to.

## Checklist

### 1. Enumerate Observers
List ALL actors that read or react to this state — not just the ones in the current file.
Think: consumers, schedulers, health checkers, UI polling, monitoring, other services, **human users, AI agents**.

**Non-deterministic observers**: Humans and AI agents react based on perceived state and affordances, not deterministic code paths. If state is rendered in a UI or consumed by an agent's decision loop, ask: "what action does this state *afford* the observer?" A button that looks clickable will be clicked. An agent that sees a status value will act on it. Trace their likely reactions the same way you trace a process — but account for the fact that their behavior is driven by what they *see*, not what the system *intends*.

### 2. Trace Each Observer's Reaction
For each observer:
- What does it do when it sees the new state value?
- Does that action produce a side effect?
- Does that side effect change state that feeds back to the original? (loop check)

### 3. Tick Forward (3 ticks minimum)
```
Tick 1: State changes to [new value]
Tick 2: Observer [name] sees [new value], does [action]
Tick 3: [action] causes [consequence]
→ Does tick 3 recreate tick 1 conditions? If yes: FEEDBACK LOOP.
```

### 4. Timing Check
Can an observer see this state BEFORE the operation that justified the state change is complete?

Example: component advertises "ready" before it can actually handle requests → premature state transition.

### 5. Validity Check
Is the new state a valid state with a defined transition out? Or can the system get stuck?

## Red Flags
- State set to "available/idle/ready" inside an error handler (is the component actually ready?)
- State visible to remote actors before local preconditions are met
- Multiple observers that can react to the same state change simultaneously
