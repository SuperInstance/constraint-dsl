import pytest
from constraint_dsl import parse, compile_pipeline, CompileError
from constraint_theory_core import TemporalAgent, Metronome


def test_compile_snap():
    p = parse("""
name: snap_test
constraints:
  - id: s
    kind: snap
    config:
      lattice: A2
      epsilon: 0.15
""")
    g = compile_pipeline(p)
    assert "s" in g.nodes
    assert g.nodes["s"].kind == "snap"
    assert g.nodes["s"].obj["lattice"] == "A2"
    assert g.nodes["s"].obj["epsilon"] == 0.15


def test_compile_funnel():
    p = parse("""
name: funnel_test
constraints:
  - id: f
    kind: funnel
    config:
      gravity: 0.8
      decay: linear
""")
    g = compile_pipeline(p)
    assert g.nodes["f"].kind == "funnel"
    assert isinstance(g.nodes["f"].obj, TemporalAgent)


def test_compile_laman_generate():
    p = parse("""
name: laman_gen
constraints:
  - id: l
    kind: laman
    config:
      num_nodes: 6
      rigid: true
""")
    g = compile_pipeline(p)
    assert g.nodes["l"].kind == "laman"
    assert g.nodes["l"].obj["n"] == 6
    assert g.nodes["l"].obj["is_rigid"] is True
    assert len(g.nodes["l"].obj["edges"]) == 9  # 2*6-3


def test_compile_laman_check_provided_edges():
    p = parse("""
name: laman_check
constraints:
  - id: l
    kind: laman
    config:
      num_nodes: 4
      rigid: true
      edges: [[0,1],[0,2],[0,3],[1,2],[1,3]]
""")
    g = compile_pipeline(p)
    assert g.nodes["l"].obj["is_rigid"] is True


def test_compile_tempo():
    p = parse("""
name: tempo_test
constraints:
  - id: t
    kind: tempo
    config:
      bpm: 140
      grid: 32
      drift: 0.01
""")
    g = compile_pipeline(p)
    assert g.nodes["t"].kind == "tempo"
    assert isinstance(g.nodes["t"].obj, Metronome)


def test_compile_consensus():
    p = parse("""
name: consensus_test
constraints:
  - id: c
    kind: consensus
    config:
      voices: 5
      method: majority
      threshold: 0.7
""")
    g = compile_pipeline(p)
    assert g.nodes["c"].kind == "consensus"
    assert g.nodes["c"].obj["voices"] == 5
    assert g.nodes["c"].obj["method"] == "majority"


def test_compile_unknown_kind():
    p = parse("""
name: bad
constraints:
  - id: x
    kind: nonexistent
""")
    with pytest.raises(CompileError, match="Unknown constraint kind"):
        compile_pipeline(p)


def test_compile_cycle_detection():
    p = parse("""
name: cyclic
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
  - from: c
    to: a
""")
    with pytest.raises(CompileError, match="cycle"):
        compile_pipeline(p)


def test_compile_params_fallback():
    p = parse("""
name: params_fallback
params:
  n: 8
  bpm: 90
constraints:
  - id: l
    kind: laman
    config:
      rigid: true
  - id: t
    kind: tempo
    config:
      grid: 16
""")
    g = compile_pipeline(p)
    assert g.nodes["l"].obj["n"] == 8
    # tempo should pick up bpm from params
