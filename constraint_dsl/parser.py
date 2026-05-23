"""
Constraint DSL parser — transforms YAML documents into typed Pipeline objects.
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ConstraintNode:
    """A single constraint vertex in the pipeline graph."""
    id: str
    kind: str
    config: dict[str, Any] = field(default_factory=dict)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ConstraintEdge:
    """A directed edge between two constraint nodes."""
    source: str
    target: str
    weight: float = 1.0
    channel: str | None = None


@dataclass
class Pipeline:
    """A complete constraint pipeline parsed from a DSL document."""
    name: str
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    constraints: list[ConstraintNode] = field(default_factory=list)
    edges: list[ConstraintEdge] = field(default_factory=list)


class ParseError(ValueError):
    """Raised when a DSL document cannot be parsed."""


def parse(text: str) -> Pipeline:
    """Parse a YAML DSL string into a Pipeline."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ParseError(f"Invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ParseError("DSL document must be a YAML mapping (top-level dict)")
    return _from_dict(data)


def load(path: str) -> Pipeline:
    """Load and parse a DSL file from disk."""
    with open(path, "r", encoding="utf-8") as fh:
        return parse(fh.read())


def _from_dict(data: dict[str, Any]) -> Pipeline:
    name = data.get("name", "untitled")
    if not isinstance(name, str):
        raise ParseError(f"'name' must be a string, got {type(name).__name__}")
    description = data.get("description", "")
    if not isinstance(description, str):
        raise ParseError(f"'description' must be a string, got {type(description).__name__}")
    params = data.get("params", {})
    if not isinstance(params, dict):
        raise ParseError(f"'params' must be a mapping, got {type(params).__name__}")
    constraints = _parse_constraints(data.get("constraints", []))
    edges = _parse_edges(data.get("edges", []))
    _validate_graph(constraints, edges)
    return Pipeline(
        name=name,
        description=description,
        params=params,
        constraints=constraints,
        edges=edges,
    )


def _parse_constraints(raw: list[Any]) -> list[ConstraintNode]:
    if not isinstance(raw, list):
        raise ParseError(f"'constraints' must be a list, got {type(raw).__name__}")
    nodes: list[ConstraintNode] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ParseError(f"constraints[{i}] must be a mapping, got {type(item).__name__}")
        node_id = item.get("id")
        if not node_id:
            raise ParseError(f"constraints[{i}] is missing required field 'id'")
        if not isinstance(node_id, str):
            raise ParseError(f"constraints[{i}].id must be a string, got {type(node_id).__name__}")
        kind = item.get("kind")
        if not kind:
            raise ParseError(f"constraints[{i}] is missing required field 'kind'")
        if not isinstance(kind, str):
            raise ParseError(f"constraints[{i}].kind must be a string, got {type(kind).__name__}")
        config = item.get("config", {})
        if not isinstance(config, dict):
            raise ParseError(f"constraints[{i}].config must be a mapping, got {type(config).__name__}")
        nodes.append(ConstraintNode(
            id=node_id,
            kind=kind,
            config=config,
            inputs=item.get("inputs", []),
            outputs=item.get("outputs", []),
        ))
    return nodes


def _parse_edges(raw: list[Any]) -> list[ConstraintEdge]:
    if not isinstance(raw, list):
        raise ParseError(f"'edges' must be a list, got {type(raw).__name__}")
    edges: list[ConstraintEdge] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ParseError(f"edges[{i}] must be a mapping, got {type(item).__name__}")
        source = item.get("from")
        target = item.get("to")
        if source is None:
            raise ParseError(f"edges[{i}] is missing required field 'from'")
        if target is None:
            raise ParseError(f"edges[{i}] is missing required field 'to'")
        weight = float(item.get("weight", 1.0))
        channel = item.get("channel")
        if channel is not None and not isinstance(channel, str):
            raise ParseError(f"edges[{i}].channel must be a string, got {type(channel).__name__}")
        edges.append(ConstraintEdge(
            source=str(source),
            target=str(target),
            weight=weight,
            channel=channel,
        ))
    return edges


def _validate_graph(constraints: list[ConstraintNode], edges: list[ConstraintEdge]) -> None:
    ids = {c.id for c in constraints}
    for edge in edges:
        if edge.source not in ids:
            raise ParseError(f"Edge references unknown source node: {edge.source!r}")
        if edge.target not in ids:
            raise ParseError(f"Edge references unknown target node: {edge.target!r}")
    seen: set[str] = set()
    for c in constraints:
        if c.id in seen:
            raise ParseError(f"Duplicate constraint id: {c.id!r}")
        seen.add(c.id)
