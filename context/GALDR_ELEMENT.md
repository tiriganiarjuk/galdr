# Galdr — The Composition Engine

[[AGENT_BUILD_SYSTEM|↑ the map]] · [[VERDANDI_ELEMENT|Verdandi]] → [[DRAUPNIR_ELEMENT|Draupnir]] → [[NORNIR_GATES_ELEMENT|Nornir gates]] → [[REGIN_ELEMENT|Regin]] → **Galdr**

## What it is

The last stage. Galdr takes one frozen, gate-validated data model and combines it with
three swappable control surfaces to produce an agent prompt.

```bash
uv run galdr <anthropic_render.toml>
#  --content / --structure / --display   paths to the three surface files
#  -o                                    output path
```

Regin answered *what is this agent*. Galdr answers *how does it read*. Running it many
times with different surfaces over the same data is what produces the benchmark matrix
— that loop is currently driven from outside Galdr; there is no sweep mode.

---

## What exists today

**Read this before anything below it.** The rest of this document describes the engine as
designed. Most of that engine is not built, and the unbuilt parts are not individually
signposted.

**Stage 1 exists.** `compose_section` calls exactly two functions —
`extract_preprocessing_fields` and `sort_into_slots` — and a run writes a file headed
`# Stage 1 Slot Inspection`: per section, the `pre_*` fields extracted, then each of the
four slots listing which axis contributed which field name.

**Stages 2, 3 and 4 do not.** Gather, resolve/render and buffer join are unimplemented. A
walker-based predecessor once did that work; it was disconnected, then deleted. So **Galdr
does not currently produce an agent prompt.** It answers *where does every field land?*

That is the designed order of work, not a stall — see "Why stage 1 comes first" below.

Eight functions hold up everything that runs: `compose_section`, `sort_into_slots`,
`extract_preprocessing_fields`, `place_structure_field`, `classify_content_slot`,
`place_display_fields_into_slots`, plus the suffix predicates in `primitive.py`. If you are
looking for more engine than that, there isn't any.

---

## The four axes

| Axis | File | Answers |
|---|---|---|
| **Data** | `anthropic_render.toml` | what to say |
| **Structure** | `structure.toml` | what to include |
| **Content** | `content.toml` | how to word it |
| **Display** | `display.toml` | how to format it |

Galdr does no reshaping. The generated Pydantic model of the data is the authoritative
field inventory — read it rather than working from a remembered list.

**On entanglement.** Axes share a *vocabulary* and that is correct. `structure.toml`
sets `framing_selector = "territory"`; `content.toml` defines a table whose keys include
`territory`. Both name the same word; neither holds the other's data. Swap the content
file and the same selector picks different prose — the design working.

What is fatal is an axis holding another axis's **data**: a heading string in the data
model, an ordering choice in the content file. Then you cannot vary one without editing
another, and the matrix dimension is gone.

Ownership, stated positively:

| Axis | Owns | Marked by |
|---|---|---|
| **Data** | the values, and the names the other three align to | (from Regin) |
| **Structure** | the *choice* — renders or not, which variant | `_visible`, `_selector` |
| **Display** | visual form, and the counts driving automatic switching | `_format`, `_format_threshold` |
| **Content** | the words | `_template`, `_label`, prose |

**Data is the source of truth for names.** Where another axis disagrees with a data
field's name, the axis gets renamed — never the data. And a threshold living in Display
is not Structure leaking: Structure says *which*, Display says *what count* triggers
automatic behaviour.

**The test that decides where a field belongs is invariance.** The four labels above
describe the files; they do not tell you where a field you have never seen goes. The rule
that does: the actual data point, *the thing that stays invariant across every variant of
this agent*, is data — whether it is shown, how it is worded, how it is formatted, what
order it comes in are knobs. That is why "a heading string in the data model" is wrong in
terms you can act on: a heading can change while the agent stays the same agent, so it is
not invariant, so it is not data.

**And the knobs are enums.** `heading_format`, `list_format`, `inline_separator`,
`separator_style`, every `*_variant_key` — closed value sets defined in Verdandi's `core/`,
which is immutable. Sweeping ten knobs across all their combinations is a finite,
enumerable job only because each draws from a closed set instead of being free text. The
benchmark matrix is computable because of a decision made three stages upstream.

