"""Composition pipeline orchestration — stage 1 slot inspection.

Orchestrate level (CC=1-5). Wires together impure (gate validation)
and pure (compose stage 1) zones. Stages 2 (gather/bundling), 3
(resolve/render), and 4 (buffer join) are NOT YET IMPLEMENTED — the
walker-based old pipeline has been disconnected. The output file now
contains human-readable slot inspection blocks per section.

Gate modules are compiled Rust/PyO3 .so files imported directly.
Each is called via validate_input(gate, path) → JSON string.
"""

from pathlib import Path

import gate_anthropic_render_input
import gate_output_content_input
import gate_output_display_input
import gate_output_structure_input

from galdr.logic.impure.gate_validate.simple import validate_input
from galdr.logic.pure.section_compose.assembled import compose_section
from galdr.logic.pure.section_compose.simple import field_view, local_field_view, source_name
from galdr.structure.gen.anthropic_render import AgentAnthropicRender
from galdr.structure.gen.output_content import AgentOutputContent
from galdr.structure.gen.output_display import AgentOutputDisplay
from galdr.structure.gen.output_structure import AgentOutputStructure
from galdr.structure.model.preprocessing_fields import PreprocessingFields


def load_all_inputs(
    data_path: Path,
    content_path: Path,
    structure_path: Path,
    display_path: Path,
) -> tuple[AgentAnthropicRender, AgentOutputContent, AgentOutputStructure, AgentOutputDisplay]:
    """Validate all four inputs through gates, deserialize to Pydantic models."""
    data_json = validate_input(gate_anthropic_render_input, data_path)
    content_json = validate_input(gate_output_content_input, content_path)
    structure_json = validate_input(gate_output_structure_input, structure_path)
    display_json = validate_input(gate_output_display_input, display_path)
    return (
        AgentAnthropicRender.model_validate_json(data_json),
        AgentOutputContent.model_validate_json(content_json),
        AgentOutputStructure.model_validate_json(structure_json),
        AgentOutputDisplay.model_validate_json(display_json),
    )


def format_preprocessing_lines(section_name: str, pre_fields: PreprocessingFields) -> list[str]:
    """Render extracted preprocessing fields as report lines, both names shown.

    Omits fields at their default values so the report only shows what
    was actually extracted for this section.
    """
    lines: list[str] = []
    if pre_fields.section_visible is not True:
        lines.append(f"  pre_section_visible = {pre_fields.section_visible!r}"
                     f"   [{section_name}_pre_section_visible]")
    if pre_fields.max_entries_rendered is not None:
        lines.append(f"  pre_max_entries_rendered = {pre_fields.max_entries_rendered!r}"
                     f"   [{section_name}_pre_max_entries_rendered]")
    if pre_fields.field_ordering is not None:
        lines.append(f"  pre_field_ordering = {pre_fields.field_ordering!r}"
                     f"   [{section_name}_pre_field_ordering]")
    if pre_fields.scaffolding_tier_override is not None:
        lines.append(f"  pre_scaffolding_tier_override = {pre_fields.scaffolding_tier_override!r}"
                     f"   [{section_name}_pre_scaffolding_tier_override]")
    return lines


def format_slot_lines(
    section_name: str, slot_name: str, entries: list[tuple[str, str]],
) -> list[str]:
    """Render one slot's entries with both names side by side.

    The universal name is what the engine works on; the source name is what
    the files say. Showing both makes the abstraction itself visible — many
    section-specific names collapsing onto one shared vocabulary.
    """
    lines = [f"### {slot_name} ({len(entries)} entries)"]
    if not entries:
        lines.append("  (empty)")
        return lines
    lines.append(f"  {'axis':<10} {'universal (engine)':<44} source (files)")
    for axis, field_name in entries:
        source = source_name(section_name, axis, field_name)
        lines.append(f"  {axis:<10} {field_name:<44} {source}")
    return lines


def format_section_report(
    section_name: str,
    pre_fields: PreprocessingFields,
    slots: dict[str, list[tuple[str, str]]],
) -> str:
    """Build a full per-section report block: preprocessor + four slots."""
    lines = [f"## {section_name}", ""]
    preprocessing_lines = format_preprocessing_lines(section_name, pre_fields)
    if preprocessing_lines:
        lines.append("**preprocessor (pre_* extracted):**")
        lines.extend(preprocessing_lines)
    else:
        lines.append("**preprocessor:** (none)")
    lines.append("")
    for slot_name in ("heading", "preamble", "body", "closing"):
        lines.extend(format_slot_lines(section_name, slot_name, slots[slot_name]))
        lines.append("")
    return "\n".join(lines)


def format_skipped_section(section_name: str, reason: str) -> str:
    """Build a skipped-section report block naming the reason."""
    return f"## {section_name}\n\n_skipped: {reason}_\n"


def compose_one_section(
    section_name: str,
    data_model: AgentAnthropicRender,
    content_model: AgentOutputContent,
    structure_model: AgentOutputStructure,
    display_model: AgentOutputDisplay,
) -> str:
    """Run stage 1 on a single section and format the report block."""
    data_section = getattr(data_model, section_name, None)
    content_section = getattr(content_model, section_name, None)
    if data_section is None:
        return format_skipped_section(section_name, "no data")
    if content_section is None:
        return format_skipped_section(section_name, "no content")
    structure_section = getattr(structure_model, section_name, None)
    display_section = getattr(display_model, section_name, None)
    # The boundary: the engine below works on short universal names and never
    # learns the section. Control fields lose their domain prefix here, once.
    pre_fields, slots = compose_section(
        field_view(data_section),
        local_field_view(section_name, structure_section),
        local_field_view(section_name, content_section),
        local_field_view(section_name, display_section),
    )
    return format_section_report(section_name, pre_fields, slots)


def compose_all_sections(
    data_model: AgentAnthropicRender,
    content_model: AgentOutputContent,
    structure_model: AgentOutputStructure,
    display_model: AgentOutputDisplay,
) -> list[str]:
    """Run stage 1 across every section in order; return one block per section."""
    section_order = [item.value for item in structure_model.section_order.section_order_order.root]
    return [
        compose_one_section(name, data_model, content_model, structure_model, display_model)
        for name in section_order
    ]


def run(
    data_path: Path,
    content_path: Path,
    structure_path: Path,
    display_path: Path,
    output_path: Path,
) -> int:
    """Run the stage-1 pipeline: load, sort into slots, write inspection report."""
    data, content, structure, display = load_all_inputs(
        data_path, content_path, structure_path, display_path,
    )
    blocks = compose_all_sections(data, content, structure, display)
    report = "# Stage 1 Slot Inspection\n\n" + "\n---\n\n".join(blocks) + "\n"
    output_path.write_text(report, encoding="utf-8")
    return 0
