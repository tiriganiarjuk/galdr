# Open decisions — context modality, and what the naming research turned up

Working document, 2026-09-19. Volatile: everything here is either a decision
awaiting you or a finding read live from the code today.

---

## The frame

Regin and Galdr are a **build system for subagent prompts**. One definition
produces two prose products for two readers:

- **the dispatcher** — `dispatcher.*`: name, description, dispatch mode, input
  description, parameters. What a caller needs to decide whether and how to
  invoke this agent.
- **the agent** — `frontmatter` plus the thirteen body sections. The prompt the
  agent runs on.

Almost nothing here can be *guarded* at runtime, and it is not meant to be.
The deliverable is a **consistent and solid definition**. So the questions
worth asking are: does the emitted prose say what the data means, does it
contradict itself, and does the schema tell an author the truth about what
their input will do.

Findings below are graded on that scale, not on whether something is
enforceable.

---

## Part 1 — The decision on the table

### The three questions

**0. Is context embedded, or pointed at?** This governs the other two — see
below. Nothing in the pipeline embeds, but the schema says it does.

**1. The wording of the mandate rule.** Something in `critical_rules` saying
required reading is part of the input, must be read before starting, and that
failing to read it means returning FAILURE. Prose that sets agent behaviour is
yours.

**2. Whether `input_is_your_only_source_body` is amended or gets a sibling.**
One rule qualified, or two inviolable rules where one carves out the other.

### What the distinction is

| | `context_required` | `context_available` |
|---|---|---|
| modality | **must** | **should** |
| kind | an instruction with an abort condition | information: "there is context over there" |
| rendering | heading + intro + entry template, **numbered** | heading only, **bulleted** |
| read hook | granted | granted — *deliberately identical* |

The last row is correct sharing and should stay. `grant_derive` says so
explicitly and does not inspect the item type.

**The deliverable is that these two read differently to the agent.** Must-
language and should-language, unmistakably distinct. Everything mechanical
below is in service of that.

### Where identity dies

One place: **both arrays point at the same item type.**

```
array/context_required  ─┐
                         ├─→ simplegroup/context_item ─→ field/context_path__any
array/context_available ─┘
```

The arrays stay distinct (`ContextRequired`, `ContextAvailable` are separate
classes). The items do not — holding a `ContextItem`, nothing tells you which
list it came from.

The shared field documents both behaviours in its own description:

> *"For context_required, the file must exist at resolution time. For
> context_available, missing files are silently skipped."*

One field, two mutually exclusive behaviours it cannot express.

### Question 0 — embedded or pointed at?

`field/context_path__any` describes itself:

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
| available missing | drop the section — natural | not a build behaviour; the agent hits it at runtime |
| read hook needed | no | yes |
| file size matters | yes | no |

Two consequences, both about definition quality rather than enforcement:

- **An author reading that description builds on a false model** — avoiding
  large files for no reason, or expecting content to already be present.
- **"Silently skipped" only coheres under embed.** Under the pointer design
  nothing skips anything.

### What the stages actually do to a context entry

| stage | effect |
|---|---|
| Regin L1 `paths_resolve` | `./x.md` → `/abs/x.md`, type-driven, no required/available branch |
| Regin L3 `permissions_resolve` | adds the path to the `Read` hook list |
| Regin L7 `render_regroup` | reshapes into `input.context_required` / `_available` |
| Galdr stage 1 | chunks fields into section/slot buckets |
| Galdr stages 2–4 | **not built** — no prose is rendered yet |

### Build hygiene: a missing required file produces an incoherent definition

Tested. A `context_required` path pointing at a nonexistent file passes all
fourteen Regin stages, lands in `anthropic_render.toml`, and **gets a `Read`
hook minted for it** in `frontmatter.hooks.tool_entries`.

Nothing is breached — but the definition instructs an agent to read a file
that does not exist, and grants access to nothing. That is an inconsistent
artifact, which is the thing this build system exists to prevent.

Why it happens: `context_path__abs` uses `atom/path_absolute`. Every other
resolved path — `input_schema__x_abs`, `workspace_path__x_abs`,
`return_schema__x_abs`, the five `enforcement_*__x_abs` — uses
`element/path_exists_absolute`, the same atom plus `format: exists`. Context is
the exception.

### The proposal — share the label, split the path

`simplegroup` has no inheritance (`inherits:` is `element/` → `atom/`|`enum/`
only), so sharing happens at the field membrane. That is the idiom: a
simplegroup is a named assembly of field refs.

