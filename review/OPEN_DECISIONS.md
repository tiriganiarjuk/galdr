# Open decisions — context modality, and what the naming research turned up

Working document, 2026-09-19. Volatile.

## Provenance — read this before trusting anything below

Three kinds of statement, marked throughout:

- **Reasoning** — Johnny's, quoted. **Authoritative.** Where anything else in
  this document conflicts with a quote, the quote wins.
- **Verified** — something run or read. Cited so it can be re-run.
- **Inference** — mine. Supersedable by either of the above, and by later
  reasoning. Marked *(inference)*.

The reason for the split: the rationale in this system has been written by
LLMs before, and inferred rationale reads exactly like recorded rationale once
it is on the page. The six systems documents got the structure right and the
purpose wrong for that reason. Several rationales below were mine before
Johnny corrected them; the corrections are in the record at the bottom.

---

## The frame

> **Reasoning.** *"Regin and galdr are a build system for subagent prompts, so
> the enforcement — most of the stuff turns into prose. One for the dispatcher,
> and one for the agent themselves. So not everything can be guarded against.
> It's about writing a consistent and solid definition."*

Two prose products from one definition:

- **dispatcher** — `dispatcher.*`: name, description, dispatch mode, input
  description, parameters. What a caller needs to decide whether and how to
  invoke.
- **agent** — `frontmatter` plus the thirteen body sections.

So the scale is **definition consistency**, not runtime enforcement. Does the
emitted prose say what the data means, does it contradict itself, does the
schema tell an author the truth about what their input will do.

---

## Part 1 — Context: required vs available

### What they are

> **Reasoning.** *"context available is information to the subagent that's
> defined — 'there is additional context over there'. context required is an
> instruction and mandatory requirement — you must utilize this context or
> exit."*
>
> *"They are in most ways similar. One is should, the other is must. Both build
> hooks that allow LLM to access the paths."*
>
> *"They should not be conflated, confused, or collapsed. They must preserve
> their identity to the end."*
>
> *"If we lose the distinction then we lose the ability to generate different
> prose varieties."*

That last line is the purpose. The distinction exists so the two can produce
**visibly different prose** — must-language and should-language. Everything
mechanical below is in service of it.

> **Reasoning** (on naming): *"We want the schema fragments to be self
> documenting, so context_available is preferred over available."*

### Where identity dies — verified

Both arrays point at the same item type:

```
array/context_required  ─┐
                         ├─→ simplegroup/context_item ─→ field/context_path__any
array/context_available ─┘
```

The arrays are distinct classes. The items are not — holding a `ContextItem`,
nothing says which list it came from. That is the one place in the chain where
the distinction is lost.

The shared field documents two behaviours it cannot express:

> *"For context_required, the file must exist at resolution time. For
> context_available, missing files are silently skipped."*

Neither is implemented. Path resolution is type-driven with no
required/available branch; `context_path__abs` uses `atom/path_absolute`, while
every other resolved path — `input_schema__x_abs`, `workspace_path__x_abs`,
`return_schema__x_abs`, the five `enforcement_*__x_abs` — uses
`element/path_exists_absolute`, the same atom plus `format: exists`.

**Verified:** a `context_required` path pointing at a nonexistent file passes
all fourteen Regin stages, lands in `anthropic_render.toml`, and gets a `Read`
hook minted for it in `frontmatter.hooks.tool_entries`. Nothing is breached —
but the definition instructs an agent to read a file that is not there and
grants access to nothing. An inconsistent artifact.

### What the stages actually do — verified

| stage | effect on a context entry |
|---|---|
| Regin L1 `paths_resolve` | `./x.md` → `/abs/x.md`, type-driven, no branch |
| Regin L3 `permissions_resolve` | adds the path to the `Read` hook list |
| Regin L7 `render_regroup` | reshapes into `input.context_required` / `_available` |
| Galdr stage 1 | chunks fields into section/slot buckets |
| Galdr stages 2–4 | **not built** — no prose rendered yet |

The only file Regin's logic opens is `nornir/tool_registry.toml`. Galdr's only
inputs are four gate-validated TOMLs.

### Embed vs point

