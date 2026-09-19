# Galdr — The Challenges

[[AGENT_BUILD_SYSTEM|↑ the map]] · companion to [[GALDR_ELEMENT]] — read that first.

**Status: volatile.** Unlike [[GALDR_ELEMENT]], which describes design that should hold,
this document names specific field-level findings in the current tree. It will go stale.
Every claim below cites a location — verify against the tree before acting on any of it.

Read [[GALDR_ELEMENT]] first. This document assumes the four axes, the slot vocabulary,
the trunk correspondence rule, and the hourglass.

---

## How to read this

**Only stage 1 of the engine exists.** `compose_section` sorts fields into slots and
extracts `pre_*` state; gather, resolve/render and buffer join are unbuilt, and the
walker-based predecessor has been deleted. Galdr does not currently render anything.

That fact governs how the sections below must be read, and getting it wrong is expensive:

> **Sections C, D and E are requirements, not defects.** They record what the waist will
> have to handle — per-item interpolation, nested traversal, count-driven switching, and so
> on. They are the output of stage 1 doing its job, which is to discover what a bundle
> actually contains before anyone commits to a model for it.
>
> **Do not treat them as a bug list.** Fixing an unbuilt engine one symptom at a time means
> building stages 2–4 as a series of patches, each shaped by whichever section prompted it.
> That is per-section code arriving by the back door — the approach scrapped twice — and it
> is the most convincing form of whack-a-mole, because it comes with a checklist.
>
> **Sections A, B, F and G are different.** Those describe things wrong in the tree *now*:
> a rename left half-finished, controls whose type cannot express the choice asked of them,
> verification that does not verify, and an upstream contract nobody enforces. Those are
> actionable today.

An earlier reading of this document found it incoherent. The prose was not the problem —
the frame was. A list of render failures, written about an engine that does not render,
describes everything and therefore locates nothing.

---

## The shape of the problem

Galdr's three control surfaces describe an engine richer than the one that exists. But
the gap is not one gap. It is four different kinds of gap, and they interlock:

```
a fragment renders correctly only when ALL of these line up

  data field exists           →  or there is nothing to say
  content template on the
    matching trunk            →  or the words attach to nothing
  structure toggle of a type
    that can express the      →  or the choice cannot be stated
    choice being asked
  display format, if it is
    a list                    →  or it renders in a default shape
  an engine mechanism for
    its data shape            →  or none of the above executes
```

Repair one layer alone and nothing moves. Rename a field without the mechanism and it
still renders nothing; build the mechanism without the rename and it wires to nothing.
**This is why it is not a position tweak** — and why past sessions that fixed one naming
aspect at a time each declared success and left the other three broken.

---

## Design rules the rest of this document assumes

Each of these rests on something specific, stated with it. Any can be challenged; none is a
stamp.

> **Data is the source of truth for names.** When a control surface disagrees with a data
> field's name, the *surface* is renamed. The data model is never bent to fit — because the
> data is the invariant across every variant of an agent, and the surfaces are the knobs.

> **Structure says WHICH, Display says WHAT COUNT.** A threshold living in `display.toml`
> beside a toggle in `structure.toml` is not entanglement. Structure names the choice;
> Display names the count that triggers automatic behaviour. Checked and struck as *"NOT A
> MISMATCH"* during the naming work.

> **The engine is generic.** No per-section functions, no per-section registry. Attempted
> twice — once as a class hierarchy, once as per-section composers — and scrapped both times,
> because section knowledge in Python is agent behaviour that nothing can version.

> **The orphaned walker is deleted.** It was retained for a period as non-normative
> reference; the code was then removed, along with `markdown_render/`,
> `template_interpolate/` and `data_unwrap/`, which nothing else used. Stage 1 is what
> remains. Restoring it from git to consult defeats the reason it was removed — code you know
> is wrong still pulls you toward it.

> **`role_responsibility` stays scalar.** An earlier plan recorded the opposite; the field
> definition forbids the conversion and that plan is void. A1 records why the reasoning
> failed, which is the part worth keeping.

---

## A. The rename cascade stopped mid-flight

