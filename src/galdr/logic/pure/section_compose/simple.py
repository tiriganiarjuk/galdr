"""Compose simple — the engine's input boundary, and slot placement.

CC=1-3. Stage 1 only.

The boundary: field_view and local_field_view turn a validated section
model into short name -> value. Control-surface names lose their
`{section}_` domain prefix here, once, so everything downstream works on
the short universal name and never deals with namespacing.

Slot placement: given a short field name, which of the four buffer slots
does it belong to? Content classifies on its own name. Display strips its
control suffix first, then classifies the trunk that remains — so a display
field lands in the same slot as the content it formats.
"""


from pydantic import BaseModel

from galdr.logic.pure.section_compose.primitive import (
    has_closing_suffix,
    has_preamble_suffix,
    has_start_suffix,
    is_preprocessing_field,
    strip_display_control_suffix,
    strip_section_domain,
)
from galdr.structure.model.field_view import FieldView


def field_view(section: BaseModel) -> FieldView:
    """A data section's fields as name -> value, names exactly as declared.

    Data names carry no domain prefix and are never stripped — some begin
    with their section's name by coincidence (`input_schema`).
    """
    return {name: getattr(section, name) for name in type(section).model_fields}


def local_field_view(section_name: str, section: BaseModel | None) -> FieldView:
    """A control section's fields as short name -> value.

    The one place the `{section}_` domain prefix is removed. An absent
    section is an empty view, so the engine never branches on it.
    """
    if section is None:
        return {}
    return {
        strip_section_domain(section_name, name): getattr(section, name)
        for name in type(section).model_fields
    }


def classify_content_slot(name: str) -> str:
    """Classify a content field into a buffer slot by positional suffix.

    Checks heading, preamble, closing via suffix predicates (which strip
    modifiers internally). Everything else is body.
    """
    classifiers = [(has_start_suffix, "heading"), (has_preamble_suffix, "preamble"), (has_closing_suffix, "closing")]
    for check, slot in classifiers:
        if check(name):
            return slot
    return "body"


def place_display_fields_into_slots(
    display_fields: FieldView,
    slots: dict[str, list[tuple[str, str]]],
) -> dict[str, list[tuple[str, str]]]:
    """Sort display-axis fields into slots by stripped trunk.

    Pre-processing fields (pre_ prefix) are consumed elsewhere and
    skipped. Remaining fields have their display control suffix
    stripped, then the trunk is classified by positional suffix.
    Returns the updated slots map.
    """
    for name in display_fields:
        if is_preprocessing_field(name):
            continue
        trunk = strip_display_control_suffix(name)
        slots[classify_content_slot(trunk)].append(("display", name))
    return slots