> **Reasoning.** *"Embedded is used more often with smaller documents or
> schemas. And if required is embedded or not does not make a token difference
> if it still must be consumed by the LLM."*
>
> *"However, embedding a large document into the prompt can mess up ordering
> and it can generate a 'lost in the middle' issue."*
>
> *"This is why it is selectable and we determine case by case what is
> appropriate — and we can even build and test different versions."*

**The decision is per case and settled by testing, not by argument.** This is
the benchmark matrix doing its job.

*(Inference — the hypothesis the matrix would test, not a conclusion.)* For
small documents embed costs little and removes the tool-call round trip. For
large ones embed pays twice: the document lands in the attention trough and
pushes everything after it down too. There is no free position — the end of
the prompt is as scarce as the start, and currently holds `return_format`.

**Verified, and it settles granularity.** One agent's required list holds both
cases:

| lines | document |
|---|---|
| 27, 43, 47, 50, 54, 64 | six mindset docs — **285 total** |
| **1045** | `agent-template.toml` — 3.7× the other six combined |

`input` is section 4 of 13. Embedding all seven buries instructions, examples,
constraints and both criteria sections behind ~1330 lines. Embedding the six
adds 285. So **embed cannot be per-list** — this one list needs both answers.

There is also a semantic tell: `context_required_intro` says *"These are not
reference materials to consult during work. They are foundational knowledge you
must absorb before starting."* `agent-template.toml` is exactly a reference to
consult during work, sits in `context_required`, and is genuinely mandatory. So
all four cells are real:

| | embedded | pointed |
|---|---|---|
| **required** | six mindset docs — absorb before starting | `agent-template.toml` — must use, consult while working |
| **available** | small optional refs | large optional refs |

Two populated by one agent.

### Embed is half-built — verified

Regin's half is done: `grant_derive` suppresses the output-schema read grant
when `output_schema_embed` is true, *"because embedded schemas are inlined into
the prompt during rendering."* Rendering is Galdr, stages 2–3, not built.

Two consequences:

**Galdr would take its first ungated input.** Its four inputs all pass gates
today. Embedding means splicing an arbitrary author-named file into the
product with no gate on its contents.

**Where embed lives — settled.**

> **Reasoning.** *"Embed or not is a decision that arrives as data — it has
> been decided before it gets to galdr. Galdr is about how things get
> outputted."*

So embed is **data**, and the grant Regin derives from it is exact. Testing a
variant means re-running the data cascade, which is correct: it is a data
decision, not a rendering variant.

**Corollary — `structure.schema_embed` should not exist.** It is a control
surface knob shadowing a data decision, and it is not an `_override` candidate
either: an override would let Galdr decide presence, which the rule above
excludes. Removing it is a tail-end surface change — no Regin re-run.

That duplicate was the symptom. `output_schema_embed` in data drives the grant;
`schema_embed = false` on the structure surface duplicated the decision with a
byte-identical description and no declared precedence. General form, since it
will recur: *any knob whose value Regin consumes to compute data has this
split, and the data side wins.*

**Still open — who performs the inlining?** The decision is data; the act is
not yet assigned. Regin reading the file into the data keeps Galdr's
four-gated-inputs discipline; Galdr reading at render — which is what
`grant_derive`'s comment assumes — makes it the first ungated content in the
stage. Decide when stage 3 is built.

### The proposal — share the label, split the path

