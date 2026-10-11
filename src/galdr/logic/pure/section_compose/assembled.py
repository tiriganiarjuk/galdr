"""Compose assembled — section composition wiring.

CC=1-2. Wires composed-level processors into a stage-1 section inspection.
One guard (data + content presence), then two composed calls: preprocessor
and slot sorter. Zero other decisions.

STAGE 1 ONLY. The hourglass pipeline has four stages (chunk, gather,
resolve+render, buffer). Only stage 1 is implemented. compose_section
returns the raw slot dict plus the extracted preprocessing fields for
inspection — no bundling, no resolution, no rendering.

The walker-based composition that preceded this was disconnected, then
deleted. Nothing of it remains to consult, deliberately — see
context/GALDR_ELEMENT.md, "Why the old walker code is gone."
"""

from galdr.logic.pure.section_compose.composed import (
    extract_preprocessing_fields,
    sort_into_slots,
)
from galdr.structure.model.field_view import FieldView
from galdr.structure.model.preprocessing_fields import PreprocessingFields


def compose_section(
    data_fields: FieldView,
    structure_fields: FieldView,
    content_fields: FieldView,
    display_fields: FieldView,
) -> tuple[PreprocessingFields, dict[str, list[tuple[str, str]]]]:
    """Run stage 1 of the hourglass pipeline for one section.

    Preprocessor extracts pre_* fields into a typed state. Slot sorter
    classifies every remaining field into heading/preamble/body/closing
    by terminal suffix. Returns both — preprocessor state and the raw
    slot dict — for inspection.

    The slot dict is intentionally untyped: the shape discovery is
    ongoing, so we don't commit to a Pydantic model until we know what
    a bundle actually contains.
    """
    pre_fields = extract_preprocessing_fields(structure_fields)
    slots = sort_into_slots(content_fields, data_fields, structure_fields, display_fields)
    return pre_fields, slots
