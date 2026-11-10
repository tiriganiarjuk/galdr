# Critical Rules Section — Four-Axis Review

## Data (CriticalRules)

```
CriticalRules
  .workspace_path    PathExistsAbsolute (scalar)
  .has_output_tool   Boolean (gate)
  .tool_name         ToolName/SnakeString (scalar, optional)
  .name_needed       OutputToolNameNeeded/Boolean (scalar, optional)
  .batch_size        OutputToolBatchSize/Integer (scalar, optional)
```

Agent-builder: `has_output_tool = False`, tool fields absent.

## Content (CriticalRulesContent)

| | # | Field | Type | Suffix | Slot | Value |
|---|---|-------|------|--------|------|-------|
| ✅ | 1 | `section_start` | StringText | `section_start` | heading | `"INVIOLABLE OPERATING RULES"` |
| ✅ | 2 | `authority_preamble` | StringProse | `_preamble` | preamble | `"Every rule below is a hard boundary..."` |
| ✅ | 3 | `rule_count_awareness_preamble_template` | StringTemplate | `_preamble_template` | preamble | `"There are {{rule_count}} inviolable rules below. All must be followed."` |
| ✅ | 4 | `workspace_confinement_template` | StringTemplate | `_template` | body | `"Your workspace is {{workspace_path}}. Nothing outside this path exists..."` |
| ✅ | 5 | `output_tool_exclusivity_template` | StringTemplate | `_template` | body | `"{{tool_name}} is your only output mechanism. All output goes through this tool."` |
| ✅ | 6 | `batch_discipline_template` | StringTemplate | `_template` | body | `"Process in batches of {{batch_size}}. After every {{batch_size}} records..."` |
| ✅ | 7 | `fail_fast_body` | StringProse | `_body` | body | `"On error: return FAILURE immediately..."` |
| ✅ | 8 | `input_is_your_only_source_body` | StringProse | `_body` | body | `"Your input defines your world. Process what you received..."` |
| ✅ | 9 | `no_invention_body` | StringProse | `_body` | body | `"Every claim in your output must trace to your input..."` |
| ✅ | 10 | `discipline_over_helpfulness_body` | StringProse | `_body` | body | `"Being helpful here means being disciplined..."` |

## Structure (CriticalRulesStructure)

| | # | Field | Type | Value | Controls |
|---|---|-------|------|-------|----------|
| ✅ | 1 | `authority_preamble_visible` | Boolean | `true` | → content #2 |
| ✅ | 2 | `rule_count_awareness_preamble_visible` | VisibilityMode | `"auto"` | → content #3 (threshold-gated) |
| ✅ | 3 | `rule_count_awareness_preamble_template_auto_threshold` | Integer | `5` | threshold for above |
| ✅ | 4 | `workspace_confinement_visible` | Boolean | `true` | → content #4 |
| ✅ | 5 | `fail_fast_body_visible` | Boolean | `true` | → content #7 |
| ✅ | 6 | `input_is_your_only_source_body_visible` | Boolean | `true` | → content #8 |
| ✅ | 7 | `no_invention_body_visible` | Boolean | `true` | → content #9 |
| ✅ | 8 | `output_tool_exclusivity_visible` | Boolean | `true` | → content #5 |
| ✅ | 9 | `batch_discipline_visible` | Boolean | `true` | → content #6 (also requires batch_size) |
| ✅ | 10 | `discipline_over_helpfulness_body_visible` | Boolean | `false` | → content #10 |

## Display (CriticalRulesDisplay)

| | # | Field | Type | Value | Controls |
|---|---|-------|------|-------|----------|
| ⚠️ | 1 | `workspace_path_format` | InlineFormat | `"backtick"` | wrap `{{workspace_path}}` in backticks — not wired |
| ⚠️ | 2 | `tool_name_format` | InlineFormat | `"backtick"` | wrap `{{tool_name}}` in backticks — not wired |
| ⚠️ | 3 | `tool_name_repetition` | CriticalRulesToolNameRepetition | `"repeat"` | full name vs shorthand — not wired |
| ⚠️ | 4 | `batch_size_format` | InlineFormat | `"plain"` | batch size rendering style — not wired |
| ⚠️ | 5 | `pre_body_entry_separator_override` | SeparatorContent (optional) | `"double_newline"` | Body-entry separator override — not wired |
| ⚠️ | 6 | `pre_section_divider_override` | SeparatorContent (optional) | `null` | Section-level divider override — not wired |

