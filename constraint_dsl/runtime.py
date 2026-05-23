"""
Constraint DSL runtime — executes compiled ConstraintGraphs.

Execution model: topological data-flow walk (COLLECT → SELECT → COMPILE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .compiler import ConstraintGraph, CompiledNode


@dataclass
class RuntimeResult:
    outputs: dict[str, Any] = field(default_factory=dict)
    node_outputs: dict[str, Any] = field(default_factory=dict)
    execution_order: list[str] = field(default_factory=list)


class RuntimeError(Exception):
    """Raised during constraint graph execution."""


class Runtime:
    """Execute a compiled constraint graph."""

    def __init__(self, graph: ConstraintGraph) -> None:
        self.graph = graph
        self._node_outputs: dict[str, Any] = {}

    def execute(self, inputs: dict[str, Any] | None = None) -> RuntimeResult:
        """Execute the graph with external inputs."""
        inputs = inputs or {}
        order = self._topological_sort()
        result = RuntimeResult(execution_order=order)
        self._node_outputs.clear()

        for node_id in order:
            node = self.graph.nodes[node_id]
            incoming = self._gather_inputs(node_id, inputs)
            try:
                output = self._run_node(node, incoming)
            except Exception as exc:
                raise RuntimeError(
                    f"Node {node_id!r} (kind={node.kind}) execution failed: {exc}"
                ) from exc
            self._node_outputs[node_id] = output

        result.node_outputs = dict(self._node_outputs)
        result.outputs = {
            node_id: out
            for node_id, out in self._node_outputs.items()
            if self._is_leaf(node_id)
        }
        return result

    def _topological_sort(self) -> list[str]:
        adj = {n: [] for n in self.graph.nodes}
        in_degree = {n: 0 for n in self.graph.nodes}
        for e in self.graph.edges:
            if e.source in adj and e.target in adj:
                adj[e.source].append(e.target)
                in_degree[e.target] += 1
        queue = [n for n, d in in_degree.items() if d == 0]
        order: list[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        if len(order) != len(self.graph.nodes):
            missing = set(self.graph.nodes) - set(order)
            raise RuntimeError(f"Graph has unreachable or cyclic nodes: {missing}")
        return order

    def _gather_inputs(self, node_id: str, external: dict[str, Any]) -> dict[str, Any]:
        incoming: dict[str, Any] = {}
        for e in self.graph.edges:
            if e.target == node_id:
                src_out = self._node_outputs.get(e.source, {})
                if e.channel:
                    if isinstance(src_out, dict) and e.channel in src_out:
                        incoming[e.channel] = src_out[e.channel]
                else:
                    if isinstance(src_out, dict):
                        incoming.update(src_out)
        for key, value in external.items():
            if "." in key:
                target, port = key.split(".", 1)
                if target == node_id:
                    incoming[port] = value
            else:
                incoming[key] = value
        return incoming

    def _is_leaf(self, node_id: str) -> bool:
        return not any(e.source == node_id for e in self.graph.edges)

    def _run_node(self, node: CompiledNode, incoming: dict[str, Any]) -> Any:
        kind = node.kind
        obj = node.obj

        if kind == "snap":
            x = float(incoming.get("x", 0.0))
            y = float(incoming.get("y", 0.0))
            pt, err = obj["snap_fn"](x, y)
            return {
                "point": (pt.a, pt.b),
                "error": err,
                "safe": err < obj["epsilon"],
                "epsilon": obj["epsilon"],
                "lattice": obj["lattice"],
            }

        if kind == "funnel":
            x = float(incoming.get("x", 0.0))
            y = float(incoming.get("y", 0.0))
            t = float(incoming.get("t", 0.0))
            result = obj.observe(x, y, t)
            return {
                "phase": result.phase.value,
                "error": result.error,
                "deadband": result.deadband,
                "snapped_a": result.snapped_a,
                "snapped_b": result.snapped_b,
            }

        if kind == "laman":
            return {
                "n": obj["n"],
                "edges": obj["edges"],
                "rigid": obj["rigid"],
                "is_rigid": obj["is_rigid"],
            }

        if kind == "tempo":
            phase = obj.tick()
            state = obj.state()
            return {
                "phase": phase,
                "tick_count": obj.tick_count,
                "converged": obj.converged,
                "epsilon": state.epsilon,
                "anomaly_count": state.anomaly_count,
            }

        if kind == "consensus":
            neighbor_phases = incoming.get("neighbor_phases", [])
            if not isinstance(neighbor_phases, list):
                neighbor_phases = []
            correction = obj["metronome"].correct(neighbor_phases)
            return {
                "correction": correction,
                "converged": obj["metronome"].converged,
                "phase": obj["metronome"].phase,
                "epsilon": obj["metronome"].state().epsilon,
            }

        return {}
