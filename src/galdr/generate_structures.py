#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "datamodel-code-generator==0.55.0",
# ]
# ///
"""Generate Pydantic models from JSON Schema files.

Reads schema mappings from codegen_schemas.toml, fetches schemas from
verdandi output directories, and writes model modules to structure/gen/.

Two schema sources:
  - agent-builder/output/ — checkpoint schemas (anthropic_render)
  - agent-output/output/  — output control surface schemas (content, structure, display)

Run after Draupnir regenerates schemas to keep models in sync.
"""

import subprocess
import sys
import tomllib
from pathlib import Path

from galdr.logic.transform.codegen_clean.composed import strip_redundant_constraints

PACKAGE_ROOT = Path(__file__).resolve().parent
SMIDJA = Path.home() / "ai" / "smidja"
SCHEMA_DIRS = [
    SMIDJA / "verdandi" / "agent-builder" / "output",
    SMIDJA / "verdandi" / "agent-output" / "output",
]
STRUCTURE_DIR = PACKAGE_ROOT / "structure"
CONFIG_PATH = PACKAGE_ROOT / "codegen_schemas.toml"


def find_schema(schema_name: str) -> Path | None:
    """Locate a schema file across known source directories."""
    for schema_dir in SCHEMA_DIRS:
        candidate = schema_dir / f"{schema_name}.schema.json"
        if candidate.exists():
            return candidate
    return None


def main() -> int:
    """Generate all Pydantic model modules from JSON Schemas."""
    config = tomllib.loads(CONFIG_PATH.read_text())
    all_schemas: dict[str, str] = {}
    for section in config.values():
        all_schemas.update(section)

    success = 0
    failed = 0
    for schema_name, module_path in all_schemas.items():
        schema_path = find_schema(schema_name)
        if schema_path is None:
            sys.stdout.write(f"  SKIP: {schema_name} (schema not found)\n")
            continue

        output_path = STRUCTURE_DIR / f"{module_path}.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            [
                sys.executable, "-m", "datamodel_code_generator",
                "--input", str(schema_path),
                "--input-file-type", "jsonschema",
                "--output", str(output_path),
                "--output-model-type", "pydantic_v2.BaseModel",
                "--use-standard-collections",
                "--use-annotated",
                "--use-title-as-name",
                "--disable-future-imports",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            sys.stderr.write(f"  FAIL: {schema_name}\n")
            sys.stderr.write(result.stderr)
            failed += 1
            continue

        content = output_path.read_text()
        content = strip_redundant_constraints(content)
        output_path.write_text(content)
        sys.stdout.write(f"  {schema_name} -> {module_path}.py\n")
        success += 1

    sys.stdout.write(f"\nGenerated: {success}/{len(all_schemas)}\n")
    if failed:
        sys.stderr.write(f"Failed: {failed}\n")
        return 1
    sys.stdout.write("Done.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
