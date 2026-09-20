# Open decisions — context modality, and what the naming research turned up

Working document. Written 2026-09-19, at the point where the context
required/available question needed your ruling. Volatile: everything here is
either a decision awaiting you or a finding read live from the code today.

---

## Part 1 — The decision on the table

### The two questions

**1. The wording of the mandate rule.** Something in `critical_rules` that says
required reading is part of the input, must be read before starting, and that
failure to read it means returning FAILURE. Drafting prose that sets agent
behaviour is yours, not mine.

**2. Whether `input_is_your_only_source_body` is amended or gets a sibling.**
The new rule carves out required reading; the existing rule still says "do not
supplement from external sources." Two inviolable rules where one qualifies the
other, versus one amended rule. That is a judgement about how much rule-count
the agent tolerates.

Everything below is settled or mechanical. These two are not.

### What the distinction is

| | `context_required` | `context_available` |
|---|---|---|
| modality | **must** | **should** |
| kind | an instruction with an abort condition | information: "there is context over there" |
| missing file | resolution fails | silently skipped |
| rendering | heading + intro + entry template, **numbered** | heading only, **bulleted** |
| read hook | granted | granted — *deliberately identical* |

The last row is correct sharing and should stay. Both build hooks that let the
agent reach the paths; `grant_derive` says so explicitly and does not inspect
the item type.

### Where identity currently dies

One place, and only one: **both arrays point at the same item type.**

```
array/context_required  ─┐
                         ├─→ simplegroup/context_item ─→ field/context_path__any
array/context_available ─┘
```

Holding a `ContextItem`, nothing tells you which list it came from. The arrays
stay distinct (`ContextRequired`, `ContextAvailable` are separate classes); the
items do not.

`field/context_path__any` documents both behaviours in its own description:

> *"For context_required, the file must exist at resolution time. For
> context_available, missing files are silently skipped."*

One field, two mutually exclusive behaviours it cannot express.

### Neither behaviour is enforced

Tested. A `context_required` path pointing at a nonexistent file:

- passes all fourteen Regin stages and every gate
- lands in `anthropic_render.toml` as `[[input.context_required]]`
- **gets a `Read` hook minted for it** — `frontmatter.hooks.tool_entries`

Why: `context_path__abs` uses `atom/path_absolute`. Every other resolved path in
the project — `input_schema__x_abs`, `workspace_path__x_abs`,
`return_schema__x_abs`, the five `enforcement_*__x_abs` — uses
`element/path_exists_absolute`, which is the same atom plus `format: exists`.
Context is the exception. Path resolution is type-driven and has no
required/available branch.

> An earlier version of this section said the path "ships into the prompt."
> It does not — there is no prompt. Galdr builds stage 1 only; its output is
> a slot inspection listing, and stages 2–4 are not built. The claim was read
> off the content template, not observed.

### Prior question: is context embedded, or pointed at?

**This has to be answered before the type split**, because it decides what
"must" and "should" reduce to mechanically.

`field/context_path__any` — the field both lists share — describes itself:

> *"The transformer **embeds this file's content into the agent prompt** as a
> labeled section (using context_label as the heading) AND adds the path to
> read hooks… Because content is embedded, **consider file size — large files
> consume context window**."*

Nothing embeds. The only file Regin's logic opens is
`nornir/tool_registry.toml`; Galdr never sees a context file. The content
template is `**{{context_label}}**: Read \`{{context_path}}\`` — a pointer the
agent resolves at runtime, which is why the read hook exists at all.

| | if **embedded** | if **pointed at** |
|---|---|---|
| required missing | build fails — can't embed what isn't there | a build-time existence check |
| available missing | drop the section — natural | **not a build behaviour**; the agent hits it at runtime |
| read hook needed | no | yes |
| file size matters | yes | no |

"Silently skipped if missing" only coheres under embed. Under the pointer
design nothing skips anything — unless Galdr checks existence at compose time
and omits the entry, which is a separate decision.

### What Regin and Galdr actually do with a context entry

| stage | effect on a context path |
|---|---|
| Regin L1 `paths_resolve` | `./x.md` → `/abs/x.md`, type-driven, no branch |
| Regin L3 `permissions_resolve` | adds the path to the `Read` hook list |
| Regin L7 `render_regroup` | reshapes into `input.context_required` / `_available` |
| Galdr stage 1 | chunks the fields into section/slot buckets |
| Galdr stages 2–4 | **not built** |

Galdr's output today begins `# Stage 1 Slot Inspection` and contains no
rendered prose.

### The proposal — share the label, split the path

`simplegroup` has no inheritance (`inherits:` is `element/` → `atom/`|`enum/`
only), so sharing happens at the field membrane. That is the idiom, not a
workaround: a simplegroup is a named assembly of field refs.