The naming plan defined two cascades. Cascade A landed and was verified end to end (models
regenerate byte-identically; all three TOMLs pass their gates). Cascade B never ran. The
plan itself has been deleted along with the rest of `archive/` — what it decided is recorded
above, and what it got wrong is recorded in A1.

### A1 — `role_responsibility` scalar→list: CLOSED, superseded

The plan's entry for this is void. The field definition forbids the conversion, and
`e0cb1e1` was right.

Worth keeping the shape of the error, because it is repeatable. The plan justified the
change with *"Current usage confirms agents can have multiple responsibility statements."*
That is true of the data and irrelevant to the decision: the data was **violating the
field's contract**, and the plan read the violation as a requirement. A plan records an
intention; a field definition records the contract. When they disagree, the field
definition wins.

Cascade B therefore has no remaining work. Every data-model change from that era is either
done or void, and **no item in this document now requires a data-schema cascade.**

**Two different cascades, and the document previously conflated them.** Say which you mean:

> **Data-schema cascade** (`agent-builder`) — Verdandi → Draupnir → rebuild gates → **re-run
> Regin** → Galdr. Invalidates every stored intermediate and re-derives data for all agent
> definitions. Wide blast radius. This is what "cascade" means above.
>
> **Surface-schema regeneration** (`agent-output`) — edit YAML → `draupnir --project
> agent-output` → rebuild the three output gates → `generate_structures.py` → re-run Galdr.
> Mechanical, tail-end, no Regin, no effect on any definition.

B1 and E2 need the second, not the first. Both are cheap; neither is free. The misreading has
teeth — taken as "no regeneration," B1 looks like a TOML edit, and the gate rejects `"auto"`
where a Boolean is declared, because the gate embeds the schema it was built with.

### A2 — Groups that landed without achieving the plan's own goal

The plan exists so trunks correspond mechanically. A group was renamed but not onto a
matching trunk:

```
examples       data       ExampleEntry.example_heading
               content    example_heading_template           trunk  example_heading       ✓
               display    groups_entry_heading_format        trunk  groups_entry_heading  ✗
```

The display axis settled on a trunk that exists on no other axis. It sits inside a group the
plan treats as addressed, and it is not catchable by gate validation — a gate checks a file's
shape, never cross-axis agreement.

The instructions group had the same shape — content and structure on
`instruction_mode_recap`, display on `steps_mode_recap` — and is gone. The content and
structure fields were deleted along with `{{mode_recap_text}}`, the placeholder that named no
data field. `steps_mode_recap_format` survives in the display surface with nothing on any
other axis, so what was a mismatch is now an orphan.

---

## B. Controls that are one state short

### B1 — The visibility control cannot express "defer to the count"

Four different shapes are in use for "should this render":

```
SHAPE 1   Boolean alone                                     ~40 fields
          X_visible = true

SHAPE 2   VisibilityMode + threshold, BOTH in structure      2 fields
          critical_rules  rule_count_awareness_preamble_visible = "auto"
                          rule_count_awareness_preamble_template_auto_threshold = 5
          input           parameters_heading_visible = "auto"
                          parameters_heading_auto_threshold = 2

SHAPE 3   Boolean in structure + threshold in DISPLAY        3 fields
          security_boundary  filesystem_permissions_label_visible = true
                     display filesystem_permissions_label_visibility_threshold = 4
          constraints        compliance_reminder_closing_visible = true
                     display compliance_reminder_closing_visibility_threshold = 6
          constraints        constraint_count_heading_visible = true
                     display constraint_count_heading_visibility_threshold = 6

SHAPE 4   VisibilityMode, no threshold — key from a data condition   1 field
          instructions  instruction_mode_explanation_preamble_visible = "auto"
                        ("auto" = render when step modes are mixed)
```

**Measure shapes 2 and 3 against the decided rule and neither is correct.**

Shape 3 has the right *placement* — Boolean choice in structure, count in display, exactly
as Group 6 requires — and the wrong *type*. A Boolean has two states. It has already
answered `true`, so there is no value that means *"I am not answering; count the list."*
The threshold sitting in the other file assumes a question that was never left open.

