"""Document write — the output boundary.

CC=2. What a run produces leaves through the compiled markdown writer,
validated against its schema on the way out. A refusal raises.
"""

from pathlib import Path

from galdr.logic.impure.document_write.ffi import call_markdown_writer
from galdr.logic.impure.document_write.primitive import slot_inspection_report_schema
from galdr.logic.impure.gate_validate.primitive import format_refusal
from galdr.structure.model.gate_types import GateRefusal, GateWritten
from galdr.structure.model.slot_inspection_report import SlotInspectionReport


def write_slot_inspection_report(report: SlotInspectionReport, file_path: Path) -> GateWritten:
    """Write the stage-1 slot inspection report to file_path."""
    outcome = call_markdown_writer(
        report.model_dump_json(), file_path, slot_inspection_report_schema(),
    )
    if isinstance(outcome, GateRefusal):
        raise ValueError(format_refusal("write_json_validate_markdown", outcome))
    return outcome
