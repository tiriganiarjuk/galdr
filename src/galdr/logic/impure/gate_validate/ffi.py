"""Gate FFI bindings — Rust/PyO3 gate module invocation.

CC=1. These are the only functions that call into compiled Rust gate
modules. The internals are a black box — purity is asserted by placement
in impure/gate_validate/ffi.py.

NornirGate is a type alias for compiled Rust/PyO3 gate modules (.so files
at ~/ai/tools/lib/gate_*.cpython-313-darwin.so). Each gate module has a
.validate() method. Input gates take a file path and return a dict.

All return {"ok": bool, "data": str | None, "error": {"type": str, "message": str} | None}.
Gate modules are imported by name (e.g. `import gate_anthropic_render_input`).

A gate carries its schema embedded. The TOML reader is the same contract
with the schema named at call time, for Galdr's own configuration files.
"""

from pathlib import Path
from types import ModuleType

import read_toml_validate_json

from galdr.structure.model.gate_types import GateRefusal, GateResult, GateSuccess

type NornirGate = ModuleType


def call_input_gate(gate: NornirGate, file_path: Path) -> GateSuccess | GateRefusal:
    """Call an input gate, return its outcome typed."""
    return GateResult.model_validate(gate.validate(str(file_path))).root


def call_toml_reader(
    file_path: Path, schema_name: str, schema_dir: Path,
) -> GateSuccess | GateRefusal:
    """Read a TOML file against {schema_dir}/{schema_name}.schema.json."""
    return GateResult.model_validate(
        read_toml_validate_json.read(str(file_path), schema_name, str(schema_dir)),
    ).root