Shape 2 has the right *type* — `VisibilityMode` is `"auto" | "always" | "never"`, and
`"auto"` is precisely the deferral Shape 3 cannot express — and the wrong *placement*: it
puts the count in structure, which Group 6 assigns to display.

The rule-consistent shape is `VisibilityMode` in structure paired with a threshold in
display. **It exists nowhere in the tree.** Every instance is half right, and the two
halves are split across two different groups of fields.

### B2 — A meta-control that sets other controls

`pre_scaffolding_tier_override` (structure, `"auto"`) combined with
`steps_scaffolding_lightweight_threshold = 3` and `steps_scaffolding_standard_threshold = 7`
(display) selects a *tier*, and the tier then determines a set of individual visibility
toggles.

Group 6 rules the naming and placement correct. The difficulty is architectural, not
nominal: `review/INSTRUCTIONS.md` ISSUE 2 notes it is "not directly processable by the
generic engine" and would need a preprocessing pass that resolves a tier into concrete
toggle values before the engine runs. One control writing many others sits awkwardly beside
"a bundle carries values, not verdicts."

---

## C. What the waist must handle

**This is a requirements catalogue, not a bug list.** Each item recurs across sections, so
each is **one** mechanism to design into stages 2–4 — not N separate defects. That is the
single most useful thing to know before estimating any of it, and the reason to read them
together rather than one at a time.

Nothing here is broken. None of it is built.

### C1 — Per-item interpolation

Templates whose placeholders resolve from *list-item* fields rather than section-level data.
Interpolation as designed fills from a section-wide dict; these require a per-item pass.

```
input             parameters_entry_template          {{param_name}} {{param_type}} {{param_description}}
input             context_required_entry_template    {{context_label}} {{context_path}}
examples          example_heading_template           {{example_heading}}
examples          group_framing_preamble_template    {{example_group_name}}   (also slot-misplaced, see E)
security_boundary compound_entry_template            {{PATH}} {{TOOLS}}
success_criteria  definition_declaration_variant_template, evidence_intro_variant,
                  definition_to_evidence_transition_variant     — per criteria item
failure_criteria  abort_stance_definition_label_variant         — per failure item
```

### C2 — Nested BaseModel traversal

`input.context` is a `ContextResources` wrapper holding two `RootModel[list[ContextItem]]`.
The wrapper and the RootModel lists are walkable; each `ContextItem` is a nested BaseModel
with `context_label` + `context_path`, and the unwrap handles only scalars and RootModels
wrapping scalars. So the waist needs a traversal that descends into a nested BaseModel and
addresses its fields — without which `context_required_heading` and
`context_required_intro` have nothing to attach to.

`review/INPUT.md` ISSUE 1 offers the alternative — redefine `ContextItem` as
`RootModel[str]` holding a pre-formatted string — and correctly notes that moves formatting
into the data axis, which the four-axis rule forbids. Reshaping the schema is normally the
right move over complicating the engine; here it is not, because the reshape would be a
formatting decision stored as data.

### C3 — Integer RootModel unwrap

`critical_rules.batch_size` is `OutputToolBatchSize`, a `RootModel[Integer]`. A scalar
unwrap covering only `RootModel[str]` will not reach it, so `{{batch_size}}` needs the
unwrap to be type-general across RootModel-wrapped scalars rather than string-specific.

*(Note there are three distinct `batch_size` fields in the data model. `Dispatcher.batch_size`
is a `DispatchBatchSize` tuple — a different shape and not this item.)*

### C4 — Count-driven conditionals

Every `_threshold` field requires counting a list at render time and switching on the
result. This is the mechanism the three Shape-3 thresholds in B1 are waiting on — their
placement problem and this missing mechanism are independent, and both must land before any
of them does anything.

### C5 — Variant selection from a data condition, with no selector

Three places pick a variant from the data rather than from a structure `_selector`:

```
instructions   instruction_mode_explanation_preamble_variant   key = which modes appear in steps
output         name_known                                      should pick name_template / name_instruction / neither
return_format  mode                                            should pick tokens_two vs tokens_three
```

### C6 — Cross-section conditionality

`writing_output` should render only when `critical_rules.has_output_tool` is true. No
mechanism exists for one section to consult another — and by design, sections resolve
without reaching outside themselves. This is the one requirement that argues against that
invariant, and it deserves a decision rather than a workaround.

