"""Compose primitives — suffix predicates for buffer slot classification.

CC=1. Single expressions with known-typed string inputs.

The positional suffix convention: every content field's terminal suffix
declares which buffer slot it belongs to. Modifier suffixes (_template,
_variant) are stripped before classification — they don't affect slot.
"""


def strip_modifiers(name: str) -> str:
    """Strip _template and _variant modifier suffixes from a field name.

    Modifiers are strippable — they signal type information to authors
    but don't affect buffer slot classification. Strip order: _template
    first (outermost), then _variant.
    """
    return name.removesuffix("_template").removesuffix("_variant")


def strip_structure_control_suffix(name: str) -> str:
    """Strip structure control suffixes to find the content trunk.

    Structure fields reference content fields with appended control
    suffixes: _visible, _selector, _auto_threshold, _override.
    Stripping reveals the content field name they control.
    """
    return (
        name
        .removesuffix("_auto_threshold")
        .removesuffix("_visible")
        .removesuffix("_selector")
        .removesuffix("_override")
    )


def strip_display_control_suffix(name: str) -> str:
    """Strip display control suffixes to find the content trunk.

    Display fields reference content/data fields with appended control
    suffixes: _format, _format_threshold, _visibility_threshold,
    _activation_threshold. Stripping reveals the field they control.
    """
    return (
        name
        .removesuffix("_activation_threshold")
        .removesuffix("_visibility_threshold")
        .removesuffix("_format_threshold")
        .removesuffix("_format")
    )


def extract_trunk(name: str) -> str:
    """Extract the trunk name from any field on any axis.

    Strips all control suffixes (structure, display) and modifiers
    (content). Operations are idempotent — stripping a suffix that
    isn't present is a no-op. No axis parameter needed.

    Used by the bundling probe, which lives outside src/ — do not judge
    this reachable or otherwise by scanning src/ alone.
    """
    return strip_modifiers(strip_display_control_suffix(strip_structure_control_suffix(name)))


def is_preprocessing_field(name: str) -> bool:
    """True if a field name starts with the `pre_` prefix.

    Pre-processing fields are consumed before slot sorting — they
    control section-level behavior (skip section, truncate list,
    expand tier preset) and never enter the bundling pipeline.
    """
    return name.startswith("pre_")


def has_start_suffix(name: str) -> bool:
    """True if name's positional suffix is section-start-slot (after stripping modifiers).

    The `_start` suffix uniquely marks section-level heading fields.
    It has no collision with other positional suffixes — nothing else
    in the vocabulary ends in `_start`, so a single endswith check is
    unambiguous and order-independent.
    """
    return strip_modifiers(name).endswith("_start")


def has_preamble_suffix(name: str) -> bool:
    """True if name's positional suffix is preamble-slot (after stripping modifiers)."""
    return strip_modifiers(name).endswith("_preamble")


def has_closing_suffix(name: str) -> bool:
    """True if name's positional suffix is closing-slot (after stripping modifiers)."""
    return strip_modifiers(name).endswith("_closing")