---

## How field names work

This is the mechanism. Everything else follows from it.

### Slot classification — three suffixes and a fallthrough

Every content field lands in one of four buffer slots. The engine checks exactly three
suffixes, after stripping the modifiers `_template` and `_variant`:

```
name ends in  _start      → heading slot
name ends in  _preamble   → preamble slot
name ends in  _closing    → closing slot
anything else             → body slot
```

That is the whole rule. `_postscript`, `_label`, `_heading`, `_declaration`,
`_transition`, `_intro`, `_separator`, `_entry_template`, `_body` **all fall through to
body** — they are not slot names. They are *body positioning* suffixes: within the body,
they determine where a fragment sits relative to the data field it decorates.

Two different vocabularies, easily conflated:

| Purpose | Suffixes |
|---|---|
| Choose the slot | `_start`, `_preamble`, `_closing` |
| Position within the body | `_transition`, `_label`, `_declaration`, `_intro`, `_postscript`, `_separator`, `_heading`, `_entry_template`, `_body` |

`_start` was chosen for the section heading rather than `_heading` because `_heading`
collides — `parameters_heading` and `context_required_heading` are body sub-headings.
Nothing else in the vocabulary ends in `_start`, so one `endswith` is unambiguous and
order-independent.

### Trunk matching — which data field a fragment decorates

Strip the axis's control suffixes and what remains is the **trunk**, which must match a
data field name:

```
structure controls   _auto_threshold, _visible, _selector, _override
display controls     _activation_threshold, _visibility_threshold,
                     _format_threshold, _format
modifiers            _template, _variant
```

Worked example:

```
role_identity_postscript_visible     a structure field
  strip _visible          → role_identity_postscript
  suffix is _postscript   → body slot, positioned after the data
  trunk role_identity     → decorates the data field role_identity
```

Once stripped, trunks must correspond across axes. This is the rule the whole naming
scheme exists to serve — the engine derives every cross-axis connection from it, with no
mapping table anywhere:

```
content    {trunk}_label            →  data       {trunk}
content    {trunk}_postscript       →  structure  {trunk}_postscript_visible
display    {trunk}_format           →  data       {trunk}          (the list it formats)
display    {trunk}_format_threshold →  pairs with {trunk}_format
structure  {field}_visible          →  content    {field}
```

A trunk that appears on one axis under a different name than on another is a silent
break: each file validates fine on its own, because a gate checks shape, not cross-axis
agreement. Nothing catches it but reading the four axes side by side.

### Placeholders — which data field fills a hole

```toml
role_identity_template = "You are a {{role_identity}}."
```

Interpolation is case-insensitive. Placeholder names draw from three sources, not one:

```
{{role_identity}}          a field of the section's data
{{success_definition}}     a field of the current list item — SuccessItem.success_definition
{{step_total}}             a value the engine computes — counts, indices, midpoints
```

So the interpolation dict is a scope chain, not a flat map of the section's values. What
that chain contains is part of what stage 1 is being used to work out.

**All three conventions operate at once.** A name can satisfy one and violate another —
correct suffix, trunk matching nothing — and the result renders in the right place
attached to nothing. Past audits each checked one convention and missed the others. When
you change a field name, check all three together.

### Fields the engine consumes before any of this

Names beginning `pre_` are preprocessing fields. They are read first and control
section-level behaviour — skipping a section, truncating a list, expanding a tier preset
— and never enter the bundling pipeline.

---

## The hourglass

```
   chunk        sort fields into slots by suffix
     │
   gather       collect everything affecting one output point into a bundle
     ▼
  ┌──────────── the narrow middle, identical for every bundle ────────────┐
  │  1. visible?        toggle value, threshold, or a data condition       │
  │  2. which variant?  selector value picks from the variant table        │
  │  3. interpolate     fill {{placeholders}} from the section's values    │
  │  4. what shape?     determines which renderer runs                     │
  └────────────────────────────────────────────────────────────────────────┘
     │
   render       route by data shape
     │
   buffer       join slots: heading, preamble, body, closing
```

