# Instructions Section — Four-Axis Review

## Data (Instructions)

```
Instructions
  steps: list of InstructionStep
    .instruction_mode    InstructionMode (enum: deterministic/probabilistic)
    .instruction_text    StringMarkdown (scalar)
```

Agent-builder has 7 steps. Modes vary per step (mixed).

## Content (InstructionsContent)

| | # | Field | Type | Suffix | Slot | Value |
|---|---|-------|------|--------|------|-------|
| ✅ | 1 | `section_start_variant_template` | BaseModel | `_variant_template` | heading | `{default: "Instructions", procedure: "Procedure", steps_with_count: "Steps ({{step_count}} total)"}` |
| ✅ | 2 | `highlight_step_count_preamble_template` | StringTemplate | `_preamble_template` | preamble | `"You will execute {{step_count}} steps."` |
| ✅ | 3 | `sequence_integrity_preamble` | StringProse | `_preamble` | preamble | `"Do not add steps. Do not skip steps. Do not reorder steps."` |
| ✅ | 4 | `follow_strictly_preamble` | StringProse | `_preamble` | preamble | `"Each instruction step is a complete specification..."` |
| ✅ | 6 | `instruction_mode_explanation_preamble_variant` | BaseModel | `_preamble_variant` | preamble | `{mixed: "...", uniform_deterministic: "...", uniform_probabilistic: "..."}` |
| ✅ | 7 | `reminder_midpoint_preamble_template` | StringTemplate | `_preamble_template` | preamble | `"You are past the halfway point..."` |
| ✅ | 8 | `steps_heading_template` | StringTemplate | `_template` | body | `"Step {{step_n}} of {{step_total}}."` |
| ✅ | 9 | `steps_heading_n_only_template` | StringTemplate | `_template` | body | `"Step {{step_n}}."` |
| ✅ | 10 | `steps_mode_label_variant` | BaseModel | `_variant` | body | `{deterministic: "**EXACT**", probabilistic: "**JUDGMENT**"}` |
| ✅ | 13 | `follow_strictly_closing_template` | StringTemplate | `_closing_template` | closing | `"These {{step_count}} steps constitute your complete task. Do not add additional steps."` |

## Structure (InstructionsStructure)

| | # | Field | Type | Value | Controls |
|---|---|-------|------|-------|----------|
| ✅ | 1 | `section_start_selector` | InstructionsHeadingSelector (enum) | `"default"` | → selects key in content #1 |
| ✅ | 2 | `instruction_mode_explanation_preamble_visible` | VisibilityMode | `"auto"` | → content #6 (auto = render when mixed modes) |
| ✅ | 3 | `highlight_step_count_preamble_visible` | Boolean | `true` | → content #2 |
| ✅ | 4 | `sequence_integrity_preamble_visible` | Boolean | `true` | → content #3 |
| ✅ | 5 | `follow_strictly_preamble_visible` | Boolean | `true` | → content #5 |
| ✅ | 6 | `steps_index_tracking` | InstructionsStepIndexTracking (enum) | `"n_of_m"` | Selects `steps_heading_template` vs `steps_heading_n_only_template` |
| ✅ | 8 | `follow_strictly_closing_visible` | Boolean | `true` | → content #13 |
| ✅ | 11 | `reminder_midpoint_preamble_visible` | Boolean | `false` | → content #7 |
| ⚠️ | 12 | `pre_scaffolding_tier_override` | InstructionsScaffoldingTierOverride | `"auto"` | Meta-policy that computes visibility toggles from step count |

## Display (InstructionsDisplay)