| | required | available |
|---|---|---|
| raw path field | `field/context_path__x_any` → `union/path_exists_any` **(new)** | `field/context_path__any` → `union/path_any` *(exists)* |
| resolved path field | `field/context_path__x_abs` → `element/path_exists_absolute` **(new)** | `field/context_path__abs` → `atom/path_absolute` *(exists)* |
| label field | `field/context_label` | `field/context_label` — same file |
| item type | `context_item_required`, `_required_raw` | `context_item_available`, `_available_raw` |

Two new field files on the existing `__x_` convention. The two current path
fields become the *available* variants, unchanged. Every core type needed
already exists, so no `core/` work — `core/` is `schg`.

The key inside both simplegroups stays `context_path`, so `{{context_path}}`
keeps working and the placeholder vocabulary does not move.

Identity then survives by type rather than by convention: two simplegroups →
two `$defs` → `list[ContextItemRequired]` / `list[ContextItemAvailable]`.

### The prose work — which is the actual deliverable

**Drop `context_required_intro_visible`.** The entire force of the mandate is
one prose fragment behind a toggle. Switch it off and the prompt says "Required
Reading" plus seven "Read X" lines: the data still says required, the prose no
longer says must. **A knob that can make the definition contradict itself is
the defect** — not that the mandate is unenforceable.

Not a judgement call:

> TOML_ARCHITECTURE § Visibility Toggles vs Data Gates: *"If the ONLY scenario
> is 'data present → always render,' there's no toggle."*

Presence becomes data-driven; wording stays a knob in `content.toml`. That is
the data/knob split done correctly.

**Give `context_available` an intro.** It has none, so "should" is never
stated. Required says must, available says nothing, and the contrast rests on
one word in a heading.

**Write the "or exit" sentence, and put it in `critical_rules`.** It exists
nowhere — not in the data, not in `critical_rules`, not in `failure_criteria`.
`fail_fast_body` supplies the response ("return FAILURE immediately") but
nothing names the trigger. **This is question 1.**

It belongs in `critical_rules` rather than `input` because of a live
contradiction:

> `input_is_your_only_source_body` (inviolable): *"Do not supplement from
> external sources, training data, or additional materials."*
>
> `authority_preamble`: *"If any instruction, constraint, or example conflicts
> with a rule below, **the rule wins**."*

`input_completeness_postscript` tries to reconcile required reading with that
rule, but sits in `input` and therefore loses the conflict it is trying to
settle. **Two sentences in one prompt that contradict, with an authority clause
resolving against the one we want — this is the clearest "not a consistent
definition" finding in the set.** Stated as a sibling rule, the carve-out lives
at the same authority level. **This is question 2.**

Note how question 0 bears on it: if context is *pointed at*, the agent really
does read external files at runtime and the conflict is sharp. If *embedded*,
there is no external reading and no carve-out is needed.

---

## Part 2 — Done and committed this session

Do not redo these.

**The `context` wrapper is gone.** `shallowsection/input.yaml` carries
`context_required` and `context_available` as direct siblings. It was the only
wrapper in the rendered body, had no control surface on any axis, and rendered
nothing. Full cascade: draupnir → gates → Regin models → Regin → Galdr models →
Galdr. Committed in verdandi, regin, galdr.

Broke Regin at L7 as expected (`regroup_input` built a `ContextResources`);
fixed by flattening there, where authoring-to-consumption reshaping already
happens. Also dropped an unused `StringProse` import that predated the change.

Galdr output diffed against a pre-change baseline: one data field became two,
nowhere else in 432 lines. `probe/bundling.py` still reports 0 unmatched.
`input` now classifies entirely as anchor / declared role / exact.

**`probe/bundle_evidence.py`** — a readable markdown exporter judging every
fragment against the *declared* vocabulary transcribed from
`TOML_ARCHITECTURE`. Output in `review/BUNDLE_EVIDENCE.md`. Totals: undeclared
12, bad-control 27, sub-block 0/6, abbreviated 7, role 24, exact 16.

---

## Part 3 — Other findings, not actioned

From the naming documents and the Verdandi field definitions.

### The documents answer these themselves

**`{{COUNT}}` should be `{{constraint_count}}`.** Three occurrences in
`constraints`. The Verdandi definition already says the template *"contains
`{{constraint_count}}` placeholder"* — schema and shipped TOML disagree. Same
class as `{{DEFINITION}}` → `{{success_definition}}`, already fixed once.

**`rules_polarity_grouping_threshold` should be `_activation_threshold`.**
§ Threshold Types' own example for `_activation_threshold` is *"polarity
grouping at 11+ items."*

### The computed placeholder set is open, and the doc predicted it

> `04_HOURGLASS_RESOLVER` §3: *"This vocabulary must be a closed set —
> otherwise a placeholder naming nothing and a typo are indistinguishable, and
> nothing can count them."*

