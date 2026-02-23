# AP-4: Boundary State Leak

## Shape
Component A exposes internal implementation details in its interface to Component B. B now depends on A's internals, coupling them unnecessarily and creating confusion about responsibility.

## Detection
State values in the inter-component interface that only make sense to one side. Example: orchestrator tracking "DEPENDENCY_X_DOWN" as a service status — the orchestrator doesn't manage dependency X, the service does.

## Symptoms
- Interface contracts keep changing as internal implementation evolves
- One component making decisions about another component's internals
- Status values that mean the same thing from the observer's perspective but differ internally (e.g., "busy" vs "not-ready" when both mean "don't send work")

## Fix
Expose abstract states at boundaries (IDLE/BUSY/OFFLINE), not implementation states (COMFYUI_DOWN/MODEL_LOADING/GPU_OOM). Each component manages its own internals and only surfaces what the other side needs to act on.