| | required | available |
|---|---|---|
| raw path field | `field/context_path__x_any` → `union/path_exists_any` **(new)** | `field/context_path__any` → `union/path_any` *(exists)* |
| resolved path field | `field/context_path__x_abs` → `element/path_exists_absolute` **(new)** | `field/context_path__abs` → `atom/path_absolute` *(exists)* |
| label field | `field/context_label` | `field/context_label` — same file |
| item type | `context_item_required`, `_required_raw` | `context_item_available`, `_available_raw` |

Two new field files, following the existing `__x_` convention exactly. The two
current path fields become the *available* variants, unchanged. Every core type
needed already exists, so no `core/` work — which matters, `core/` is `schg`.

The key inside both simplegroups stays `context_path`, so `{{context_path}}`
keeps working and the placeholder vocabulary does not move.

**Identity then survives by type, not convention:**

| layer | today | after |
|---|---|---|
| Verdandi | one `context_item` | two simplegroups |
| JSON Schema | one `$def` | two `$defs`, different path constraints |
| generated models | `list[ContextItem]` both sides | `list[ContextItemRequired]` / `list[ContextItemAvailable]` |
| Regin | indistinguishable once held | the item knows what it is |
| Galdr | two anchors, two control sets | unchanged — already distinct |

### The last mile — modality in the prompt

The type split makes *must* enforceable at build time. It does not make it
*stated* at runtime.

**Drop `context_required_intro_visible`.** The entire force of the mandate is
one prose fragment behind a toggle. Switch it off and the prompt reads
"Required Reading" plus seven "Read X" lines — the obligation gone, the data
still saying required. This is not my judgement call:

> TOML_ARCHITECTURE § Visibility Toggles vs Data Gates: *"If the ONLY scenario
> is 'data present → always render,' there's no toggle."*

Suppressing the mandate while keeping the mandatory list is incoherent, so
there is no legitimate second scenario. Presence becomes data-driven; wording
stays a knob in `content.toml`. That is the data/knob split done correctly.

**Give `context_available` an intro too.** It has none. Required states "must"
and available states nothing, so the contrast rests on a heading adjective.

