"""
Constraint DSL — declarative YAML-like language for constraint graphs.

Compiles to executable constraint pipelines using ``constraint_theory_core``.

Quick start
-----------
>>> from constraint_dsl import load, compile_pipeline, Runtime
>>> pipeline = load("examples/jazz_solo.yaml")
>>> graph = compile_pipeline(pipeline)
>>> result = Runtime(graph).execute({"x": 0.5, "y": 0.3})
>>> print(result.outputs)
"""

from .parser import (
    load,
    parse,
    Pipeline,
    ConstraintNode,
    ConstraintEdge,
    ParseError,
)
from .compiler import (
    compile_pipeline,
    ConstraintGraph,
    CompiledNode,
    CompileError,
    register,
)
from .runtime import (
    Runtime,
    RuntimeResult,
    RuntimeError,
)

__version__ = "0.1.0"

__all__ = [
    "load",
    "parse",
    "compile_pipeline",
    "Runtime",
    "Pipeline",
    "ConstraintNode",
    "ConstraintEdge",
    "ConstraintGraph",
    "CompiledNode",
    "RuntimeResult",
    "ParseError",
    "CompileError",
    "RuntimeError",
    "register",
]