By the middle, section identity is gone — it is just a bundle. That is what lets one
engine handle every section. Branching on data *shape* at step 4 is a closed vocabulary
of a few renderers; branching on *section* would be an open-ended list that grows every
time a section is added, which is the difference that matters.

A bundle carries **values, not verdicts**: the toggle's value rather than the decision,
the variant table plus the selector's value rather than the chosen string, the template
plus the interpolation dict rather than filled text. Keep resolution in one place.

**Body order comes from the data.** The data model's field declaration order is the
render order; content attaches to data fields, and content that matches no data field
renders afterward as standalone. Note the consequence: the engine **cannot distinguish
intentional standalone content from a mistyped trunk.** Both are simply content that
matched nothing. That is why naming discipline is load-bearing and why the repository
carries probe scripts that count unmatched fields — the count is the only detector.

### Suppress-on-incomplete

The designed mechanism for conditionality without conditional code: a template still
containing `{{...}}` after interpolation renders as nothing. An agent with no output
tool has no `tool_name`, so the rule mentioning it disappears — no gate logic anywhere.

> **Specified, not implemented — and not currently reachable either.** `interpolate`
> preserves unmatched placeholders verbatim rather than blanking the fragment, so the rule
> as written would not suppress. But interpolation is not running at all: every caller sits
> in the orphaned half of `composed.py`. Implementing suppress-on-incomplete is stage-3
> work, and stage 3 does not exist.
>
> The literal `{{tool_name}}` visible in `staging/` is **not** evidence of this. That file
> predates the walker's disconnection. Diagnosing from it leads to a bug that is not there —
> which has already happened once.

---

## Why it is built this way

### Why names carry the mechanism

Your training says explicit beats implicit. Here is the explicit alternative:

```toml
[identity.role_identity_postscript]
slot        = "body"
after       = "role_identity"
visible     = true
text        = "..."
```

Three things break.

> **It entangles the axes.** That table mixes content (`text`), structure (`visible`),
> and placement. Split across the three files as required and each must repeat the
> placement — or one file owns it and the others defer, making content depend on
> structure.
>
> **It adds a second source of truth.** You still need a key to identify the table, so
> placement is now declared twice and the two can disagree.
>
> **The name instructs the author.** An LLM writing `content.toml` pattern-matches on the
> field name. Seeing `_postscript`, it writes prose that refers back to what came before.
> A `slot = "body"` value is data the author sets, not a signal the author reads.

The general principle, which is the load-bearing one:

**An LLM authoring input will not reach for the manual. It will wing it from the field
names. So the names are built so that winging it produces reasonable input.**

Documentation is opt-in; names are mandatory. The names are not documentation *about*
the mechanism — they are the mechanism, on both the machine side and the author side.

Note what this does *not* buy: it does not make drift impossible. A mistyped trunk is
perfectly representable and fails silently. What it buys is that the most likely
guess is the correct one, and that there is exactly one place to check.

### Why the engine is generic — and why an hourglass specifically

Section-specific knowledge in Python would mean an agent's behaviour partly lives in code,
and the whole product requires that an agent be fully specified by versioned files. A
`compose_identity()` would encode "identity's title goes in the heading" — a structure
decision sitting where nothing can version it. Attempted twice, once as a class hierarchy
and once as per-section composer functions, and scrapped both times.

But that only states the prohibition. The hourglass is the part that makes it *possible*,
because the sections genuinely do differ: identity has a role string, constraints a rule
list with a count threshold, examples nested groups. One code path, fourteen different
sections, zero section knowledge — those stop being contradictory for six reasons.

