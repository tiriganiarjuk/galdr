"""Gate validation — the IO boundary.

CC=2-3. Turns a gate's or reader's outcome into validated JSON, or raises
with the refusal. Calls the FFI layer for the actual Rust invocation —
never calls gate.validate() directly.
See gate_validate/ffi.py for the NornirGate type alias and FFI bindings.
"""

from pathlib import Path

from galdr.logic.impure.gate_validate.ffi import NornirGate, call_input_gate, call_toml_reader
from galdr.logic.impure.gate_validate.primitive import format_refusal
from galdr.structure.model.gate_types import GateRefusal, GateSuccess


def require_data(tool_name: str, outcome: GateSuccess | GateRefusal) -> str:
    """The validated JSON string of a success. A refusal raises."""
    if isinstance(outcome, GateRefusal):
        raise ValueError(format_refusal(tool_name, outcome))
    return outcome.data


def validate_input(gate: NornirGate, file_path: Path) -> str:
    """Validate input through a gate. Returns validated JSON string."""
    return require_data(gate.__name__, call_input_gate(gate, file_path))


def read_toml_config(file_path: Path, schema_name: str, schema_dir: Path) -> str:
    """Read a TOML config file against a named schema. Returns validated JSON string."""
    return require_data(
        "read_toml_validate_json", call_toml_reader(file_path, schema_name, schema_dir),
    )
