# INTEGRATION.md — constraint-dsl

## Role in the SuperInstance Ecosystem

constraint-dsl is the **declarative front-end** for constraint-dynamics-rs. It compiles YAML-like pipeline definitions into executable constraint graphs, enabling non-Rust code (Python, live performance systems) to define and run constraint systems without writing solver code directly.

## SuperInstance Integration Points

### 1. constraint-dynamics-rs — Native Backend
- `parser.load(path)` reads a `.yaml` pipeline definition
- `compiler.compile_pipeline(pipeline)` emits a `ConstraintGraph` with `CompiledNode` objects
- `runtime.Runtime(graph).execute(inputs)` runs the graph topologically
- The DSL is a thin layer: all heavy lifting (backtracking, propagation, energy landscapes) is delegated to constraint-dynamics-rs

### 2. superinstance-live — Live Constraint Pipelines
- `ConstraintHost` (superinstance-live) instantiates `FluxRoomPipeline`, `CounterpointPipeline`, `GroovePipeline`
- Each pipeline can be defined in constraint-dsl YAML and compiled at session start
- Example: a counterpoint pipeline might declare voice-leading rules as DSL constraints, compiled once and executed per transport tick
- `set_param` calls map to runtime input mutations; `trigger` maps to `Runtime.execute()`

### 3. si-runtime-python — Pythonic Constraint Definitions
- si-runtime-python agents can write constraint specs in Python dicts, serialized to YAML, and fed to constraint-dsl
- `si_runtime.cell.Cell` can emit a constraint spec describing its local capability graph
- The spec is compiled and solved to determine optimal message routing

### 4. creative-engine-rust — Creative Regime as DSL Parameter
- The DSL supports a top-level `regime` field: `FixedPoint | Periodic | Chaotic`
- The compiler reads this and sets default `Constraint.strength` values:
  - FixedPoint: 0.9 (tight)
  - Periodic: 0.6 (balanced)
  - Chaotic: 0.3 (loose)
- This couples creative-engine-rust dynamics to constraint hardness without code changes

### 5. plato-adapters — Adapter-Driven I/O
- `plato-adapters` provides `AdapterRegistry` for transforming external data into DSL-compatible inputs
- Example: MIDI note events → `ConstraintNode` variables; hyperbolic embeddings → `ConstraintEdge` weights
- `AdapterRegistry.chain(["midi_to_notes", "notes_to_variables"])` feeds directly into `Runtime.execute()`

### 6. si-cli — Scan & Rank
- `si-cli scan` discovers `.yaml` and `.yml` files and classifies them as `constraint-dsl` pipelines
- `si-cli rank` includes DSL pipeline count in repo metrics (more pipelines = higher capability surface)
- `si-cli check` validates that all referenced DSL files compile successfully

## Dial / Room / Snap Compatibility

| Primitive | Mapping |
|-----------|---------|
| **Dial**  | Pipeline-level `tolerance` field ∈ [0, 1]; 1.0 = strict (all hard constraints), 0.0 = permissive |
| **Room**  | Each `Pipeline` instance is a Room; variables are local, edges define message passing |
| **Snap**  | `compiler.compile_pipeline(..., mode=Snap)` forces all constraints to hard, ignores tolerance |
| **Cascade**| Child pipelines inherit parent `default_strength` and variable bindings via `Pipeline::merge()` |

## Energy Conservation

DSL pipelines carry an implicit energy budget:
- Each `ConstraintNode` has a `cost` field (default 1.0)
- Total pipeline cost = Σ node costs + Σ edge traversal costs
- `Runtime.execute()` aborts with `EnergyExceeded` if cumulative cost exceeds `pipeline.budget`
- Budget defaults are drawn from `si-runtime-python.Budget` when available

## Quick Start

```python
from constraint_dsl import parser, compiler, runtime

pipeline = parser.load("counterpoint.yaml")
graph = compiler.compile_pipeline(pipeline)
result = runtime.Runtime(graph).execute(inputs={"key": "C_major"})
print(result.assignments)
```

Example YAML:
```yaml
name: counterpoint_voices
regime: Periodic
budget: 10.0
nodes:
  - id: soprano
    domain: [60, 62, 64, 65, 67]
    cost: 1.0
  - id: alto
    domain: [48, 50, 52, 53, 55]
    cost: 1.0
edges:
  - from: soprano
    to: alto
    constraint: interval_leq_8ve
    strength: 0.8
```

## Tests

```bash
pytest tests/
```

Parser, compiler, and runtime tests cover YAML loading, topological execution, and energy-budget enforcement.
