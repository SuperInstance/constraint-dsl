# constraint-dsl

> YAML-based DSL for defining constraint pipelines — write music theory as data, not code

Part of the [SuperInstance](https://github.com/SuperInstance) music constraint theory ecosystem. Provides a declarative YAML syntax for defining constraint satisfaction pipelines: you describe *what* musical constraints you want (no parallel fifths, swing rhythm, spectral density below 0.6) and the engine figures out *how* to satisfy them.

## What It Does

Instead of writing procedural code to enforce musical rules, you write YAML documents that declare constraint pipelines. Each pipeline is a directed graph of **nodes** (constraint checks, transformations, generators) connected by **edges** (data flow). The DSL parser compiles these into executable pipelines that the [constraint-toolkit](https://github.com/SuperInstance/constraint-toolkit) engine solves.

The DSL ships with example pipelines for common musical scenarios: `jazz_solo`, `trap_beat`, and `classical_quartet`. These demonstrate how to encode tradition-specific constraints as data — a core SuperInstance principle.

## Key Features

- **YAML syntax** — human-readable, diffable, version-controllable constraint definitions
- **Pipeline graphs** — nodes + edges define data flow through constraint stages
- **Built-in node types** — generators, filters, transformers, validators
- **Example pipelines** — `jazz_solo`, `trap_beat`, `classical_quartet` included
- **Parser + Compiler + Runtime** — full pipeline from YAML text to executable constraint solver
- **Composable** — pipelines can import and extend other pipelines

## Installation

```bash
git clone https://github.com/SuperInstance/constraint-dsl.git
cd constraint-dsl
pip install -e ".[dev]"
```

Requires Python 3.11+.

## DSL Syntax Reference

### Minimal Pipeline

```yaml
name: my_pipeline
version: "1.0"

nodes:
  generate:
    type: generator
    params:
      dial: harmonic_tension
      range: [0.2, 0.8]

  constrain:
    type: filter
    params:
      rule: no_parallel_fifths
      tolerance: 0.0

edges:
  - [generate, constrain]
```

### Jazz Solo Pipeline (excerpt)

```yaml
name: jazz_solo
version: "1.0"

nodes:
  harmonic_seed:
    type: generator
    params:
      dial: harmonic_tension
      range: [0.5, 0.9]
      tradition: jazz

  rhythm_seed:
    type: generator
    params:
      dial: rhythmic_complexity
      range: [0.6, 0.85]
      tradition: jazz

  swing_filter:
    type: transformer
    params:
      operation: apply_swing
      ratio: 0.67    # Triplet swing

  chord_quality:
    type: filter
    params:
      rule: acceptable_voicing
      allow: [maj7, min7, dom7, dim7, half_dim, alt]

  spectral_gate:
    type: filter
    params:
      dial: spectral_density
      max: 0.7

edges:
  - [harmonic_seed, chord_quality]
  - [rhythm_seed, swing_filter]
  - [chord_quality, spectral_gate]
  - [swing_filter, spectral_gate]
```

### Trap Beat Pipeline (excerpt)

```yaml
name: trap_beat
version: "1.0"

nodes:
  hi_hat_pattern:
    type: generator
    params:
      dial: rhythmic_complexity
      range: [0.7, 0.95]
      subdivision: 16

  808_bass:
    type: generator
    params:
      dial: spectral_density
      range: [0.8, 1.0]
      waveform: sine
      saturation: high

edges:
  - [hi_hat_pattern, output]
  - [808_bass, output]
```

### Node Types

| Type | Purpose | Key Params |
|---|---|---|
| `generator` | Produce initial musical material | `dial`, `range`, `tradition` |
| `filter` | Remove constraint violations | `rule`, `tolerance`, `allow`/`deny` |
| `transformer` | Modify material | `operation`, params vary |
| `validator` | Check final output passes constraints | `rules` list |
| `output` | Terminal node — collects results | `format` |

## Usage

### Parse and run a pipeline

```python
from constraint_dsl import parse, compile_pipeline, Runtime

# Parse YAML into AST
ast = parse("pipelines/jazz_solo.yaml")

# Compile to executable pipeline
pipeline = compile_pipeline(ast)

# Run with the constraint toolkit engine
runtime = Runtime()
result = runtime.execute(pipeline)

for solution in result.solutions:
    print(solution)
```

### Programmatic pipeline construction

```python
from constraint_dsl import PipelineBuilder

pipeline = (
    PipelineBuilder("my_custom")
    .add_node("gen", type="generator", params={"dial": "harmonic_tension", "range": [0.3, 0.7]})
    .add_node("filter", type="filter", params={"rule": "no_parallel_fifths"})
    .add_edge("gen", "filter")
    .build()
)
```

## Architecture

```
constraint_dsl/
├── parser.py      # YAML → AST
├── compiler.py    # AST → executable pipeline
├── runtime.py     # Pipeline execution engine
├── nodes.py       # Built-in node type implementations
└── examples/
    ├── jazz_solo.yaml
    ├── trap_beat.yaml
    └── classical_quartet.yaml
```

### Pipeline Lifecycle

```
YAML file → Parser → AST → Compiler → Pipeline → Runtime → Solutions
```

## Testing

```bash
pytest                            # Run all tests
pytest tests/test_parser.py       # Parser tests
pytest tests/test_compiler.py     # Compiler tests
pytest tests/test_runtime.py      # Runtime execution tests
pytest tests/test_examples.py     # Validate example pipelines
```

## Related Repos

- [**constraint-toolkit**](https://github.com/SuperInstance/constraint-toolkit) — Core constraint satisfaction engine that executes compiled pipelines
- [**constraint-dialect**](https://github.com/SuperInstance/constraint-dialect) — Alternative DSL with different syntax tradeoffs
- [**superinstance-live**](https://github.com/SuperInstance/superinstance-live) — Live controller that loads DSL pipelines
- [**flux-genome**](https://github.com/SuperInstance/flux-genome) — Genetic evolution engine for generating constraint parameters
- [**flux-hyperbolic**](https://github.com/SuperInstance/flux-hyperbolic) — Hyperbolic tradition embeddings used by tradition-aware nodes

## License

MIT
