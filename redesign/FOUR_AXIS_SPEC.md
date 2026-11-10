# Agent Build System

## Purpose

One agent definition produces many agents. The composition engine takes a single validated data structure and multiplies it across content variants, display variants, and model configurations to produce a matrix of benchmarkable agent prompts.

This enables:
- Empirical optimization of prompt format through systematic benchmarking
- Regression testing when underlying LLM models are updated
- Auditable evidence that an agent meets quality and safety standards
- Reproducible agent configurations versioned as TOML files in git

---

## Pipeline

```
Verdandi → Draupnir → Nornir → Regin → Galdr
 (types)   (schemas)  (gates)  (resolver) (composer)
```

Everything upstream of Galdr exists to produce one clean, typed, gate-validated Pydantic model: the `anthropic_render` data structure — one top-level section per section of the final agent prompt, plus frontmatter and dispatcher.

Galdr's job is simple: combine data with structure, content, and display choices to produce markdown.

---

## Four Input Axes

Every rendered agent prompt is the product of four independent inputs:

| Axis | Source | Controls |
|------|--------|----------|
| **Data** | `anthropic_render.toml` | What to say — field values, paths, parameters, instructions |
| **Structure** | `structure.toml` | What to include — visibility toggles, variant selectors, section ordering |
| **Content** | `content.toml` | How to word it — prose fragments, templates, headings, framing, variant alternatives |
| **Display** | `display.toml` | How to format it — list types, thresholds, separators, visual containers |

Structure is stable across experiments. Content is the primary experimental surface — swap content files to test different prose framings. Display is orthogonal to both — any content works with any display.

An optional **override.toml** applies deltas on top of the base three, allowing fine-grained experiments without copying entire files.

---

## Data Axis

The data model is produced by the Regin pipeline and validated by a Nornir gate. It is a single Pydantic model carrying one top-level section per section of the rendered prompt, plus two special-path sections: `frontmatter` (YAML metadata, not body prose) and `dispatcher` (feeds the separate skill generation path).

The generated model — `structure/gen/anthropic_render.py` — IS the authoritative section list and field inventory. Read it; do not work from a remembered census. It regenerates whenever the upstream schema changes, so it cannot drift.

Live data instances are not stored in this repo. They are produced by running regin on an agent definition and land in the bragi space, one per agent, alongside the definition that produced them: `~/ai/spaces/bragi/definitions/agents/{agent-name}/anthropic_render.toml`. To get a fresh one, run regin on any agent definition there.

No reshaping. The gate-validated Pydantic model IS the data. Field names are used directly.

---

## Structure Axis

Structure.toml controls what renders without affecting how it's worded or formatted:

- **Visibility toggles** (`_visible` suffix) — show/hide prose fragments
- **Variant selectors** (`_selector` suffix) — choose among content variant sub-tables
- **Override patterns** (`_override` suffix) — substitute data values at the rendering layer
- **Section ordering** — `section_order` array controlling inter-section sequence
- **Plain enums** — presentation paradigms, organizational modes

```toml
[identity]
identity_pre_field_ordering = "identity_first"
identity_role_expertise_postscript_visible = true
identity_identity_reminder_closing_visible = false

[constraints]
constraints_pre_section_visible = true
constraints_pre_max_entries_rendered = 0
constraints_section_preamble_selector = "standalone"
```

Structure is stable — it defines the shape of what renders. Experiments typically change content or display, not structure.

---

## Content Axis

Content.toml defines every piece of text that appears in the rendered output that is not data:

- **Headings** — section titles (`heading = "Instructions"`)
- **Templates** — prose with `{{DATA}}` holes (`declaration = "You are a {{role_identity}}."`)
- **Text blobs** — pure prose with no data references
- **Variant sub-tables** — mutually exclusive prose alternatives selected by structure.toml

```toml
[identity]
identity_section_start_template = "AGENT: {{title}}"
identity_role_identity_template = "You are a {{role_identity}}."
identity_role_expertise_label = "**Your judgment is authoritative in:**"

[constraints.constraints_section_preamble_variant]
standalone = "These constraints govern your execution..."
references_instructions = "While executing your instructions..."
references_critical_rules = "These constraints are binding operational rules..."
```

Variant alternatives live in sub-tables named after their structure.toml selector. The sub-table keys ARE the allowed enum values — self-documenting, and the schema derives the enum directly from the keys.

Multiple content files can exist: `default.toml`, `stern.toml`, `concise.toml`. Each is a complete set of text for all sections.

---

## Display Axis

Display.toml defines how data renders visually — list formats, thresholds, separators, containers:

```toml
[identity]
identity_role_expertise_format = ["bulleted", "inline"]
identity_role_expertise_format_threshold = 3

[instructions]
instructions_steps_heading_format = "bold"
instructions_steps_body_container = "none"
instructions_steps_scaffolding_lightweight_threshold = 3
instructions_steps_scaffolding_standard_threshold = 7
```

Format fields use a tuple convention for count-based switching: `["above_threshold", "at_or_below"]`. Plain strings mean "always this format."

Multiple display variants can exist: `standard.toml`, `compact.toml`, `dense.toml`.

---

## Composition

One generic `compose_section()` processes all sections — no per-section code. For how the engine works, see `COMPOSITION_ENGINE_DESIGN.md` and `redesign/`.

---

## Matrix Multiplication

The composition engine enables systematic benchmarking:

```
agent_definitions  ×  llm_models  ×  display_variants  ×  content_variants  =  benchmark_matrix
```

One agent definition with 3 models, 4 display variants, and 3 content variants produces 36 agent prompts. Run them all against representative test data with known expected outputs.

Select the highest performers. Version the winning configuration. Re-run when models update.

---

## Versioning and Reproducibility

Every input is a TOML file in git:

```
definition v3 + structure v1 + content v2 + display v1 + model claude-opus-4-6
```

This fully specifies a reproducible agent configuration. No code changes to vary an agent. No hidden state. Change one file, re-run, diff the output.

---

## Regression Testing

When an underlying LLM model is updated:

1. Re-run the benchmark matrix with the new model
2. Compare results against the previous baseline
3. Identify any agents adversely affected by the upgrade
4. Adjust definitions or configurations as needed
5. Re-benchmark to verify fixes

This turns model upgrades from a hope-and-pray event into a measurable, auditable process.

---

## Auditability

For regulated industries with strict safety and audit requirements:

- **Definition**: declarative TOML describing the agent's role, permissions, instructions
- **Test data**: representative inputs with known correct outputs
- **Benchmark results**: performance across N configurations
- **Selected configuration**: which content, display, model, and why
- **Verification run**: results against held-out test data
- **Regression history**: benchmark results across model versions

Every piece is a versionable artifact. Every decision has evidence. The system produces not just agents, but proof that those agents work.
