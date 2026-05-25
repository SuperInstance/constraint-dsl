# constraint-dsl

> Declarative YAML language for building constraint pipelines in the SuperInstance ecosystem.

`constraint-dsl` lets you define musical constraint graphs as YAML documents — specifying lattice snapping, funnel resolution, tempo grids, Laman rigidity, and multi-agent consensus — then compile and execute them as directed acyclic graphs. It's the glue between [constraint-theory-core](https://github.com/SuperInstance/constraint-toolkit) and higher-level SuperInstance components.

## How It Works

The pipeline has three stages:

1. **Parse** — YAML document → `Pipeline` object (nodes + edges)
2. **Compile** — `Pipeline` → `ConstraintGraph` (typed executable nodes with cycle detection)
3. **Execute** — `ConstraintGraph` → `RuntimeResult` (topological data-flow walk)

```
YAML → Parser → Pipeline → Compiler → ConstraintGraph → Runtime → RuntimeResult
```

## DSL Syntax

A DSL document is a YAML file with four top-level keys:

```yaml
name: "My Pipeline"
description: "What it does"
params:          # shared parameters (optional)
  bpm: 120
  key_root: 60

constraints:     # list of constraint nodes
  - id: my_snap
    kind: snap
    config:
      lattice: A2
      epsilon: 0.15

  - id: my_tempo
    kind: tempo
    config:
      bpm: 120
      grid: 16

edges:           # directed connections between nodes (optional)
  - from: my_snap
    to: my_tempo
    channel: point     # optional: route specific output field
    weight: 1.0        # optional: edge weight
```

### Constraint Node

Each constraint has:

| Field | Required | Description |
|---|---|---|
| `id` | ✅ | Unique identifier |
| `kind` | ✅ | Constraint type (see below) |
| `config` | ❌ | Type-specific configuration |
| `inputs` | ❌ | Input port names |
| `outputs` | ❌ | Output port names |

### Edge

| Field | Required | Description |
|---|---|---|
| `from` | ✅ | Source node ID |
| `to` | ✅ | Target node ID |
| `channel` | ❌ | Route a specific output field |
| `weight` | ❌ | Edge weight (default 1.0) |

## Constraint Kinds

### `snap` — Lattice snapping

Snaps 2D coordinates to a lattice (A2 by default) with configurable epsilon tolerance.

```yaml
- id: tuning
  kind: snap
  config:
    lattice: A2
    epsilon: 0.15
```

**Runtime output:** `point`, `error`, `safe`, `epsilon`, `lattice`

### `funnel` — Temporal funnel resolution

Applies a temporal agent that resolves values through phases (search → lock → deadband).

```yaml
- id: phrase
  kind: funnel
  config:
    target: 60
    gravity: 0.7
    decay: exponential  # exponential | linear | slow
```

**Runtime output:** `phase`, `error`, `deadband`, `snapped_a`, `snapped_b`

### `tempo` — Metronome / tempo grid

Creates a metronome with configurable BPM, grid subdivision, and allowed drift.

```yaml
- id: timekeeper
  kind: tempo
  config:
    bpm: 180
    grid: 16
    drift: 0.02
```

**Runtime output:** `phase`, `tick_count`, `converged`, `epsilon`, `anomaly_count`

### `laman` — Rigidity constraints

Builds a Laman rigidity graph (using Henneberg construction) to enforce structural constraints.

```yaml
- id: structure
  kind: laman
  config:
    num_nodes: 8
    rigid: true
```

**Runtime output:** `n`, `edges`, `rigid`, `is_rigid`

### `consensus` — Multi-agent consensus

Sets up a multi-agent metronome for ensemble synchronization with configurable voting method.

```yaml
- id: ensemble
  kind: consensus
  config:
    voices: 3
    method: majority
    threshold: 0.6
```

**Runtime output:** `correction`, `converged`, `phase`, `epsilon`

## Examples

### Jazz Solo (Bebop)

```yaml
name: "Jazz Solo Constraints"
description: "Bebop solo pipeline: lattice snap, funnel resolution, tempo grid"
params:
  key_root: 60
  bpm: 180

constraints:
  - id: lattice
    kind: snap
    config:
      lattice: A2
      epsilon: 0.15

  - id: phrase
    kind: funnel
    config:
      target: 60
      gravity: 0.7
      decay: exponential

  - id: timekeeper
    kind: tempo
    config:
      bpm: 180
      grid: 16
      drift: 0.02

  - id: structure
    kind: laman
    config:
      num_nodes: 8
      rigid: true

edges:
  - from: lattice
    to: phrase
    channel: point
```

