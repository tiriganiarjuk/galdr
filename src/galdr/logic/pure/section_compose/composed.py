"""Compose composed — stage 1 of the hourglass: chunking.

Sorts every field of all four axes into one of four buffer slots
(heading, preamble, body, closing), and extracts the `pre_*` fields that
control section-level behaviour before sorting begins.

This is the whole of the engine that currently exists. Stages 2-4 —
gather, resolve/render, buffer join — are unbuilt, and stage 1's output
is the inspection report used to work out what a bundle must contain.
See `redesign/01_PROCESSING_FLOW.md`.

Data goes to body wholesale; content classifies on its own suffix;
structure and display classify on the trunk left after their control
suffix is stripped, so a control lands beside what it controls.
"""

from galdr.logic.pure.section_compose.primitive import (
    is_preprocessing_field,
    strip_structure_control_suffix,
)
from galdr.logic.pure.section_compose.simple import (
    classify_content_slot,
    place_display_fields_into_slots,
)
from galdr.structure.model.field_view import FieldView
from galdr.structure.model.preprocessing_fields import PreprocessingFields


def place_structure_field(
    name: str,
    slots: dict[str, list[tuple[str, str]]],
) -> list[tuple[str, tuple[str, str]]]:
    """Determine which slot(s) a structure field belongs to.

    Selectors are duplicated to every slot containing a matching content
    variant (by prefix). Other structure fields are classified by
    stripping their control suffix and classifying the remainder.
    Returns list of (slot_name, (axis, field_name)) placements.
    """
    if name.endswith("_selector"):
        selector_trunk = name.removesuffix("_selector")
        return [
            (slot_name, ("structure", name))
            for slot_name, entries in slots.items()
            if any(axis == "content" and fname.startswith(selector_trunk) for axis, fname in entries)
        ]
    trunk = strip_structure_control_suffix(name)
    return [(classify_content_slot(trunk), ("structure", name))]


def sort_into_slots(
    content_fields: FieldView,
    data_fields: FieldView,
    structure_fields: FieldView,
    display_fields: FieldView,
) -> dict[str, list[tuple[str, str]]]:
    """Sort all fields from all four axes into buffer slots.

    Data first (all body), content second (by positional suffix),
    structure third (by content trunk or selector duplication),
    display last (all body). Every name is the short universal name.

    Returns {slot: [(axis, field_name), ...]}.
    """
    slots: dict[str, list[tuple[str, str]]] = {
        "heading": [], "preamble": [], "body": [], "closing": [],
    }
    for name in data_fields:
        slots["body"].append(("data", name))
    for name in content_fields:
        slots[classify_content_slot(name)].append(("content", name))
    for name in structure_fields:
        if is_preprocessing_field(name):
            continue
        for slot_name, entry in place_structure_field(name, slots):
            slots[slot_name].append(entry)
    return place_display_fields_into_slots(display_fields, slots)


def extract_preprocessing_fields(structure_fields: FieldView) -> PreprocessingFields:
    """Extract pre-processing fields from a structure section into a typed model.

    Pre-processing fields (pre_ prefix) are consumed before slot sorting.
    Not every section has every field — missing fields fall back to defaults
    on PreprocessingFields. Boolean/Integer wrappers unwrap via .root; enum
    wrappers unwrap via .value to their string form.
    """
    visible = structure_fields.get("pre_section_visible")
    max_entries = structure_fields.get("pre_max_entries_rendered")
    ordering = structure_fields.get("pre_field_ordering")
    tier = structure_fields.get("pre_scaffolding_tier_override")
    return PreprocessingFields(
        section_visible=visible.root if visible is not None else True,
        max_entries_rendered=max_entries.root if max_entries is not None else None,
        field_ordering=ordering.value if ordering is not None else None,
        scaffolding_tier_override=tier.value if tier is not None else None,
    )
