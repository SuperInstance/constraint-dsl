"""
Constraint DSL compiler — transforms Pipeline objects into executable ConstraintGraphs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from constraint_theory_core import (
    TemporalAgent,
    Metronome,
    is_laman,
    henneberg_construct,
    snap,
    covering_radius,
)

from .parser import Pipeline, ConstraintNode, ConstraintEdge


@dataclass
class CompiledNode:
    id: str
    kind: str
    obj: Any
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConstraintGraph:
    pipeline: Pipeline
    nodes: dict[str, CompiledNode] = field(default_factory=dict)
    edges: list[ConstraintEdge] = field(default_factory=list)
    inputs: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)


class CompileError(ValueError):
    """Raised when a pipeline cannot be compiled."""


_CompilerFn = Callable[[dict[str, Any], dict[str, Any]], Any]
_REGISTRY: dict[str, _CompilerFn] = {}


def register(kind: str) -> Callable[[_CompilerFn], _CompilerFn]:
    def decorator(fn: _CompilerFn) -> _CompilerFn:
        _REGISTRY[kind] = fn
        return fn
    return decorator


def compile_pipeline(pipeline: Pipeline) -> ConstraintGraph:
    """Compile a Pipeline into an executable ConstraintGraph."""
    graph = ConstraintGraph(pipeline=pipeline, edges=list(pipeline.edges))
    for node in pipeline.constraints:
        compiler = _REGISTRY.get(node.kind)
        if compiler is None:
            raise CompileError(f"Unknown constraint kind: {node.kind!r}")
        try:
            obj = compiler(node.config, pipeline.params)
        except Exception as exc:
            raise CompileError(f"Failed to compile node {node.id!r}: {exc}") from exc
        graph.nodes[node.id] = CompiledNode(
            id=node.id,
            kind=node.kind,
            obj=obj,
            config=dict(node.config),
        )
    _validate_graph(graph)
    return graph


def _validate_graph(graph: ConstraintGraph) -> None:
    adj = {n: [] for n in graph.nodes}
    for e in graph.edges:
        if e.source in adj and e.target in adj:
            adj[e.source].append(e.target)
    visited: set[str] = set()
    rec_stack: set[str] = set()

    def _dfs(node_id: str) -> bool:
        visited.add(node_id)
        rec_stack.add(node_id)
        for neighbor in adj.get(node_id, []):
            if neighbor not in visited:
                if _dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node_id)
        return False

    for node_id in graph.nodes:
        if node_id not in visited:
            if _dfs(node_id):
                raise CompileError("Constraint graph contains a cycle")


@register("snap")
def _compile_snap(config: dict[str, Any], _params: dict[str, Any]) -> Any:
    epsilon = float(config.get("epsilon", covering_radius()))
    lattice = str(config.get("lattice", "A2"))
    return {"snap_fn": snap, "epsilon": epsilon, "lattice": lattice}


@register("funnel")
def _compile_funnel(config: dict[str, Any], params: dict[str, Any]) -> Any:
    gravity = float(config.get("gravity", 0.5))
    decay_str = str(config.get("decay", "exponential"))
    decay_rate = {"exponential": 0.1, "linear": 0.05, "slow": 0.01}.get(decay_str, 0.1)
    return TemporalAgent(decay_rate=decay_rate, epsilon_0=gravity, delta=gravity * 0.5)


@register("laman")
def _compile_laman(config: dict[str, Any], params: dict[str, Any]) -> Any:
    n = int(config.get("num_nodes", params.get("n", 4)))
    rigid = bool(config.get("rigid", True))
    edges = config.get("edges")
    if edges is None:
        edges = [] if n < 2 else henneberg_construct(n)
    else:
        edges = [tuple(e) for e in edges]
    is_rigid = is_laman(n, edges) if rigid else None
    return {"n": n, "edges": edges, "rigid": rigid, "is_rigid": is_rigid}


@register("tempo")
def _compile_tempo(config: dict[str, Any], params: dict[str, Any]) -> Any:
    bpm = float(config.get("bpm", params.get("bpm", 120.0)))
    grid = int(config.get("grid", 16))
    drift = float(config.get("drift", 0.02))
    T = 60.0 / bpm
    epsilon = T / grid
    return Metronome(T=T, epsilon=epsilon, delta=drift)


@register("consensus")
def _compile_consensus(config: dict[str, Any], params: dict[str, Any]) -> Any:
    voices = int(config.get("voices", params.get("voices", 4)))
    threshold = float(config.get("threshold", 0.6))
    method = str(config.get("method", "majority"))
    edges = [] if voices < 2 else henneberg_construct(voices)
    return {
        "voices": voices,
        "threshold": threshold,
        "method": method,
        "edges": edges,
        "metronome": Metronome(
            T=1.0,
            epsilon=threshold,
            delta=threshold * 0.3,
            edges=edges,
            n_agents=voices,
        ),
    }