Declared: `{{step_n}} {{step_total}} {{rule_count}} {{midpoint}}`.
In use: those four plus `{{step_count}}`, `{{midpoint_next}}`, `{{COUNT}}`.

`{{COUNT}}` is the live instance of that warning. `{{step_count}}` and
`{{step_total}}` are two names for `len(steps)`.

### Thresholds — 12 of them

Nine fit the four declared types (4 `_format_threshold`, 3
`_visibility_threshold`, 2 `_auto_threshold`). Three are bare `_threshold`:

- `rules_polarity_grouping_threshold` — a rename, above
- `steps_scaffolding_lightweight_threshold` = 3 and `_standard_threshold` = 7 —
  **a shape the vocabulary lacks.** One tier band, not two switches: ≤3
  lightweight, 4–7 standard, >7 heavy. Two values, three outcomes. Every
  declared threshold type is binary.

**A threshold names what it gates, not what it counts.** For three of twelve
those differ:

| field | gates | counts |
|---|---|---|
| `compliance_reminder_closing_visibility_threshold` | a closing | `rules` |
| `constraint_count_heading_visibility_threshold` | a heading | `rules` |
| `rule_count_awareness_preamble_template_auto_threshold` | a preamble | **visible rule fragments** |

The first two are recoverable by rule: the trunk has no data, count the
section's list. The third is not. `critical_rules` has no list — its rules are
prose fragments, each with its own `_visible`, some behind the
`has_output_tool` gate. `{{rule_count}}` counts *what survived resolution*.

**That breaks the resolver's per-bundle independence.**
`04_HOURGLASS_RESOLVER` says the resolver "processes one bundle" and "does not
know about sections," but that preamble renders first and cannot resolve until
every rule bundle has. It needs a section-level pre-pass the design does not
have. A dependency-ordering problem hiding inside a threshold.

### The display vocabulary is coherent and undeclared

`TOML_ARCHITECTURE` line 64: *"The suffixes in **content.toml** field names map
directly to position."* The positional table is content-only. Display has a
declared category (§display.toml) but no suffix table. What exists:

| suffix | applies to | example enum |
|---|---|---|
| `_format` | the item itself | `entry_list_format` |
| `_container` | around the item's body | `body_container` |
| `_separator` | between items | `separator_style` |
| `_style` | inside the item's value | `path_display_style` |
| `_normalization` | rewriting the text | `must_normalization` |
| `_repetition` | a reference after first mention | `tool_name_repetition` |
| `_handling` | items vs their type marker | `evidence_type_handling` |

The top four are positional for lists — item / around / between / within —
mirroring the content table. The bottom three are text transforms. A missing
table, not missing design.

`_selector` is stripped in code but appears in no table. Ten fields use it.

### Remaining depth cases — six, all real

With `input` flat, `examples` is the only genuinely two-level section, and its
nesting is real: `groups[] → example_entries[]`. The control surface addresses
both levels (`groups_separator` vs `groups_entry_separator`) using `entry` as
the declared item word. `steps_mode_*` is the same shape — `mode` abbreviates
`steps[].instruction_mode`.

No general depth-syntax problem to design. One real nesting, addressed by an
existing word, plus abbreviations to settle.

### Loose ends

**`group/context_resources.yaml` is unreferenced** and byte-identical in body
to `group/context.yaml` (consumed by `section/security`). Which retires is a
call.

**`section/security.yaml` has the same wrapper shape.** It never reaches the
render schema, so not Galdr's problem — but the same pattern if it ever does.

**Six of twelve agent definitions fail Regin,** at L1 and L3. Pre-existing and
uninvestigated: only the two render schemas changed content this session, and
those are consumed at L7/L8.

**`probe/bundle_evidence.py` has a display bug.** `reachable_names` prints `[]`
on every descent regardless of whether the field is a list, which is why it
reported `context[].context_required` for a plain wrapper object. It misled me
once; fix before trusting a path string from it.

---

## My errors this session, for the record

**I asserted both context arrays "specialize `simplegroup/context_item`."** They
alias it. I read `context_required.yaml` and assumed the other file was
parallel without opening it, then used that premise to justify the wrapper
removal. The wrapper finding held on its own evidence; the justification did
not.

**I reported 13 thresholds twice.** There are 12; I counted comment lines.

**I wrote that a missing context path "ships into the prompt."** There is no
prompt — Galdr builds stage 1 only, and I had seen its output earlier the same
session. I read the claim off the content template and reported it as
observation.

**I graded the whole context investigation as "enforcement."** Regin and Galdr
cannot reach runtime; they emit prose. The scale is whether the definition is
consistent, not whether behaviour is guaranteed. Several findings changed
weight when regraded — the `input_is_your_only_source` contradiction went from
one item in a list to the most important thing in it.