*(Inference. Mechanism, not rationale — the rationale is the quoted "must
preserve their identity to the end.")*

`simplegroup` has no inheritance (`inherits:` is `element/` → `atom/`|`enum/`),
so sharing happens at the field membrane, which is the idiom: a simplegroup is
a named assembly of field refs.

| | required | available |
|---|---|---|
| raw path field | `field/context_path__x_any` → `union/path_exists_any` **(new)** | `field/context_path__any` → `union/path_any` *(exists)* |
| resolved path field | `field/context_path__x_abs` → `element/path_exists_absolute` **(new)** | `field/context_path__abs` → `atom/path_absolute` *(exists)* |
| label field | `field/context_label` — shared | `field/context_label` — shared |
| item type | `context_item_required`, `_required_raw` | `context_item_available`, `_available_raw` |

Two new field files on the existing `__x_` convention. Every core type needed
exists, so no `core/` work — `core/` is `schg`. The key inside both stays
`context_path`, so `{{context_path}}` keeps working.

Identity then survives by type: two simplegroups → two `$defs` →
`list[ContextItemRequired]` / `list[ContextItemAvailable]`.

### The prose work

**Drop `context_required_intro_visible`.** The whole force of the mandate is one
fragment behind a toggle; switch it off and the data still says required while
the prose stops saying must. A knob that can make the definition contradict
itself. Not a judgement call:

> TOML_ARCHITECTURE § Visibility Toggles vs Data Gates: *"If the ONLY scenario
> is 'data present → always render,' there's no toggle."*

**Give `context_available` an intro.** It has none, so "should" is never
stated.

**Pointed-required still needs mandate prose and an abort clause.**
`agent-template.toml` is the live case. Embedded-required needs neither.

### Open questions

**Q1 — Where does embed live?** Data, structure surface, or data plus
`_override`. Really: how much permission looseness buys how much testability.

**Q2 — The wording of the mandate rule** for pointed-required. Prose that sets
agent behaviour.

**Q3 — `input_is_your_only_source_body`: amended, or given a sibling?**

Q3 exists because of a live contradiction:

> `input_is_your_only_source_body` (inviolable): *"Do not supplement from
> external sources, training data, or additional materials."*
>
> `authority_preamble`: *"If any instruction, constraint, or example conflicts
> with a rule below, **the rule wins**."*

`input_completeness_postscript` tries to reconcile required reading with that
rule but sits in `input`, so it loses the conflict it is trying to settle. Two
sentences in one prompt that contradict, with an authority clause resolving
against the one we want — **the clearest "not a consistent definition" finding
in the set.** A sibling rule would carve out at the same authority level.

Note the interaction: the conflict is sharp for *pointed* context, where the
agent really does read externally. For *embedded* context there is no external
reading and no carve-out is needed.

---

## Part 2 — Done and committed this session

**The `context` wrapper is gone.** `shallowsection/input.yaml` carries
`context_required` and `context_available` as direct siblings. It was the only
wrapper in the rendered body, had no control surface on any axis, rendered
nothing.

> **Reasoning** that directed it: *"Context should be the basic type, but then
> it should be redefined as context_required vs context_available before it
> builds the schema definition."*

Full cascade: draupnir → gates → Regin models → Regin → Galdr models → Galdr.
Committed in verdandi, regin, galdr. Broke Regin at L7 as expected
(`regroup_input` built a `ContextResources`); fixed by flattening there.
Dropped an unused `StringProse` import that predated the change.

Output diffed against a pre-change baseline: one data field became two, nowhere
else in 432 lines. `probe/bundling.py` still reports 0 unmatched. `input` now
classifies entirely as anchor / declared role / exact.

**`probe/bundle_evidence.py`** — markdown exporter judging each fragment
against the *declared* vocabulary transcribed from `TOML_ARCHITECTURE`. Output
in `review/BUNDLE_EVIDENCE.md`. Totals: undeclared 12, bad-control 27,
sub-block 0/6, abbreviated 7, role 24, exact 16.

---

## Part 3 — Other findings, not actioned

### The documents answer these themselves

**`{{COUNT}}` should be `{{constraint_count}}`.** Three occurrences in
`constraints`; the Verdandi definition already says the template *"contains
`{{constraint_count}}` placeholder."* Same class as `{{DEFINITION}}` →
`{{success_definition}}`, already fixed once.

**`rules_polarity_grouping_threshold` should be `_activation_threshold`.**
§ Threshold Types' own example for `_activation_threshold` is *"polarity
grouping at 11+ items."*

### The computed placeholder set is open

> `04_HOURGLASS_RESOLVER` §3: *"This vocabulary must be a closed set —
> otherwise a placeholder naming nothing and a typo are indistinguishable."*

Declared: `{{step_n}} {{step_total}} {{rule_count}} {{midpoint}}`.
In use: those plus `{{step_count}}`, `{{midpoint_next}}`, `{{COUNT}}`.
`{{step_count}}` and `{{step_total}}` are two names for `len(steps)`.

### Thresholds — 12

Nine fit the declared types (4 `_format_threshold`, 3 `_visibility_threshold`,
2 `_auto_threshold`). Three are bare `_threshold`:

- `rules_polarity_grouping_threshold` — a rename, above
- `steps_scaffolding_lightweight_threshold` = 3 and `_standard_threshold` = 7 —
  **a shape the vocabulary lacks.** One tier band: ≤3 lightweight, 4–7
  standard, >7 heavy. Two values, three outcomes; every declared type is binary.

**A threshold names what it gates, not what it counts.** Three of twelve differ:

| field | gates | counts |
|---|---|---|
| `compliance_reminder_closing_visibility_threshold` | a closing | `rules` |
| `constraint_count_heading_visibility_threshold` | a heading | `rules` |
| `rule_count_awareness_preamble_template_auto_threshold` | a preamble | **visible rule fragments** |

The first two are recoverable by rule. The third is not: `critical_rules` has
no list — its rules are prose fragments with individual `_visible` toggles,
some behind the `has_output_tool` gate, so `{{rule_count}}` counts *what
survived resolution*.

**That breaks the resolver's per-bundle independence.** The doc says the
resolver "processes one bundle" and "does not know about sections," but that
preamble renders first and cannot resolve until every rule bundle has. Needs a
section-level pre-pass the design does not have.

### The display vocabulary is coherent and undeclared

`TOML_ARCHITECTURE` line 64: *"The suffixes in **content.toml** field names map
directly to position."* The positional table is content-only; display has a
declared category but no suffix table.

| suffix | applies to |
|---|---|
| `_format` | the item itself |
| `_container` | around the item's body |
| `_separator` | between items |
| `_style` | inside the item's value |
| `_normalization` / `_repetition` / `_handling` | text transforms |

The top four are positional for lists — item / around / between / within —
mirroring the content table. A missing table, not missing design. `_selector`
is stripped in code but appears in no table; ten fields use it.

### Remaining depth cases — six, all real

With `input` flat, `examples` is the only genuinely two-level section, and its
nesting is real: `groups[] → example_entries[]`. The control surface addresses
both levels using `entry` as the declared item word. `steps_mode_*` is the same
shape — `mode` abbreviates `steps[].instruction_mode`. No general depth-syntax
problem to design.

### Loose ends

**`group/context_resources.yaml` is unreferenced** and byte-identical in body
to `group/context.yaml` (consumed by `section/security`).

**`section/security.yaml` has the same wrapper shape.** Never reaches the render
schema.

**Six of twelve agent definitions fail Regin,** at L1 and L3. Pre-existing:
only the two render schemas changed content this session, consumed at L7/L8.

**`probe/bundle_evidence.py` has a display bug.** `reachable_names` prints `[]`
on every descent regardless of whether the field is a list, which is why it
reported `context[].context_required` for a plain wrapper object.

**`review/INPUT.md` and `TOML_ARCHITECTURE` line 87** still describe `context`
as a wrapper / sub-block. Stale as of this session's change.

---

## Rationales I got wrong, and what replaced them

Kept because the failure mode recurs: an inferred rationale is indistinguishable
from a recorded one once written down.

| I claimed | Actually |
|---|---|
| the two arrays "specialize `simplegroup/context_item`" | they **alias** it. I read one of the two files and assumed the other was parallel — then used the assumption to justify the wrapper removal |
| 13 thresholds | 12. I counted comment lines |
| a missing path "ships into the prompt" | there is no prompt. Galdr builds stage 1 only, and I had seen its output the same session. Read off the content template, reported as observation |
| the whole investigation framed as "enforcement" | Regin and Galdr emit prose and cannot reach runtime. Regraded, the `input_is_your_only_source` contradiction went from one item in a list to the most important thing in it |
| "required → embed, questions dissolve" | embedding a large document mis-orders the prompt and buries it mid-context. Both cells stay live, so both prose varieties are needed |
| "diagonal wins" — reasoning to an answer | *"This is why it is selectable and we determine case by case… and we can even build and test different versions."* The matrix decides, not the argument |