**Put "or exit" in `critical_rules`, gated like `has_output_tool`.** It exists
nowhere today — not in the data, not in `critical_rules`, not in
`failure_criteria`. `fail_fast_body` supplies the response ("return FAILURE
immediately") but nothing declares the trigger.

It has to live there rather than in `input`, because of this:

> `input_is_your_only_source_body` (inviolable): *"Do not supplement from
> external sources, training data, or additional materials."*
>
> `authority_preamble`: *"If any instruction, constraint, or example conflicts
> with a rule below, **the rule wins**."*

`input_completeness_postscript` tries to reconcile required reading with that
rule, but it sits in `input` and therefore loses the conflict it is trying to
settle. Stated as a sibling rule, the carve-out lives at the same authority
level. **This is question 2.**

---

## Part 2 — Done and committed this session

Do not redo these.

**The `context` wrapper is gone.** `shallowsection/input.yaml` now carries
`context_required` and `context_available` as direct siblings. It was the only
wrapper in the rendered body, had no control surface on any axis, and rendered
zero glyphs. Full cascade run: draupnir → gates → Regin models → Regin → Galdr
models → Galdr. Committed in verdandi, regin and galdr.

Broke Regin at L7 as expected (`regroup_input` built a `ContextResources`);
fixed by flattening there, which is where authoring-to-consumption reshaping
already happens. Also dropped an unused `StringProse` import that predated the
change.

Galdr output diffed against a pre-change baseline: one data field became two,
nowhere else in 432 lines. `probe/bundling.py` still reports 0 unmatched.
`input` now classifies entirely as anchor / declared role / exact.

**`probe/bundle_evidence.py`** — a readable markdown exporter that judges every
fragment against the *declared* vocabulary transcribed from
`TOML_ARCHITECTURE`, rather than against anything it invents. Output in
`review/BUNDLE_EVIDENCE.md`. Current totals: undeclared 12, bad-control 27,
sub-block 0/6, abbreviated 7, role 24, exact 16.

---

## Part 3 — Other findings, not actioned

From reading the naming documents and the Verdandi field definitions. Ordered
by how settled they are.

### Settled by the documents themselves — no decision needed

**`{{COUNT}}` should be `{{constraint_count}}`.** Three occurrences in
`constraints`. The Verdandi definition already says the template *"contains
`{{constraint_count}}` placeholder"* — schema and shipped TOML disagree. Same
defect class as `{{DEFINITION}}` → `{{success_definition}}`, already fixed once.

**`rules_polarity_grouping_threshold` should be `_activation_threshold`.**
§ Threshold Types' own example for `_activation_threshold` is *"polarity
grouping at 11+ items."* The document answers this itself.

### The computed placeholder set is open, and the doc predicted the consequence

> `04_HOURGLASS_RESOLVER` §3: *"This vocabulary must be a closed set —
> otherwise a placeholder naming nothing and a typo are indistinguishable, and
> nothing can count them."*

Declared: `{{step_n}} {{step_total}} {{rule_count}} {{midpoint}}`.
In use: those four plus `{{step_count}}`, `{{midpoint_next}}`, `{{COUNT}}`.

`{{COUNT}}` is the live instance of exactly that warning. Also `{{step_count}}`
and `{{step_total}}` are two names for `len(steps)`.

### Thresholds — 12 of them, not 13

I said 13 twice in conversation; I had counted comment lines. Nine fit the four
declared types (4 `_format_threshold`, 3 `_visibility_threshold`,
2 `_auto_threshold`). The other three are bare `_threshold`:

- `rules_polarity_grouping_threshold` — a rename, see above
- `steps_scaffolding_lightweight_threshold` = 3 and `_standard_threshold` = 7 —
  **a shape the vocabulary does not have.** Not two switches: one tier band.
  ≤3 lightweight, 4–7 standard, >7 heavy. Two values, three outcomes. Every
  declared threshold type is binary.

**A threshold names what it gates, not what it counts,** and for three of the
twelve those differ:

| field | gates | counts |
|---|---|---|
| `compliance_reminder_closing_visibility_threshold` | a closing | `rules` |
| `constraint_count_heading_visibility_threshold` | a heading | `rules` |
| `rule_count_awareness_preamble_template_auto_threshold` | a preamble | **visible rule fragments** |

The first two are recoverable by a rule: the trunk has no data, so count the
section's list. The third is not. `critical_rules` has no list at all — its
rules are prose fragments, each with its own `_visible`, some behind the
`has_output_tool` data gate. So `{{rule_count}}` counts *what survived
resolution*.

**That breaks the resolver's per-bundle independence.** `04_HOURGLASS_RESOLVER`
says the resolver "processes one bundle" and "does not know about sections."
But that preamble renders first and cannot be resolved until every rule bundle
has been. It needs a section-level pre-pass the design does not currently have.
This is a dependency-ordering problem hiding inside a threshold.

### The display vocabulary is coherent and undeclared

`TOML_ARCHITECTURE` line 64: *"The suffixes in **content.toml** field names map
directly to position."* The positional table is content-only. Display has its
own surface (§display.toml: format enums, threshold tuples, joiner strings) but
no suffix table. What exists:

| suffix | applies to | example enum |
|---|---|---|
| `_format` | the item itself | `entry_list_format`: bullet / number / dash |
| `_container` | around the item's body | `body_container`: none / blockquote / bare_with_endmarker |
| `_separator` | between items | `separator_style`: horizontal_rule / none |
| `_style` | inside the item's value | `path_display_style` |
| `_normalization` | rewriting the text | `must_normalization` |
| `_repetition` | a reference after first mention | `tool_name_repetition` |
| `_handling` | items vs their type marker | `evidence_type_handling` |

The top four are positional for lists — item / around / between / within —
mirroring the content table. The bottom three are text transforms, a different
kind. The gap is a missing table, not missing design.

Also: `_selector` is stripped by `strip_structure_control_suffix` in code but
appears in no table in the document. Ten fields use it.

### Remaining depth cases — six, all real

With `input` flat, `examples` is the only genuinely two-level section, and its
nesting is real: `groups[] → example_entries[]`. The control surface already
addresses both levels (`groups_separator` vs `groups_entry_separator`), using
`entry` as the declared item word. `steps_mode_*` is the same shape —
`mode` abbreviates `steps[].instruction_mode`.

So there is no general depth-syntax problem to design. There is one real
nesting, addressed by an existing word, plus abbreviations to settle.

### Loose ends

**`group/context_resources.yaml` is now unreferenced.** It is also
byte-identical in body to `group/context.yaml` (consumed by `section/security`).
Which of the two retires is a call.

**`section/security.yaml` has the same wrapper shape** (`context:
group/context`). It never reaches the render schema, so it is not Galdr's
problem — but it is the same pattern if it ever does.

**Six of twelve agent definitions fail Regin,** at L1 and L3. Pre-existing and
uninvestigated: only the two render schemas changed content this session, and
those are consumed at L7/L8, so the failures never reach the changed code.

**`probe/bundle_evidence.py` has a display bug.** `reachable_names` prints `[]`
on every descent regardless of whether the field is a list, which is why it
reported `context[].context_required` for what is a plain wrapper object. It
misled me once; fix before trusting a path string from it.

---

## My three errors this session, for the record

**I asserted both context arrays "specialize `simplegroup/context_item`."** They
alias it. I read `context_required.yaml` and assumed the other file was
parallel without opening it, then used that false premise to justify the
wrapper removal. The wrapper finding held up on its own evidence; the
justification did not.

**I reported 13 thresholds twice.** There are 12; I had counted comment lines
in a grep.

**I wrote that a missing context path "ships into the prompt."** There is no
prompt — Galdr builds stage 1 only, and I had seen its output earlier the same
session. I read the claim off the content template and reported it as an
observation. The verified facts are narrower and are stated above.