| | # | Field | Type | Value | Controls |
|---|---|-------|------|-------|----------|
| ✅ | 1 | `steps_heading_format` | HeadingFormat | `"bold"` | Step headers as bold/h3/h4 |
| ✅ | 2 | `steps_body_container` | BodyContainer | `"none"` | Step body wrapping (none/blockquote) |
| ✅ | 3 | `steps_mode_separator` | InlineSeparator (enum) | `"dash"` | Separator between mode label and step header (dash/colon/pipe/newline) |
| ✅ | 4 | `steps_mode_restrict_to_transition` | Boolean | `false` | When true, suppress mode labels on consecutive same-mode steps |
| ⚠️ | 5 | `steps_scaffolding_lightweight_threshold` | Integer | `3` | Step count threshold for lightweight tier |
| ⚠️ | 6 | `steps_scaffolding_standard_threshold` | Integer | `7` | Step count threshold for standard tier |
| ✅ | 7 | `steps_mode_recap_format` | InstructionModeRecapFormat | `"prose"` | Recap as prose/tabular |
| ⚠️ | 8 | `pre_section_divider_override` | SeparatorContent (optional) | `null` | Section-level divider override — not wired |
| ⚠️ | 9 | `pre_body_entry_separator_override` | SeparatorContent (optional) | `null` | Body-entry separator override — not wired |

---

## Rendering Order

```
HEADING:
  ✅ section_start_variant_template         selected by section_start_selector = "default" → "Instructions"

PREAMBLE:
  ✅ highlight_step_count_preamble_template "You will execute {{step_count}} steps."
                                             [visible: highlight_step_count_preamble_visible = true]
  ✅ sequence_integrity_preamble            "Do not add steps. Do not skip steps. Do not reorder steps."
                                             [visible: sequence_integrity_preamble_visible = true]
  ✅ follow_strictly_preamble              "Each instruction step is a complete specification..."
                                             [visible: follow_strictly_preamble_visible = true]
  ⚠️ instruction_mode_explanation_preamble_variant
                                             {selected by data condition: mixed/uniform modes}
                                             [visible: instruction_mode_explanation_preamble_visible = "auto"]
  ✅ reminder_midpoint_preamble_template   "You are past the halfway point..."
                                             [visible: reminder_midpoint_preamble_visible = false]

BODY:
  For each InstructionStep:
    MODE LABEL:  steps_mode_label_variant    selected by step's instruction_mode enum
                                             [display: steps_mode_separator = "dash"]
                                             [display: steps_mode_restrict_to_transition = false]
    STEP HEADER: steps_heading_template      "Step {{step_n}} of {{step_total}}."
                                             [structure: steps_index_tracking = "n_of_m"]
                                             [display: steps_heading_format = "bold"]
    STEP BODY:   instruction_text            rendered as markdown prose
                                             [display: steps_body_container = "none"]

CLOSING:
  ✅ follow_strictly_closing_template      "These {{step_count}} steps constitute your complete task..."
                                             [visible: follow_strictly_closing_visible = true]
```

---

## Issues

### ⚠️ ISSUE 1: `instruction_mode_explanation_preamble_variant` has no structure selector

Its variant key is computed from data (what modes are present in the steps), not from a structure selector. The engine needs to inspect the steps list to determine `mixed` vs `uniform_deterministic` vs `uniform_probabilistic`. No `_selector` field exists.

### ⚠️ ISSUE 2: `pre_scaffolding_tier_override` is a meta-policy

A meta-control that computes which visibility toggles should be active based on step count and thresholds. Not directly processable by the generic engine — may need pre-processing that resolves the tier into individual toggle values before the engine runs.

### ⚠️ ISSUE 3: `steps_index_tracking` selects between templates by non-matching names

`"n_of_m"` → use `steps_heading_template`, `"n_only"` → use `steps_heading_n_only_template`. The enum values don't match the content field names. The engine needs a mapping.

### ⚠️ ISSUE 4: Computed placeholders

`{{step_count}}`, `{{step_n}}`, `{{step_total}}`, `{{midpoint}}` are computed values, not data fields — counts and indices derived from the list in scope. The engine needs to generate these before interpolation.

This issue previously also listed `{{completion_condition}}`, `{{dependency_steps}}` and `{{mode_recap_text}}` as computed. They were not computed and were not data: they named nothing at all, and their content fields have been deleted.
