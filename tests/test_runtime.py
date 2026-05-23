import pytest
from constraint_dsl import parse, compile_pipeline, Runtime, RuntimeError


def test_runtime_snap():
    p = parse("""
name: rt_snap
constraints:
  - id: s
    kind: snap
    config:
      epsilon: 0.5
""")
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute({"x": 0.5, "y": 0.3})
    assert "s" in result.outputs
    assert "point" in result.outputs["s"]
    assert "error" in result.outputs["s"]
    assert result.outputs["s"]["lattice"] == "A2"


def test_runtime_funnel():
    p = parse("""
name: rt_funnel
constraints:
  - id: f
    kind: funnel
    config:
      gravity: 0.5
      decay: exponential
""")
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute({"x": 0.1, "y": 0.2, "t": 1.0})
    assert "f" in result.outputs
    assert "phase" in result.outputs["f"]
    assert "deadband" in result.outputs["f"]


def test_runtime_laman():
    p = parse("""
name: rt_laman
constraints:
  - id: l
    kind: laman
    config:
      num_nodes: 5
      rigid: true
""")
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute()
    assert result.outputs["l"]["n"] == 5
    assert result.outputs["l"]["is_rigid"] is True


def test_runtime_tempo():
    p = parse("""
name: rt_tempo
constraints:
  - id: t
    kind: tempo
    config:
      bpm: 120
      grid: 16
""")
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute()
    assert result.outputs["t"]["tick_count"] == 1
    assert "phase" in result.outputs["t"]


def test_runtime_consensus():
    p = parse("""
name: rt_consensus
constraints:
  - id: c
    kind: consensus
    config:
      voices: 3
      threshold: 0.6
""")
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute({"neighbor_phases": [0.1, 0.2, 0.15]})
    assert "c" in result.outputs
    assert "correction" in result.outputs["c"]


def test_runtime_full_pipeline():
    text = """
name: pipeline
constraints:
  - id: lattice
    kind: snap
    config:
      epsilon: 0.15
  - id: phrase
    kind: funnel
    config:
      gravity: 0.7
      decay: exponential
  - id: timekeeper
    kind: tempo
    config:
      bpm: 120
      grid: 16
edges:
  - from: lattice
    to: phrase
    channel: point
"""
    p = parse(text)
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute({"x": 0.5, "y": 0.3})
    assert "phrase" in result.outputs or "timekeeper" in result.outputs
    assert result.execution_order[0] == "lattice"


def test_runtime_topological_order():
    text = """
name: topo
constraints:
  - id: a
    kind: snap
  - id: b
    kind: snap
  - id: c
    kind: snap
edges:
  - from: a
    to: b
  - from: b
    to: c
"""
    p = parse(text)
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute()
    assert result.execution_order == ["a", "b", "c"]


def test_runtime_data_flow():
    text = """
name: flow
constraints:
  - id: src
    kind: snap
    config:
      epsilon: 0.5
  - id: dst
    kind: funnel
    config:
      gravity: 0.5
edges:
  - from: src
    to: dst
    channel: point
"""
    p = parse(text)
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute({"x": 0.5, "y": 0.3})
    # dst should receive 'point' from src via channel mapping
    assert "dst" in result.node_outputs
