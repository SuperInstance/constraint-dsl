"""Tests targeting previously uncovered lines in parser, compiler, and runtime."""

import pytest
from constraint_dsl import parse, compile_pipeline, Runtime, ParseError, CompileError
from constraint_dsl.compiler import register, _REGISTRY


# ── Parser gaps ──────────────────────────────────────────────────────────

def test_parse_top_level_non_dict():
    """Non-mapping top-level should raise ParseError."""
    with pytest.raises(ParseError, match="YAML mapping"):
        parse("[1, 2, 3]")


def test_parse_non_string_name():
    with pytest.raises(ParseError, match="'name' must be a string"):
        parse("name: 42\nconstraints: []\n")


def test_parse_non_string_description():
    with pytest.raises(ParseError, match="'description' must be a string"):
        parse("name: x\ndescription: 99\nconstraints: []\n")


def test_parse_non_list_constraints():
    with pytest.raises(ParseError, match="'constraints' must be a list"):
        parse("name: x\nconstraints: oops\n")


def test_parse_non_list_edges():
    with pytest.raises(ParseError, match="'edges' must be a list"):
        parse("name: x\nconstraints: []\nedges: oops\n")


def test_parse_constraint_non_mapping():
    with pytest.raises(ParseError, match="constraints\\[0\\] must be a mapping"):
        parse("name: x\nconstraints: [42]\n")


def test_parse_constraint_non_string_id():
    with pytest.raises(ParseError, match=r"constraints\[0\]\.id must be a string"):
        parse("name: x\nconstraints:\n  - id: 123\n    kind: snap\n")


def test_parse_constraint_non_string_kind():
    with pytest.raises(ParseError, match=r"constraints\[0\]\.kind must be a string"):
        parse("name: x\nconstraints:\n  - id: a\n    kind: 123\n")


def test_parse_constraint_non_dict_config():
    with pytest.raises(ParseError, match="config must be a mapping"):
        parse("name: x\nconstraints:\n  - id: a\n    kind: snap\n    config: bad\n")


def test_parse_edge_non_mapping():
    with pytest.raises(ParseError, match="edges\\[0\\] must be a mapping"):
        parse("name: x\nconstraints: []\nedges: [42]\n")


def test_parse_edge_missing_from():
    with pytest.raises(ParseError, match="missing required field 'from'"):
        parse("""
name: x
constraints:
  - id: a
    kind: snap
edges:
  - to: a
""")


def test_parse_edge_missing_to():
    with pytest.raises(ParseError, match="missing required field 'to'"):
        parse("""
name: x
constraints:
  - id: a
    kind: snap
edges:
  - from: a
""")


def test_parse_edge_non_string_channel():
    with pytest.raises(ParseError, match="channel must be a string"):
        parse("""
name: x
constraints:
  - id: a
    kind: snap
  - id: b
    kind: snap
edges:
  - from: a
    to: b
    channel: 123
""")


def test_parse_default_name():
    """When name is omitted, default should be 'untitled'."""
    p = parse("constraints: []\n")
    assert p.name == "untitled"


# ── Compiler gaps ────────────────────────────────────────────────────────

def test_compile_error_in_compiler_fn():
    """A registered compiler that raises should be wrapped as CompileError."""
    @register("fail_kind")
    def _bad_compiler(config, params):
        raise ValueError("boom")

    p = parse("""
name: fail
constraints:
  - id: x
    kind: fail_kind
""")
    with pytest.raises(CompileError, match="Failed to compile node 'x'"):
        compile_pipeline(p)
    # cleanup
    _REGISTRY.pop("fail_kind", None)


# ── Runtime gaps ─────────────────────────────────────────────────────────

def test_runtime_dot_notation_input():
    """External inputs with node.port syntax should route correctly."""
    p = parse("""
name: dot
constraints:
  - id: s
    kind: snap
    config:
      epsilon: 0.5
""")
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute({"s.x": 0.5, "s.y": 0.3})
    assert "s" in result.outputs
    assert "point" in result.outputs["s"]


def test_runtime_unknown_kind_returns_empty():
    """_run_node for unknown kind returns empty dict — tested indirectly."""

    # We need a node that doesn't match any known kind in _run_node.
    # Since compile_pipeline validates kinds, we build the graph manually.
    from constraint_dsl.compiler import ConstraintGraph, CompiledNode, ConstraintEdge
    from constraint_dsl.parser import Pipeline, ConstraintNode as CN

    pipeline = Pipeline(name="manual", constraints=[CN(id="u", kind="unknown")])
    node = CompiledNode(id="u", kind="unknown", obj=None)
    graph = ConstraintGraph(pipeline=pipeline, nodes={"u": node}, edges=[])
    rt = Runtime(graph)
    result = rt.execute()
    assert result.node_outputs["u"] == {}


def test_runtime_non_list_neighbor_phases():
    """consensus with non-list neighbor_phases should handle gracefully."""
    p = parse("""
name: consensus_nl
constraints:
  - id: c
    kind: consensus
    config:
      voices: 3
""")
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute({"neighbor_phases": "not_a_list"})
    assert "c" in result.outputs
    assert "correction" in result.outputs["c"]


def test_runtime_reexecute_clears_state():
    """Running execute() twice should produce fresh RuntimeResults."""
    p = parse("""
name: reexec
constraints:
  - id: l
    kind: laman
    config:
      num_nodes: 4
""")
    g = compile_pipeline(p)
    rt = Runtime(g)
    r1 = rt.execute()
    r2 = rt.execute()
    # Laman output is stateless — should be identical across runs
    assert r1.outputs["l"] == r2.outputs["l"]


def test_runtime_empty_inputs():
    """execute() with no args should work for nodes not needing inputs."""
    p = parse("""
name: noinput
constraints:
  - id: l
    kind: laman
    config:
      num_nodes: 3
""")
    g = compile_pipeline(p)
    rt = Runtime(g)
    result = rt.execute()
    assert result.outputs["l"]["n"] == 3
