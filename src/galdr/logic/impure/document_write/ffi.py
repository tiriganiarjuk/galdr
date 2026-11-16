"""Markdown writer FFI binding — the Rust/PyO3 text writer.

CC=1. The only function that calls the compiled markdown writer. It takes
the {frontmatter, body} envelope as JSON, validates it against the named
schema, and writes the file atomically. Nothing is written without a schema.
"""

from pathlib import Path

import write_json_validate_markdown

from galdr.structure.model.gate_types import GateRefusal, GateWritten, WriteResult
from galdr.structure.model.schema_location import SchemaLocation


def call_markdown_writer(
    document_json: str, file_path: Path, schema: SchemaLocation,
) -> GateWritten | GateRefusal:
    """Validate a markdown envelope and write it; return the outcome typed."""
    return WriteResult.model_validate(
        write_json_validate_markdown.write(
            document_json, str(file_path), schema.name, schema.directory,
        ),
    ).root
