"""Document write primitives — which schema each output is written against.

CC=1. The schemas/ directory is a sibling of src/, not inside the package,
so its path is built from this file's location.
"""

from pathlib import Path

from galdr.structure.model.schema_location import SchemaLocation


def slot_inspection_report_schema() -> SchemaLocation:
    """schemas/output/slot-inspection-report.schema.json, by absolute directory."""
    return SchemaLocation(
        name="slot-inspection-report",
        directory=str(Path(__file__).resolve().parents[5] / "schemas" / "output"),
    )