### C7 — Section-level skip and truncation

`pre_section_visible` (constraints, anti_patterns, success_criteria, failure_criteria) and
`pre_max_entries_rendered` are extracted by stage 1 into typed state, and nothing consumes
that state yet. Both are section-level decisions and belong **above** the per-section
engine, in orchestrate — the one item here that is not waist work.

---

## D. Data fields no content field names

Seventeen data fields have no content field on their trunk, so as things stand there is no
route by which their values could reach a page:

```
identity         role_description
critical_rules   name_needed
output           output_file · name_template · name_instruction · name_known
writing_output   invocation_display · name_needed · name_pattern · batch_size
                 schema_path · file_path · directory_path
return_format    return_schema · status_instruction · metrics_instruction · output_instruction
```

Three of these are, by their own sections' reviews, the most important content in the
section:

> **`return_format.status_instruction`** — what this specific agent must actually return.
> **`writing_output.invocation_display`** — the literal tool-call block to copy.
> **`output.name_instruction`** — where and under what name output goes.

These are the per-agent payload. An agent prompt without them is generic scaffolding.

**This is one design question, not seventeen gaps.** Several of these fields are
already-formatted prose that needs no template at all, which points at a **passthrough**
content mechanism — a way to say *render this data field as-is*. That would be a new kind of
content field, and deciding whether it should exist is the item here. Adding seventeen
templates to name seventeen trunks is the alternative, and it is worse: it would put wording
around content that already carries its own.

---

## E. Ambiguities with no detector

### E1 — Standalone content and a mistyped trunk are the same thing

Content whose trunk matches no data field renders after the data as standalone. A typo in a
trunk also matches no data field. The engine cannot distinguish intent from error; both are
simply content that matched nothing.

This is structural, not a bug to fix, and it is the reason naming discipline is
load-bearing. The only detector is a probe that counts unmatched fields — the count is the
signal, and it must be read by a person.

### E2 — Two mutually exclusive fields in one slot

`return_format` holds `token_must_be_first_word_tokens_three_preamble` and
`token_must_be_first_word_tokens_two_preamble` (`extracted/content.toml`, lines 159–160).
Both carry `_preamble`, so both land in the same slot, and nothing selects between them —
which means the waist would emit both. `review/RETURN_FORMAT.md` ISSUE 3 names the two
candidate resolutions: per-field visibility toggles, or merge into one `_preamble_variant`
table keyed on `mode`. The second is consistent with how every other variant works, and it
does not wait on the engine.

It is **not** a TOML-only edit, though — all the fields involved are schema-declared, so this
needs the surface-schema regeneration described in A1. (The review sheet names two siblings;
the model carries a third. Check the generated model, not the sheet.)

### E3 — `title` may reach two slots

`identity.title` is consumed by `section_start_template` (`"AGENT: {{title}}"`) and is also
a scalar body field. `review/IDENTITY.md` ISSUE 2 flags it as needing verification.

**Not verifiable today** — it is a question about render output, and there is no render.
What stage 1 *can* answer is whether `title` appears in two slots in the inspection report;
that is the check to run, and it is not the same question. Recorded so it is not lost, not
as a confirmed defect.

---

## F. What verification does and does not catch

> **Gate validation checks shape, not correspondence.** All three control-surface TOMLs
> pass their gates today, with both A2 trunk mismatches present. A gate validates one file
> against one schema; nothing validates that a trunk in `display.toml` names something that
> exists in the data model.

> **The plan's model-freshness check is broken as written.** It says run
> `generate_structures.py` and confirm the models regenerate. But the generator stamps a
> fresh `# timestamp:` into every file header, so `git status` reports all four generated
> models dirty on every run regardless. As a staleness check it returns a false positive
> every time; the models must be **diffed**, not statused. (Verified: regenerating today
> produced a one-line timestamp change per file and nothing else.)

The gap those two leave is the same gap: **cross-axis correspondence is checked by nobody.**
The probes in `probe/` and the per-section sheets in `review/` are the only instruments, and
both require a person to read them.

---