### String Quartet (Classical)

```yaml
name: "String Quartet Constraints"
params:
  bpm: 90

constraints:
  - id: time
    kind: tempo
    config: { bpm: 90, grid: 16, drift: 0.005 }
  - id: form
    kind: laman
    config: { num_nodes: 4, rigid: true }
  - id: tuning
    kind: snap
    config: { lattice: A2, epsilon: 0.05 }

edges:
  - from: tuning
    to: form
```

### Trap Beat (Half-time)

```yaml
name: "Trap Beat Constraints"
params:
  bpm: 140

constraints:
  - id: grid
    kind: tempo
    config: { bpm: 140, grid: 32, drift: 0.01 }
  - id: ensemble
    kind: consensus
    config: { voices: 3, method: majority, threshold: 0.6 }
  - id: rigidity
    kind: laman
    config: { num_nodes: 3, rigid: true }

edges:
  - from: rigidity
    to: ensemble
    channel: edges
```

## Installation

```bash
pip install constraint-dsl
```

Requires Python ≥ 3.10, PyYAML ≥ 6.0, and `constraint-theory-core`.

## Quick Start

```python
from constraint_dsl import load, compile_pipeline, Runtime

# Parse a DSL file
pipeline = load("examples/jazz_solo.yaml")

# Compile to executable graph
graph = compile_pipeline(pipeline)

# Execute with inputs
runtime = Runtime(graph)
result = runtime.execute({"x": 0.5, "y": 0.3, "t": 0.1})

# Access outputs
print(result.outputs)           # leaf node outputs
print(result.execution_order)   # topological order
print(result.node_outputs)      # all node outputs
```

### Parse from string

```python
from constraint_dsl import parse, compile_pipeline, Runtime

yaml_str = """
name: "Simple"
constraints:
  - id: snap
    kind: snap
    config: { lattice: A2, epsilon: 0.1 }
"""

pipeline = parse(yaml_str)
graph = compile_pipeline(pipeline)
result = Runtime(graph).execute({"x": 1.5, "y": 2.3})
```

### Register custom constraint kinds

```python
from constraint_dsl import register

@register("my_constraint")
def compile_my_constraint(config, params):
    return {"custom_data": config.get("value", 0)}
```

## API Reference

### Parser

| Function | Description |
|---|---|
| `parse(text)` | Parse YAML string → `Pipeline` |
| `load(path)` | Load YAML file → `Pipeline` |

### Data Types

| Type | Description |
|---|---|
| `Pipeline` | Parsed document: name, description, params, constraints, edges |
| `ConstraintNode` | Node: id, kind, config, inputs, outputs |
| `ConstraintEdge` | Edge: source, target, weight, channel |

### Compiler

| Function | Description |
|---|---|
| `compile_pipeline(pipeline)` | Compile → `ConstraintGraph` |
| `register(kind)` | Decorator to register custom constraint kinds |

### Runtime

| Class | Description |
|---|---|
| `Runtime(graph)` | Executor for a compiled graph |
| `.execute(inputs)` | Run graph → `RuntimeResult` |

### Result

| Field | Description |
|---|---|
| `RuntimeResult.outputs` | Leaf node outputs |
| `RuntimeResult.node_outputs` | All node outputs |
| `RuntimeResult.execution_order` | Topological execution order |

### Errors

| Exception | Stage |
|---|---|
| `ParseError` | YAML parsing / validation |
| `CompileError` | Compilation / cycle detection |
| `RuntimeError` | Graph execution |

## Related Repos

- **[constraint-toolkit](https://github.com/SuperInstance/constraint-toolkit)** — Core constraint theory library (lattice snap, Laman rigidity, metronome, funnel)
- **[superinstance-live](https://github.com/SuperInstance/superinstance-live)** — Live session controller using DSL pipelines
- **[plato-client](https://github.com/SuperInstance/plato-client)** — Client for the Plato optimization backend
- **[flux-genome](https://github.com/SuperInstance/flux-genome)** — Genetic algorithm framework for evolving traditions

## License

MIT