---

## Rendering Order

```
HEADING:
  ✅ section_start                          "INVIOLABLE OPERATING RULES"

PREAMBLE:
  ✅ authority_preamble                     "Every rule below is a hard boundary..."
                                             [visible: authority_preamble_visible = true]
  ✅ rule_count_awareness_preamble_template "There are {{rule_count}} inviolable rules below..."
                                             [visible: rule_count_awareness_preamble_visible = "auto", threshold = 5]

BODY (per-trunk, matches BUNDLE_INSPECTION.md):
  [workspace_path]
    ✅ data.workspace_path                  SCALAR (interpolated into {{workspace_path}})
    ⚠️ workspace_path_format                "backtick" — not wired

  [has_output_tool]
    ✅ data.has_output_tool                 GATE (drives output_tool_exclusivity + batch_discipline visibility)

  [tool_name]
    ✅ data.tool_name                       SCALAR (interpolated into {{tool_name}})
    ⚠️ tool_name_format                     "backtick" — not wired
    ⚠️ tool_name_repetition                 "repeat" — not wired

  [name_needed]
    ⚠️ data.name_needed                     SCALAR — no content field references it (see ISSUE 2)

  [batch_size]
    ⚠️ data.batch_size                      SCALAR (RootModel[int] — unwrap not handled, see ISSUE 1)
    ⚠️ batch_size_format                    "plain" — not wired

  [workspace_confinement]
    ✅ workspace_confinement_template       "Your workspace is {{workspace_path}}. Nothing outside this path exists..."
                                             [visible: workspace_confinement_visible = true]

  [output_tool_exclusivity]
    ✅ output_tool_exclusivity_template     "{{tool_name}} is your only output mechanism..."
                                             [visible: output_tool_exclusivity_visible = true]

  [batch_discipline]
    ✅ batch_discipline_template            "Process in batches of {{batch_size}}..."
                                             [visible: batch_discipline_visible = true]

  [fail_fast_body]
    ✅ fail_fast_body                       "On error: return FAILURE immediately..."
                                             [visible: fail_fast_body_visible = true]

  [input_is_your_only_source_body]
    ✅ input_is_your_only_source_body       "Your input defines your world..."
                                             [visible: input_is_your_only_source_body_visible = true]

  [no_invention_body]
    ✅ no_invention_body                    "Every claim in your output must trace to your input..."
                                             [visible: no_invention_body_visible = true]

  [discipline_over_helpfulness_body]
    ✅ discipline_over_helpfulness_body     "Being helpful here means being disciplined..."
                                             [visible: discipline_over_helpfulness_body_visible = false]

CLOSING:
  (none)
```

---

## Issues

### ⚠️ ISSUE 1: `batch_size` is RootModel[int] — unwrap not handled

`batch_size` is typed `OutputToolBatchSize` which is `RootModel[int]`. The current data unwrap only handles `RootModel[str]`. Interpolating `{{batch_size}}` into `batch_discipline_template` will fail or produce a wrong value.

**Fix required:** Extend the scalar unwrap to handle `RootModel[int]`, converting to string for interpolation.

### ⚠️ ISSUE 2: `name_needed` data field has no content connection

`name_needed` (OutputToolNameNeeded/Boolean) is a scalar in the data model but no content template references it and no structure toggle is named for it. It appears unused.

**Fix required:** Determine whether `name_needed` should be exposed in this section at all, or if it is only used by `writing_output`.

### ⚠️ ISSUE 3: All display controls not wired

Five display fields control inline formatting (backtick wrapping, repetition, separators). None are read by the engine. Rules currently render with hardcoded defaults.
