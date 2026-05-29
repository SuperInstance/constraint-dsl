# constraint-dsl

A declarative YAML-like constraint pipeline language — define constraint workflows as readable config files, compile to executable pipelines.

## What This Gives You

- **YAML-based syntax** — write constraint pipelines as human-readable config files
- **Pipeline compilation** — declarative descriptions compile to optimized execution plans
- **Composable stages** — snap, funnel, consensus, verify, and custom stages chain together
- **Runtime engine** — execute compiled pipelines with built-in error handling and logging
- **Zero dependencies** — pure Python, works everywhere

## Quick Start

```yaml
# pipeline.yaml — a constraint verification pipeline
name: lattice-verify
stages:
  - type: snap
    lattice: eisenstein_a2
    input: points.csv
  - type: funnel
    decay: 0.1
    tolerance: 0.01
  - type: verify
    check: holonomy
    mod: 48
```

```python
from constraint_dsl import compile_pipeline, run_pipeline

# Compile and execute
pipeline = compile_pipeline("pipeline.yaml")
result = run_pipeline(pipeline)
print(result.summary())
```

### Programmatic API

```python
from constraint_dsl import Pipeline, Stage

p = Pipeline("my-check", stages=[
    Stage("snap", lattice="eisenstein_a2"),
    Stage("funnel", decay=0.1, tolerance=0.01),
    Stage("verify", check="holonomy"),
])
result = p.run()
```

## API Reference

| Class / Function | Description |
|---|---|
| `compile_pipeline(path)` | Parse YAML pipeline file to Pipeline object |
| `run_pipeline(pipeline)` | Execute a compiled pipeline |
| `Pipeline(name, stages)` | Build pipeline programmatically |
| `Stage(type, **params)` | Individual pipeline stage |
| `PipelineResult` | Execution result with `.summary()` |

### Stage Types

| Stage | Parameters | Description |
|---|---|---|
| `snap` | `lattice`, `input` | Quantize to lattice |
| `funnel` | `decay`, `tolerance` | Apply deadband funnel |
| `consensus` | `agents`, `coupling` | Run metronome consensus |
| `verify` | `check`, `mod` | Verify holonomy or rigidity |
| `custom` | `module`, `function` | Call user-defined function |

## How It Fits

The **configuration layer** of the constraint theory ecosystem:

- Uses [constraint-theory-core](https://github.com/SuperInstance/constraint-theory-core) primitives under the hood
- Feeds into [constraint-theory-engine-cpp-lua](https://github.com/SuperInstance/constraint-theory-engine-cpp-lua) for high-performance execution
- Pairs with [constraint-substrate](https://github.com/SuperInstance/constraint-substrate) for cross-language pipeline stages

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

## Installation

```bash
pip install constraint-dsl
```

Requires Python ≥ 3.10.

## License

MIT