> **It converts an open-ended branch into a closed one.** This is the move everything else
> rests on. Branching on *section* is a list that grows every time a section is added, and
> every new arm is a new place for agent behaviour to leak into code. Branching on *data
> shape* — scalar, list of scalars, list of objects, group — is a handful, fixed, and adding
> a section adds no arm at all. The waist exists to get from the first kind of branch to the
> second.
>
> **The narrowing is deliberate information destruction, and that is the point.** Chunk
> discards field identity and keeps slot. Gather discards which axis a fragment came from
> and keeps what affects one output point. By the waist there is no "constraints section" —
> only a bundle, and every section produces bundles of the same shape. This does not hide
> the differences; it demonstrates they do not reach the middle.
>
> **The four axes meet in exactly one place.** Per-section composition would give fourteen
> sites where data, structure, content and display touch — fourteen chances to entangle,
> fourteen things to audit. Here there is one. Axis independence stops being a discipline
> and becomes a property of the shape, which matters directly for the matrix, since
> entanglement is what collapses a dimension.
>
> **"Values, not verdicts" is what protects the waist.** A bundle carrying the *decision* —
> chosen variant, filled text, visibility answer — means the deciding happened upstream, in
> the wide part, where sections still differ. That is per-section decision logic wearing a
> bundle's clothes. Carrying the toggle's value, the variant table plus the selector, the
> template plus the dict, forces all resolution into the one place with no section knowledge
> left.
>
> **Names can only be the mechanism if there is exactly one reader.** Suffix determines
> slot, trunk links content to data, placeholders determine interpolation — all of which
> works because one piece of code reads them mechanically. Fourteen composers reading the
> same conventions would drift, and the conventions would stop being load-bearing. Generic
> engine and names-as-mechanism are not two design choices; they are the same one.
>
> **And Galdr sits past the last gate.** Its output is prose, where schema checking no
> longer reaches, so the strategy switches from verifying the artifact to verifying the
> machinery. That is achievable only if the machinery is small: fourteen code paths tested
> against prose output is not something anyone finishes; one generic path is. The hourglass
> is not only what makes the engine versionable — it is what makes the weak end of the
> verifiability gradient survivable.

### Why stage 1 comes first

The waist cannot be designed until you know what a bundle contains, and the honest way to
learn that is to look at what actually lands in each slot across every section — not to
guess a model and build an engine around the guess.

That is why the slot dict is deliberately untyped. `assembled.py` says so outright: *"the
shape discovery is ongoing, so we don't commit to a Pydantic model until we know what a
bundle actually contains."*

Stage 1 is the instrument that tells stages 2–4 what they have to handle. Reshape what is
messy, *then* write the simple engine — never a complex engine built around messy data.

### Why the old walker code is gone

A disconnected walker-based composition was retained in the tree for a period, deliberately,
against the usual rule — Draupnir having made the opposite call and deleted its dead
implementation outright.

That call was reversed. The walker is deleted, together with `markdown_render/`,
`template_interpolate/` and `data_unwrap/`, which nothing else used: fifty-six functions,
just under nine hundred lines. The reason given was that it had become confusing and was no
longer useful, which is the same reason Draupnir gave — **code you know is wrong still pulls
you toward it, and a label does not stop that.**

The cost of having kept it is worth recording, because it is the argument against ever
doing so again. `composed.py` was a *mixed* file: the live stage-1 functions sat beside the
orphaned ones with nothing to tell them apart by inspection. A reachability analysis run
during the deletion got it wrong on first pass — it followed function *calls* only, so a
predicate passed by name rather than called looked dead, and four live functions were
nearly removed. Mixed dead and live code is not merely untidy; it defeats the tools you
would use to clean it up.

It is recoverable from git. **Do not recover it to consult** — that is precisely what the
deletion was for.

---

## Working with it

**Reshape the schema before complicating the engine.** The three control-surface schemas
are tail-end — nothing downstream consumes them — so changing one costs a mechanical
regeneration through Verdandi and Draupnir. When engine code grows detection logic to
cope with an awkward shape, the shape is the bug. (This applies to the surfaces. The
*data* schema is Regin's output and changing it is a wider blast radius.)

**Show the data before drawing conclusions.** Analysing one axis alone and reporting
conclusions has repeatedly wasted large amounts of time. Produce the interleaved view —
data, content, structure, display together, per section — and let the author identify
where the pattern holds and where it breaks. A break is almost always a naming or schema
fix, not engine code.

**Current state is read live**, from the code and `git log`. Nothing here records
implementation status except the one warning above, because nothing would keep it true.
