"""Full bundler probe — data-first, then content, single pass per section.

NOT PRODUCTION CODE. Exempt from gleipnir.

Algorithm (per section):

  sources = {data, content, structure, display} — field name lists
  bundles = {heading: {}, preamble: {}, body: {}, closing: {}}
           where each slot maps trunk_name → list of (axis, field_name)

  Phase 1: data drives
    for each data field (in declaration order):
      - create a body bundle keyed by trunk = field name
      - seed with ("data", field_name); remove from data source
      - pull in any content/structure/display field whose stripped
        name equals the trunk or starts with trunk + "_"
      - consumed fields are removed from their source list

  Phase 2: content drives (remaining content)
    for each content field still in source (in declaration order):
      - classify slot via classify_content_slot
      - create a bundle in that slot keyed by trunk = strip_modifiers(name)
      - seed with ("content", field_name); remove from content source
      - pull in any remaining structure/display field whose stripped
        name equals the trunk or starts with trunk + "_"

  Phase 3: distribute selectors
    for each remaining structure field ending in _selector:
      - selector_trunk = name minus _selector
      - add the selector into every bundle whose trunk equals
        selector_trunk or starts with selector_trunk + "_"
      - remove from source if placed at least once

  Leftover = anything still in structure or display sources.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path.home() / "ai" / "tools" / "lib"))

from galdr.logic.orchestrate.section_compose.orchestrate import load_all_inputs
from galdr.logic.pure.section_compose.primitive import (
    is_preprocessing_field,
    strip_display_control_suffix,
    strip_modifiers,
    strip_section_domain,
    strip_structure_control_suffix,
)
from galdr.logic.pure.section_compose.simple import classify_content_slot
from galdr.structure.gen.output_content import AgentOutputContent

DEFAULT_DATA_PATH = Path.home() / "ai" / "spaces" / "bragi" / "definitions" / "agents" / "agent-builder" / "anthropic_render.toml"
DEFAULT_CONTENT_PATH = REPO_ROOT / "extracted" / "content.toml"
DEFAULT_STRUCTURE_PATH = REPO_ROOT / "extracted" / "structure.toml"
DEFAULT_DISPLAY_PATH = REPO_ROOT / "extracted" / "display.toml"


def stripped_for_axis(axis, name):
    """The trunk a short field name links on, once its suffixes are off."""
    if axis == "content":
        return strip_modifiers(name)
    if axis == "structure":
        return strip_modifiers(strip_structure_control_suffix(name))
    if axis == "display":
        return strip_modifiers(strip_display_control_suffix(name))
    return name


def matches_trunk(stripped, trunk):
    return stripped == trunk or stripped.startswith(trunk + "_")


def pull_into_bundle(trunk, bundle, sources):
    for axis in ("content", "structure", "display"):
        for name in list(sources[axis]):
            if axis == "structure" and name.endswith("_selector"):
                continue  # selectors handled in phase 3
            stripped = stripped_for_axis(axis, name)
            if matches_trunk(stripped, trunk):
                bundle.append((axis, name))
                sources[axis].remove(name)


def distribute_selectors(bundles, sources):
    for name in list(sources["structure"]):
        if not name.endswith("_selector"):
            continue
        selector_trunk = name.removesuffix("_selector")
        placed = False
        for slot_bundles in bundles.values():
            for bundle_trunk, bundle in slot_bundles.items():
                if bundle_trunk == selector_trunk or bundle_trunk.startswith(selector_trunk + "_"):
                    bundle.append(("structure", name))
                    placed = True
        if placed:
            sources["structure"].remove(name)


def short_names(section_name, section):
    """The boundary: a control section's field names, domain prefix stripped.

    Everything after this works on the short universal name, exactly as the
    engine does. pre_* fields are excluded — they never enter bundling.
    """
    if section is None:
        return []
    local = [strip_section_domain(section_name, name) for name in type(section).model_fields]
    return [name for name in local if not is_preprocessing_field(name)]


def bundle_section(section_name, data_section, content_section, structure_section, display_section):
    bundles = {"heading": {}, "preamble": {}, "body": {}, "closing": {}}
    sources = {
        "data": list(type(data_section).model_fields),
        "content": short_names(section_name, content_section),
        "structure": short_names(section_name, structure_section),
        "display": short_names(section_name, display_section),
    }

    # Phase 1: data drives
    for data_name in list(sources["data"]):
        trunk = data_name
        bundle = [("data", data_name)]
        sources["data"].remove(data_name)
        pull_into_bundle(trunk, bundle, sources)
        bundles["body"][trunk] = bundle

    # Phase 2: content drives
    for content_name in list(sources["content"]):
        slot = classify_content_slot(content_name)
        trunk = strip_modifiers(content_name)
        bundle = [("content", content_name)]
        sources["content"].remove(content_name)
        pull_into_bundle(trunk, bundle, sources)
        bundles[slot][trunk] = bundle

    # Phase 3: selectors
    distribute_selectors(bundles, sources)

    leftover = [("structure", n) for n in sources["structure"]] + [
        ("display", n) for n in sources["display"]
    ]
    return bundles, leftover


def format_section_block(section_name, bundles, leftover):
    lines = [f"## {section_name}", ""]
    lines.append("```")
    for slot_name in ("heading", "preamble", "body", "closing"):
        slot_bundles = bundles[slot_name]
        if not slot_bundles:
            lines.append(f"{slot_name}: (empty)")
            continue
        lines.append(f"{slot_name}:")
        for trunk, bundle in slot_bundles.items():
            lines.append(f"  [{trunk}]")
            for axis, name in bundle:
                lines.append(f"    {axis}: {name}")
    if leftover:
        lines.append(f"LEFTOVER ({len(leftover)}):")
        for axis, name in leftover:
            lines.append(f"  {axis}: {name}")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def run_probe():
    data, content, structure, display = load_all_inputs(
        DEFAULT_DATA_PATH, DEFAULT_CONTENT_PATH, DEFAULT_STRUCTURE_PATH, DEFAULT_DISPLAY_PATH,
    )
    output_lines = ["# Bundle Inspection — agent-builder", "", "Generated by `probe/bundle_full.py`.", ""]
    total_leftover = 0
    for section_name in AgentOutputContent.model_fields:
        data_section = getattr(data, section_name, None)
        content_section = getattr(content, section_name, None)
        structure_section = getattr(structure, section_name, None)
        display_section = getattr(display, section_name, None)
        if data_section is None or content_section is None or structure_section is None:
            output_lines.append(f"## {section_name}\n\n_skipped_\n")
            continue
        bundles, leftover = bundle_section(
            section_name, data_section, content_section, structure_section, display_section,
        )
        output_lines.append(format_section_block(section_name, bundles, leftover))
        total_leftover += len(leftover)
    output_lines.append(f"## Summary\n\nTOTAL LEFTOVER: {total_leftover}\n")
    output_path = REPO_ROOT / "review" / "BUNDLE_INSPECTION.md"
    output_path.write_text("\n".join(output_lines))
    print(f"wrote {output_path} — TOTAL LEFTOVER: {total_leftover}")


if __name__ == "__main__":
    run_probe()
