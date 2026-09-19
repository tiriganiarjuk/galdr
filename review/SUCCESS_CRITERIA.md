# Success Criteria Section — Four-Axis Review

## Data (SuccessCriteria)

```
SuccessCriteria
  └─ criteria: list of SuccessItem
       .success_definition    SuccessDefinition (scalar)
       .success_evidence      list of StringProse (scalar list)
```

Agent-builder has 1 SuccessItem. Each item has a definition string and a list of evidence strings.

## Content (SuccessCriteriaContent)

| | # | Field | Type | Suffix | Slot | Value |
|---|---|-------|------|--------|------|-------|
| ✅ | 1 | `section_start` | StringText | `section_start` | heading | `"Success Criteria"` |
| ✅ | 2 | `criteria_separator` | TitleString | `_separator` | body | `"Additionally"` |
| ✅ | 3 | `verification_guidance_postscript` | StringProse | `_postscript` | body | `"Some conditions above are mechanically verifiable; others require your judgment..."` |
| ✅ | 4 | `success_failure_independence_statement_postscript` | StringProse | `_postscript` | body | `"Success criteria define quality. Failure criteria define breakage. These are independent evaluations."` |
| ✅ | 5 | `definition_declaration_variant_template` | BaseModel | `_variant_template` | body | `{declarative_assertion: "{{success_definition}}", conditional_gate: "...", completion_identity: "..."}` |
| ✅ | 6 | `evidence_intro_variant` | BaseModel | `_variant` | body | `{properties: "A successful output has these properties:", verification_checklist: "...", quality_signals: "..."}` |
| ✅ | 7 | `definition_to_evidence_transition_variant` | BaseModel | `_variant` | body | `{goal_then_criteria: "Meeting this standard means:", proof: "...", dual_presentation: "..."}` |

## Structure (SuccessCriteriaStructure)

| | # | Field | Type | Value | Controls |
|---|---|-------|------|-------|----------|
| ⚠️ | 1 | `pre_section_visible` | Boolean | `true` | master section toggle — not checked by engine |
| ✅ | 2 | `pre_max_entries_rendered` | Integer | `0` | render all entries (0 = all) |
| ✅ | 3 | `definition_declaration_selector` | SuccessCriteriaDefinitionDeclarationSelector | `"declarative_assertion"` | → selects key in content #5 |
| ✅ | 4 | `evidence_intro_selector` | SuccessCriteriaEvidenceIntroSelector | `"properties"` | → selects key in content #6 |
| ✅ | 5 | `definition_to_evidence_transition_selector` | SuccessCriteriaDefinitionToEvidenceTransitionSelector | `"goal_then_criteria"` | → selects key in content #7 |
| ⚠️ | 6 | `criteria_evidence_type_handling` | SuccessCriteriaEvidenceTypeHandling | `"undifferentiated"` | per-item evidence classification — not implemented |
| ✅ | 7 | `success_failure_independence_statement_postscript_visible` | Boolean | `true` | → content #4 |
| ✅ | 8 | `verification_guidance_postscript_visible` | Boolean | `false` | → content #3 |
| ⚠️ | 9 | `criteria_relationship` | SuccessCriteriaMultiCriteriaRelationship | `"independent_blocks"` | how multiple criteria relate visually — not implemented |

## Display (SuccessCriteriaDisplay)

| | # | Field | Type | Value | Controls |
|---|---|-------|------|-------|----------|
| ⚠️ | 1 | `criteria_evidence_format` | UnionFormatOrPair | `["bulleted", "numbered"]` | threshold-based evidence list format — not wired |
| ⚠️ | 2 | `criteria_evidence_format_threshold` | Integer | `5` | switch to numbered above 5 items — not wired |
| ⚠️ | 3 | `pre_section_divider_override` | SeparatorContent (optional) | `null` | Section-level divider override — not wired |
| ⚠️ | 4 | `pre_body_entry_separator_override` | SeparatorContent (optional) | `null` | Body-entry separator override — not wired |

---

## Rendering Order

```
HEADING:
  ✅ section_start                         "Success Criteria"

BODY:
  For each SuccessItem:
    .success_definition                    → scalar string (SuccessDefinition)
    .success_evidence                      → list of StringProse scalars

    ⚠️ definition_declaration_variant_template  {selector: "declarative_assertion" → "{{success_definition}}"}
                                             wraps success_definition — per-item rendering not yet wired
    ⚠️ definition_to_evidence_transition_variant  {selector: "goal_then_criteria" → "Meeting this standard means:"}
                                             transition between definition and evidence list — not wired
    ⚠️ evidence_intro_variant              {selector: "properties" → "A successful output has these properties:"}
                                             framing label before evidence list — not wired
    ⚠️ evidence list                       renders success_evidence items
                                             [display: criteria_evidence_format = ["bulleted", "numbered"], threshold = 5]

  criteria_separator                       "Additionally" — rendered between items when >1 criteria
                                             [visible: implicit — always rendered between items]

  verification_guidance_postscript         "Some conditions above are mechanically verifiable..."
                                             [visible: verification_guidance_postscript_visible = false]
  success_failure_independence_statement_postscript  "Success criteria define quality. Failure criteria define breakage..."
                                             [visible: success_failure_independence_statement_postscript_visible = true]

CLOSING:
  (none)
```

---

## Issues

### ⚠️ ISSUE 1: Per-item variant framing not wired for per-item rendering

The three variant fields (`definition_declaration_variant_template`, `definition_to_evidence_transition_variant`, `evidence_intro_variant`) are body-slot content that need to be applied per criteria item. They are classified correctly by suffix but the engine's per-item rendering loop does not yet use them as decoration templates around each item's data.

### ⚠️ ISSUE 2: `criteria_evidence_type_handling` not implemented

Structure control for per-item evidence classification (`"undifferentiated"`) exists but is not read.

### ⚠️ ISSUE 3: `criteria_relationship` not implemented

`criteria_relationship = "independent_blocks"` controls visual grouping when there are multiple criteria items. Not implemented.

### ⚠️ ISSUE 4: `criteria_evidence_format` display threshold not wired

Evidence list format switches between bulleted and numbered based on count vs threshold. Engine does not read the threshold.

### ⚠️ ISSUE 5: `pre_section_visible` master toggle not checked by engine

Same as other sections — section-skip decision not implemented at orchestrate level.

---

See `plans/DEFERRED_RENDERING_FEATURES.md` for deferred rendering features (`output_vs_agent_voice`) that were unlinked from the schema pending engine support.
