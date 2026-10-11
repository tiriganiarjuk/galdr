"""Bundling probe — the canonical unmatched-count test.

NOT PRODUCTION CODE. This script is a critical iteration tool, exempt
from gleipnir guardrails while the data shapes and program architecture
are being decided. Once those decisions are made, the logic here will
be absorbed into the real pipeline (probably as a stage-2 bundler).
Until then, every schema rename / refactor should re-run this probe
to see the effect on the unmatched count.

History: this is Generation 4 of the bundling test, originally written
inline as `python -c "..."` in an earlier session. The inline form made
the iterations untraceable — every rename/recount pair lived only in
the session log. This file is the persistent home so we keep a shared
record of what the probe does and what each run measures.

What it measures:
  Given the four-axis inputs loaded through the gates, and given the
  existing `sort_into_slots` stage-1 classifier, count how many
  structure and display fields land in a slot that NONE of:
    - a data field in that slot (Pass 1 trunk-prefix match), or
    - a content field in that slot (Pass 2 trunk-prefix match, either
      direction: content.startswith(field) or field.startswith(content))
  matches. Every unmatched field is a schema naming issue or an
  intentional section-level control that doesn't bundle with anything.

Driving the count down:
  - Rename offending fields so their trunk matches an existing data or
    content trunk.
  - Prefix true preprocessing fields with `pre_` so the slot sorter
    filters them out entirely (they never enter the bundling pipeline).

How to run:
  uv run python probe/bundling.py

  Default inputs are agent-builder; override with arguments if needed.

Runnable without PYTHONPATH; the sys.path setup at the top points at
the local src/ and the gate lib dir.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(Path.home() / "ai" / "tools" / "lib"))

from galdr.logic.orchestrate.section_compose.orchestrate import load_all_inputs  # noqa: E402
from galdr.logic.pure.section_compose.composed import sort_into_slots  # noqa: E402
from galdr.logic.pure.section_compose.primitive import extract_trunk  # noqa: E402
from galdr.logic.pure.section_compose.simple import field_view, local_field_view  # noqa: E402
from galdr.structure.gen.output_content import AgentOutputContent  # noqa: E402

DEFAULT_DATA_PATH = Path.home() / "ai" / "spaces" / "bragi" / "definitions" / "agents" / "agent-builder" / "anthropic_render.toml"
DEFAULT_CONTENT_PATH = _REPO_ROOT / "extracted" / "content.toml"
DEFAULT_STRUCTURE_PATH = _REPO_ROOT / "extracted" / "structure.toml"
DEFAULT_DISPLAY_PATH = _REPO_ROOT / "extracted" / "display.toml"


def run_probe(
    data_path: Path = DEFAULT_DATA_PATH,
    content_path: Path = DEFAULT_CONTENT_PATH,
    structure_path: Path = DEFAULT_STRUCTURE_PATH,
    display_path: Path = DEFAULT_DISPLAY_PATH,
) -> tuple[int, list[str]]:
    """Run the two-pass bundling probe. Returns (count, unmatched_list)."""
    data, content, structure, display = load_all_inputs(
        data_path, content_path, structure_path, display_path,
    )

    section_names = list(AgentOutputContent.model_fields.keys())
    all_unmatched: list[str] = []

    for section_name in section_names:
        ds = getattr(data, section_name, None)
        cs = getattr(content, section_name, None)
        ss = getattr(structure, section_name, None)
        dd = getattr(display, section_name, None)
        if ds is None or cs is None or ss is None:
            continue
        slots = sort_into_slots(
            local_field_view(section_name, cs), field_view(ds),
            local_field_view(section_name, ss), local_field_view(section_name, dd),
        )

        for slot_name, entries in slots.items():
            if not entries:
                continue
            data_fields = [(a, n) for a, n in entries if a == "data"]
            content_fields = [(a, n) for a, n in entries if a == "content"]
            structure_fields = [(a, n) for a, n in entries if a == "structure"]
            display_fields = [(a, n) for a, n in entries if a == "display"]
            matched: set[tuple[str, str]] = set()

            # Pass 1: data trunks match content/structure/display by prefix.
            for _, dname in data_fields:
                trunk = dname
                for axis_name, axis_fields in (
                    ("content", content_fields),
                    ("structure", structure_fields),
                    ("display", display_fields),
                ):
                    for _, fname in axis_fields:
                        ftrunk = extract_trunk(fname)
                        if ftrunk.startswith(trunk + "_") or ftrunk == trunk:
                            matched.add((axis_name, fname))

            # Pass 2: unmatched content trunks match remaining structure/display,
            # symmetric prefix check (either direction).
            for _, cname in content_fields:
                if ("content", cname) in matched:
                    continue
                ctrunk = extract_trunk(cname)
                matched.add(("content", cname))
                for axis_name, axis_fields in (
                    ("structure", structure_fields),
                    ("display", display_fields),
                ):
                    for _, fname in axis_fields:
                        if (axis_name, fname) in matched:
                            continue
                        ftrunk = extract_trunk(fname)
                        if (
                            ftrunk.startswith(ctrunk + "_")
                            or ftrunk == ctrunk
                            or ctrunk.startswith(ftrunk + "_")
                        ):
                            matched.add((axis_name, fname))

            for axis, name in structure_fields + display_fields:
                if (axis, name) not in matched:
                    all_unmatched.append(f"{section_name}.{slot_name}: {axis}:{name}")

    return len(all_unmatched), all_unmatched


if __name__ == "__main__":
    count, unmatched = run_probe()
    for line in unmatched:
        print(line)
    print(f"TOTAL UNMATCHED: {count}")
