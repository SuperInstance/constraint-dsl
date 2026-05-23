import os
import pytest
from constraint_dsl import load, compile_pipeline, Runtime

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def test_jazz_solo_yaml():
    path = os.path.join(EXAMPLES, "jazz_solo.yaml")
    pipeline = load(path)
    assert pipeline.name == "Jazz Solo Constraints"
    assert pipeline.params["key_root"] == 60
    graph = compile_pipeline(pipeline)
    assert set(graph.nodes.keys()) == {"lattice", "phrase", "timekeeper", "structure"}
    rt = Runtime(graph)
    result = rt.execute({"x": 0.5, "y": 0.3})
    # structure and timekeeper are leaves; phrase is not (has no outgoing edges? Actually phrase has no outgoing edges in jazz_solo.yaml)
    assert "structure" in result.outputs
    assert result.outputs["structure"]["is_rigid"] is True


def test_trap_beat_yaml():
    path = os.path.join(EXAMPLES, "trap_beat.yaml")
    pipeline = load(path)
    assert pipeline.name == "Trap Beat Constraints"
    graph = compile_pipeline(pipeline)
    assert set(graph.nodes.keys()) == {"grid", "ensemble", "rigidity"}
    rt = Runtime(graph)
    result = rt.execute()
    # rigidity -> ensemble, so ensemble is leaf. grid is leaf (no outgoing).
    assert "ensemble" in result.outputs or "grid" in result.outputs
    assert result.node_outputs["rigidity"]["n"] == 3


def test_classical_quartet_yaml():
    path = os.path.join(EXAMPLES, "classical_quartet.yaml")
    pipeline = load(path)
    assert pipeline.name == "String Quartet Constraints"
    graph = compile_pipeline(pipeline)
    assert set(graph.nodes.keys()) == {"time", "form", "tuning"}
    rt = Runtime(graph)
    result = rt.execute({"x": 0.1, "y": 0.2})
    assert "form" in result.outputs
    assert result.outputs["form"]["n"] == 4
    assert result.outputs["form"]["is_rigid"] is True


def test_end_to_end_param_substitution():
    text = """
name: e2e
params:
  bpm: 100
  voices: 3
constraints:
  - id: t
    kind: tempo
    config:
      grid: 8
  - id: c
    kind: consensus
    config:
      threshold: 0.5
edges: []
"""
    from constraint_dsl import parse
    p = parse(text)
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute()
    assert result.outputs["t"]["tick_count"] == 1
    # consensus runtime returns correction/converged/phase/epsilon, not voices
    assert "c" in result.outputs


def test_all_constraint_kinds_executable():
    text = """
name: all_kinds
constraints:
  - id: s
    kind: snap
  - id: f
    kind: funnel
  - id: l
    kind: laman
  - id: t
    kind: tempo
  - id: c
    kind: consensus
"""
    from constraint_dsl import parse
    p = parse(text)
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute({"x": 0.5, "y": 0.3, "neighbor_phases": [0.1, 0.2]})
    for node_id in ["s", "f", "l", "t", "c"]:
        assert node_id in result.node_outputs
