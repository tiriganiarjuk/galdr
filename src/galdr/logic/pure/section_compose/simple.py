"""Compose simple — slot placement for the content and display axes.

CC=1-3. Stage 1 only. Both functions answer the same question for a
different axis: given a field name, which of the four buffer slots does
it belong to?

Content classifies on its own name. Display strips its control suffix
first, then classifies the trunk that remains — so a display field lands
in the same slot as the content it formats.
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
    section_name: str,
    display_section: BaseModel,
    slots: dict[str, list[tuple[str, str]]],
) -> dict[str, list[tuple[str, str]]]:
    """Sort display-axis fields into slots by stripped trunk.

    Pre-processing fields (pre_ after the section prefix) are consumed
    elsewhere and skipped. Remaining fields have their display control
    suffix stripped, then the trunk is classified by positional suffix.
    Returns the updated slots map.
    """
    for name in type(display_section).model_fields:
        if is_preprocessing_field(strip_section_domain(section_name, name)):
            continue
        trunk = strip_display_control_suffix(name)
        slots[classify_content_slot(trunk)].append(("display", name))
    return slots

