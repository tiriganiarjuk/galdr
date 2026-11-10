# Composition Engine Design

## Core Principle

One generic engine processes all sections. Section-specific knowledge lives in the data models and TOML files, not in code. The engine reads field names, checks types, and applies operations based on naming conventions. It never asks "which section am I in?"

---

## The Four Inputs

Every section receives four typed chunks — one from each axis:

- **Data** — what to say. Agent values from the pipeline. Frozen — the engine never modifies data.
- **Content** — how to word it. Prose, templates, variant alternatives. The experimental surface.
- **Structure** — what to include. Visibility toggles, variant selectors, section ordering. Stable configuration.
- **Display** — how to format it. List formats, thresholds, separators, containers. Orthogonal to prose.

These are independent. The engine never reads a content field to make a structure decision. Never reads a display field to determine visibility.

---

## What the Engine Produces

For each section: a rendered markdown block. Heading, then prose and data interleaved, then closing. Each piece of output text comes from one of these sources:

- **Plain prose** — content field rendered as-is. May be gated by a visibility toggle.
- **Interpolated template** — content template with `{{placeholder}}` markers filled from data values.
- **Resolved variant** — one of several content alternatives, selected by a structure enum.
- **Formatted list** — data list rendered per display format (bulleted, numbered, inline, etc.) with optional threshold-based switching.
- **Compound structure** — nested data items with per-item content (headings, templates, variant framing, sub-lists).

---

## Buffer Slots

Every piece of output goes into one of four buffer slots, determined by the content field's terminal suffix:

- **Heading** — section title. Renders first.
- **Preamble** — context prose before the body. Renders second.
- **Body** — data-driven content with decorations. Renders third. This is where most of the work happens.
- **Closing** — reinforcement prose after the body. Renders last.

The suffix convention (documented in `TOML_ARCHITECTURE.md`) mechanically determines which slot each content field belongs to. No heuristics, no classification logic.

---

## Body Processing

The body has two input streams:

1. **Data fields** in declaration order — each may have associated content (labels before, templates wrapping, postscripts after). These are linked by trunk naming.
2. **Standalone content** — content body fields not linked to any data field. Rendered after all data-driven content, in content declaration order.

For each data field, the engine gathers everything that affects it — the data value, matched content, visibility toggles, variant selections, display format — resolves it all, and renders. Simple fields produce simple output. Compound fields (nested lists, enum-discriminated items, variant-framed items) go to specialized renderers that handle per-item logic.

---

## Data Gates

Invariant rules baked into the engine, separate from visibility toggles:

- **Silence for absence** — null/absent data renders nothing
- **Boolean gates** — false data gates suppress related content entirely
- **Empty arrays** — no items means no list and no surrounding prose
- **Suppress on incomplete interpolation** — if a template still has `{{placeholders}}` after interpolation, suppress it. The required data isn't available.

Data gates fire before visibility toggles. If the data isn't there, the toggle is irrelevant.

---

## Section Ordering

The structure axis controls which sections render and in what order. The engine iterates the section order, extracts four chunks per section, processes each through the same pipeline.

Sections render at H2. Heading level is invariant.

---

## Dividers

Each section controls the divider above it. Global default applies unless overridden per section. When sections are reordered, dividers travel with them.

---

## Special Cases

**Identity field ordering** — the only section with intra-section field reordering. Two structural variants produce different field sequences. The structure selector picks which order is used.

**Frontmatter and Dispatcher** — different render paths. Frontmatter is YAML serialization. Dispatcher programs the caller, not the agent. Neither shares the body-section engine.

The dispatcher is not built until the agent is, and it does not need designing now. It is a natural extension of having the agent: whatever the agent needs becomes what the dispatcher hands over — paths, inclusions — derived from the same specification. Batching is never done by hand: the dispatcher feeds what needs batching and the batch size to a deterministic tool and sends out what comes back. Because almost everything it does is deterministic, it needs far less play in wording than the agent prompt.

---

## Guardrails Family

Four sections get extra controls: `section_visible` (master toggle) and `max_entries_rendered` (truncation cap). Sections: constraints, anti_patterns, success_criteria, failure_criteria. Enables combinatorial testing without changing data.

Other sections render when data is present and don't when it isn't. No master toggle needed.