## G. Upstream — found here, not Galdr's to fix

Surfaced while closing A1. Recorded so it is not lost, and flagged so nobody attempts a
repair inside Galdr, where it does not belong.

**Six of eleven agent definitions violate `role_responsibility`'s stated contract.** The
field requires a single mandate and names "multiple obligations joined by 'and'" as an
`error`-severity anti-pattern. These enumerate three to seven:

```
agent-builder (7)   agent-deconstructor (6)   agent-improver (6)
agent-preparer (5)  agent-auditor (4+)        agent-quality-auditor (3)
```

All six are agent-pipeline meta-agents, likely authored in one pass. The five conforming
definitions include `truth-system-quality-control`, whose value is the field description's
own worked example almost verbatim.

**Why nothing catches it.** `min_length: 30` is the field's only *structural* constraint.
"One-sentence mandate, not a list of duties" lives in the `semantic:` block — guidance an
LLM auditor can apply, not something a compiled gate can check. So definitions carrying an
`error`-severity anti-pattern validate cleanly through every gate in the pipeline and render
into finished prompts.

This is the same failure shape as A2 and F: **a rule that exists, is correct, and is
enforced by nobody.** It sits in Verdandi and the agent definitions, upstream of Regin.
Nothing Galdr does causes it; Galdr would carry it faithfully through.

### Correction — this is not the gap it looks like

An earlier revision of this document grouped G with A2, F and a Draupnir defect as one class:
*"a rule that exists, is correct, and is enforced by nobody."* **That reading was wrong about
G, and the error is worth keeping visible because it is easy to repeat.**

`semantic:` blocks compile to `x-semantic` in the output schema, carrying `intent`,
`severity`, `checks` and `anti_patterns`. An `x-` key is ignored by every JSON Schema
validator by definition — so it looks like a rule falling into a hole.

It is not. It is a **payload addressed to a different enforcement layer.** From
`agent-quality-auditor`'s own definition:

> *"Schema validity and field correctness are already enforced by the pipeline — your concern
> is the qualitative dimension that no schema can capture."*

The architecture is deliberately two-layered: structural constraints go to compiled gates,
semantic constraints go to an auditor agent, and `x-semantic`'s `checks` array is that
agent's checklist. G is therefore **a designed layer that is not yet operational**, not an
architectural oversight — and it is blocked on precisely what this pipeline exists to
unblock, since a semantic auditor is exactly the kind of agent you cannot trust until you
can build agents you can trust.

The `role_responsibility` observation still stands as an observation. What does not stand is
calling it an enforcement gap.

### What the genuine instances are

With G removed, three remain, and they are not all the same thing:

> **A2 — detected, not enforced.** `probe/slots_trunk_match.py` finds orphaned trunks. No
> gate does, and nothing runs the probe automatically. The instrument exists; the loop
> around it does not.
>
> **F — a check that cannot fail.** Self-defeating rather than absent. See F.
>
> **Draupnir's conditional predicates — genuinely unenforced.** The `field:` in a `when`
> clause is carried as an opaque string and never resolved as an edge, so a mistyped target
> fails open silently. One such typo exists today. See `TODO.md` in the Verdandi repository.

Three findings, three different shapes: no enforcement loop, a broken instrument, and a
missing resolution step. Treating them as one pattern was tidier than the evidence supported.

---

## Where to verify any of this

```
review/{SECTION}.md      per-section four-axis interleave — data, content, structure,
                         display side by side, plus render order and known issues
review/BUNDLE_INSPECTION.md   bundle snapshot
extracted/*.toml         the live control surfaces
src/galdr/structure/gen/ the generated models — authoritative field inventory
probe/*.py               inspection scripts; unmatched-trunk counting
redesign/*.md            the current design — FOUR_AXIS_SPEC, the hourglass, trunk
                         matching, the naming law
```

`archive/` no longer exists. It held the rename plan, nine audit iterations and thirty
superseded section analyses, and it was deleted deliberately: everything worth keeping from
it is recorded above, and everything else was a set of pre-rename field names that no
warning label could stop from steering a reader. Do not restore it from git to consult.

Current implementation status is not recorded here or anywhere. Read it from the code.
