# Constraint DSL

Declarative YAML-like language for constraint graphs in the SuperInstance ecosystem.

## Quick Start

```python
from constraint_dsl import load, compile_pipeline, Runtime

pipeline = load("examples/jazz_solo.yaml")
graph = compile_pipeline(pipeline)
result = Runtime(graph).execute({"x": 0.5, "y": 0.3})
print(result.outputs)
```

## Constraint Primitives

| Kind | Description | Core Mapping |
|------|-------------|--------------|
| `snap` | Lattice quantization | `constraint_theory_core.snap` |
| `funnel` | Deadband gravitational pull | `TemporalAgent` |
| `consensus` | Multi-agent agreement | `Metronome` with Laman coupling |
| `laman` | Structural rigidity | `is_laman` / `henneberg_construct` |
| `tempo` | Metronomic constraint | `Metronome` |

## Pipeline Schema

```yaml
name: "My Pipeline"
params:
  bpm: 120
constraints:
  - id: lattice
    kind: snap
    config:
      lattice: A2
      epsilon: 0.15
edges:
  - from: lattice
    to: next_node
```

## Examples

- `examples/jazz_solo.yaml` — bebop solo constraints
- `examples/trap_beat.yaml` — half-time grid with consensus
- `examples/classical_quartet.yaml` — four-voice counterpoint rigidity

## Testing

```bash
pytest tests/ -v
```

34 tests covering parser, compiler, runtime, and integration.
