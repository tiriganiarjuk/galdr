"""Gate validation primitives — how a refusal reads.

CC=1. No cross-module calls.
"""

from galdr.structure.model.gate_types import GateRefusal


def format_refusal(tool_name: str, refusal: GateRefusal) -> str:
    """The message a refused call is raised with: tool, failure class, message."""
    return f"{tool_name} refused ({refusal.error.type}): {refusal.error.message}"
