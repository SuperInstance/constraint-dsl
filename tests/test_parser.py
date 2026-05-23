import pytest
from constraint_dsl.parser import parse, load, ParseError, Pipeline


def test_parse_minimal():
    text = """
name: test
constraints: []
edges: []
"""
    p = parse(text)
    assert p.name == "test"
    assert p.constraints == []
    assert p.edges == []


def test_parse_full_pipeline():
    text = """
name: full
description: A full pipeline
params:
  bpm: 120
constraints:
  - id: a
    kind: snap
    config:
      epsilon: 0.1
  - id: b
    kind: funnel
    config:
      gravity: 0.7
edges:
  - from: a
    to: b
    weight: 0.5
    channel: point
"""
    p = parse(text)
    assert p.name == "full"
    assert p.description == "A full pipeline"
    assert p.params == {"bpm": 120}
    assert len(p.constraints) == 2
    assert p.constraints[0].id == "a"
    assert p.constraints[0].kind == "snap"
    assert p.constraints[0].config["epsilon"] == 0.1
    assert len(p.edges) == 1
    assert p.edges[0].source == "a"
    assert p.edges[0].target == "b"
    assert p.edges[0].weight == 0.5
    assert p.edges[0].channel == "point"


def test_parse_missing_id():
    text = """
name: bad
constraints:
  - kind: snap
"""
    with pytest.raises(ParseError, match="missing required field 'id'"):
        parse(text)


def test_parse_missing_kind():
    text = """
name: bad
constraints:
  - id: a
"""
    with pytest.raises(ParseError, match="missing required field 'kind'"):
        parse(text)


def test_parse_invalid_yaml():
    with pytest.raises(ParseError, match="Invalid YAML"):
        parse("{[bad yaml")


def test_parse_duplicate_node_id():
    text = """
name: dup
constraints:
  - id: a
    kind: snap
  - id: a
    kind: funnel
"""
    with pytest.raises(ParseError, match="Duplicate constraint id"):
        parse(text)


def test_parse_unknown_edge_source():
    text = """
name: bad_edge
constraints:
  - id: a
    kind: snap
edges:
  - from: b
    to: a
"""
    with pytest.raises(ParseError, match="unknown source node"):
        parse(text)


def test_parse_unknown_edge_target():
    text = """
name: bad_edge
constraints:
  - id: a
    kind: snap
edges:
  - from: a
    to: c
"""
    with pytest.raises(ParseError, match="unknown target node"):
        parse(text)


def test_parse_invalid_params_type():
    text = """
name: bad
params: 123
constraints: []
"""
    with pytest.raises(ParseError, match="'params' must be a mapping"):
        parse(text)


def test_load_file(tmp_path):
    f = tmp_path / "test.yaml"
    f.write_text("name: from_file\nconstraints: []\n")
    p = load(str(f))
    assert isinstance(p, Pipeline)
    assert p.name == "from_file"


def test_parse_edge_no_channel():
    text = """
name: edge_test
constraints:
  - id: a
    kind: snap
  - id: b
    kind: funnel
edges:
  - from: a
    to: b
"""
    p = parse(text)
    assert p.edges[0].channel is None
    assert p.edges[0].weight == 1.0


def test_parse_inputs_outputs():
    text = """
name: io
constraints:
  - id: a
    kind: snap
    inputs: [x, y]
    outputs: [point]
"""
    p = parse(text)
    assert p.constraints[0].inputs == ["x", "y"]
    assert p.constraints[0].outputs == ["point"]
