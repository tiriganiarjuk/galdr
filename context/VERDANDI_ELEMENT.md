# Verdandi — The Type Hierarchy

[[AGENT_BUILD_SYSTEM|↑ the map]] · **Verdandi** → [[DRAUPNIR_ELEMENT|Draupnir]] → [[NORNIR_GATES_ELEMENT|Nornir gates]] → [[REGIN_ELEMENT|Regin]] → [[GALDR_ELEMENT|Galdr]]

## What it is

Around 730 hand-edited YAML files. **There is nothing to execute** — no
`pyproject.toml`, no package manifest, no entry point. Verdandi is data; other tools
consume it. If you go looking for the program you will waste twenty minutes, because
there isn't one.

Do not let that make it look inert. **This is arguably the most significant part of the
system,** and the reason is a question worth sitting with before you read further:

> Schemas are among the best tools available for constraining LLM work and checking it
> mechanically. So — can you trust an LLM to write a good schema?

No. And humans are no better, because JSON Schema is a tedious language and the mistakes
it invites are asymmetric: an error almost always leaves a schema **too permissive rather
than too restrictive.** A missing `additionalProperties: false`, an incomplete `required`
list, `anyOf` used as a shrug — each of those is a perfectly valid schema, and a loose one
is indistinguishable from a strict one by inspection. The failure is silent by
construction, which is the one kind review does not catch.

It has already happened here. Schemas that were not tight enough surfaced downstream as
Regin throwing bugs and failing to catch things it should have caught.

And there is a circularity underneath. A schema's entire job is to be a fixed point
*outside* the LLM's interpretation. Let the LLM author it and validation proves only
self-consistency — you have promoted the thing under examination into the authority that
examines it, and handed yourself a file to point at, which makes the illusion more
convincing rather than less.

**Verdandi is the schema for writing schemas.** Nobody authors JSON Schema here. You
write one small YAML file, at a named level, which may only reference lower levels and may
only carry the keys that level accepts — and that file passes through
`read_yaml_validate_json`, against its level's schema, on its way in. The same medicine, applied one turn up: not *don't write a bad schema* but
*a bad schema is not expressible.*

That is also why it is the least agent-specific thing in the pipeline. Everything
downstream is about agents; this is about the general problem of getting trustworthy
schemas out of a machine. A second project — of any kind — inherits the whole apparatus:
JSON Schemas, compiled validators, generated models.

---

## How it works

### Fifteen levels

Three container tiers, with the type tier beneath them and the field membrane between:

```
Types              pattern · atom · enum · element · union · tuple      6
Field membrane     field                                               1
Simple containers  simplearray · simplegroup                           2
Complex containers array · group · superarray                          3
Top level          section · shallowsection · schema                   3
```

A file references files at lower levels. **Never sideways, never up.** A reference is a
file path — `atom/path_absolute`, `field/role_identity` — with no name-based lookup and
no inline type declarations above the pattern level. The file path *is* the identity.

Downward does **not** mean one hop. Each level has an explicit list of levels it may
reference, and levels are skipped routinely:

```
simplearray    accepts  field/
simplegroup    accepts  field/, simplearray/
array          accepts  simplegroup/
group fields   accepts  field/
group cont'rs  accepts  simplearray/, simplegroup/, array/
superarray     accepts  group/, simplegroup/
section        accepts  group/, array/, superarray/
shallowsection accepts  field/, simplearray/, array/, superarray/, group/
```

Read that list before authoring: it answers "may a group contain a group?" (no — but a
group may contain an array of simplegroups) and every similar question. Containers do
nest; they nest through the levels this table permits.

**The levels accreted. They were not designed up front.** Each one exists because some
kind of document could not be expressed with what was already there — `shallowsection`
most clearly, serving a flat kind of presentation that `section` could not model. Read the
fifteen as an empirical set that grew from need, not as a taxonomy derived from first
principles.

**And the reference table is not a permissions list. It is a set of closed worlds.**
Choosing a level chooses what you can no longer do. `shallowsection` accepting five levels
is not extra latitude — it is a *different* closed world, and taking it forecloses the
`section` path and everything that path allows. The design is deliberately rigid and
exclusionary; the intent is that abuse should be hard, and wherever possible impossible.

The two projects show what that looks like on disk. `agent-builder` is deep and uses every
container level. `agent-output` is flat — 282 fields, 41 shallowsections, 15 simplegroups,
3 schemas, and **zero** arrays, groups, sections or superarrays. It never touches the
complex-container tier at all, because the world it chose does not have one.

Each level builds one thing on the level below. A path type, end to end:

```
pattern/absolute        the regex
  → atom/path_absolute  a string constrained by it, with exclusions
    → element/…         plus a runtime format contract (e.g. "must exist")
      → union/path_any  either relative or absolute
        → field/…       plus a description of what this particular path means
```

Five files, five levels, each adding exactly one thing. Not every type needs the full
chain — most fields reference an atom or enum directly through `field/`. Build only the
levels that add something.

### Constraints compose in both polarities

An atom is not only what it matches. It is also what it must *not* match:

```yaml
# core/atom/path_absolute.yaml
type: string
pattern: pattern/absolute
min_length: 2
excludes: [pattern/traversal, pattern/env, pattern/home, pattern/root, pattern/claude]
```

The same pattern primitives serve as exclusions. So `path_absolute` is not "starts with a
slash" — it is that, minus parent traversal, minus `.env` at any depth, minus a bare `~/`
or `/`, minus any `.claude` directory. A path that escapes its sandbox is not a value the
type can hold, and every field built on that atom inherits the entire exclusion set for
free.

This is where the security posture for generated agents actually lives. The description on
`pattern/claude` reads *"agents must not read or modify their own control infrastructure"*
— a policy statement, enforced as a regex, at the bottom of the type system, in an
immutable file.

Closed value sets do the same work on the enum side. `unix_command` is exactly
`[find, ls, du, wc, stat, diff, tree]`, so no definition can grant `rm` or `curl` — those
are not values. `permission_mode` has one legal value, `bypassPermissions`, which is not a
loosening but a *swap*: from interactive prompts to structural hook enforcement, the only
thing that works for an unattended subagent. Declaring it as a one-value enum instead of
hardcoding it means the choice still has to be stated and still gets validated.

One consequence worth noticing, because it is what makes the benchmark matrix computable
at all: **the presentation knobs are enums too** — `heading_format`, `list_format`,
`inline_separator`, `separator_style`, every `*_variant_key`. Sweeping ten knobs across
all their combinations is a finite, enumerable job only because each knob draws from a
closed set instead of being free text.

### The `element` level, and what runs it

`element/` holds three files. That reads like a vestigial level until you see what consumes
them.

An element is an atom plus a contract the schema language *cannot express*.
`element/path_exists_absolute` says **this path must exist on disk** — something no regex
and no enumeration can check, because it is a fact about the world rather than about the
string. Draupnir compiles it to a `"format": "path_exists_absolute"` marker in the output
schema, and Nornir's `path_verify_io` walks incoming data for fields carrying that marker
and checks the filesystem before the gate returns.

So **the element level exists to carry constraints JSON Schema cannot express, and the gate
is what executes them.** Three files because there are three runtime contracts. The level is
not underused — it is exactly the size of the problem it covers.

See [[NORNIR_GATES_ELEMENT]], "What a gate actually checks," for the other end.

### The field membrane is mandatory — and it is where the system locks

Containers reference `field/` files. **Never raw types directly.** This is the rule most
likely to feel like pointless indirection, so here is what it buys.

**It resolves a tension between reuse and meaning.** Types are reusable precisely because
they are anonymous — `atom/path_absolute` is the same type everywhere it appears. But a
container needs members that mean something specific. Attach descriptions to types and you
destroy the reuse; attach them inline in containers and the same field gets described
differently in two places. The membrane is the one place that tension resolves: where a
type and a description merge into a field value, and the only place per-field meaning can
live.

Without it the symptom shows up immediately — an input path, an output path and a schema
path all compile to the identical `$ref` pointing at one string atom. Three distinct
meanings collapse into one opaque pointer, because meaning was never given a home.

**And the membrane is where the filesystem locks.** Every file in `core/` — the whole type
tier — carries the `schg` system-immutable flag. Everything above the membrane is freely
writable:

```
core/  pattern · atom · enum · element · union · tuple       immutable
─────────────────────────────────────────────────────────  ← the line
field · simplearray · simplegroup · array · group ·          writable
superarray · section · shallowsection · schema
```

This is deliberate, and the rule is precise: **the constraint-bearing definitions are
immutable.** The type tier is where constraints are actually *expressed* — regexes,
exclusions, closed value sets, minimum lengths. Everything above only arranges things that
are already constrained. Immutability follows the constraint, not the abstraction level.

The consequence is the whole point. An LLM working in Verdandi can compose whatever it
likes and cannot change the vocabulary it composes from. It cannot loosen `path_absolute`
to permit `..`, cannot add a command to `unix_command`, cannot widen `permission_mode`.
Those are exactly the edits that would silently expand the blast radius of every agent the
system will ever generate, and they are unavailable at the OS level rather than by
convention.

Gates buy distance. This buys impossibility.

> Two files are currently unlocked and should not be: `core/atom/string_label.yaml` and
> `core/enum/inline_separator.yaml`. Tracked in the repository's `TODO.md`.

### Two projects, one core

| Project | Holds | Its schemas end up serving |
|---|---|---|
| `core/` | shared primitives — patterns, atoms, enums, elements, unions, tuples | both projects, via symlink |
| `agent-builder/` | 13 schemas: the pipeline checkpoints | Regin |
| `agent-output/` | 3 schemas: structure, content, display | Galdr |

**Nothing reads these YAML files except Draupnir.** Regin and Galdr never see them —
they consume the JSON Schemas Draupnir compiles, and the Pydantic models generated from
those. The right-hand column names the eventual beneficiary, not the reader.

The tier-1 directories inside each project are symlinks to `core/`. New primitives
always go in core.

Note the asymmetry: agent-builder is deep (sections, groups, arrays, superarrays);
agent-output is flat (fields and shallowsections only). They model different things —
one a nested definition, the other three parallel control surfaces.

### Conditionals

Field presence can depend on other field values, in three directional keywords:

```
only_when     required when true, FORBIDDEN when false   (if and only if)
always_when   required when true, no effect when false
not_when      forbidden when true, no effect when false
```

Predicates are `equals:`, `in: [...]`, or `exists: true`. Scope is one character: a
**leading dot** traverses from the schema root, no dot is a sibling within the same
container. That is how a field in one section becomes conditional on a value in another,
and how conditions chain locally — `enforcement_output_tool` runs format → write_frequency
→ batch_size, each depending on the last.

**`only_when` is the load-bearing one, because forbidding on false gives you mutually
exclusive branches for free.** In `group/security_io.yaml`, three input targets each
declare `only_when .indirect.dispatch.dispatch_input_delivery equals file | directory |
tempfile`. Set the discriminator and exactly one of the three is required while the other
two become *forbidden*. A definition cannot declare both a file input and a directory
input.

That is a discriminated union without any of JSON Schema's machinery for one — no `oneOf`,
no `if`/`then`/`else`, no discriminator keyword. Exclusivity falls out of the
bidirectionality, declared once per branch at the field that needs it.

### Stage variants

Types appear as `_raw`, plain, and `_reduced`. These describe stages of *agent
definition processing* — authored, paths absolutized, includes inlined — **not** stages
of Verdandi itself. Verdandi is static. This trips up every reader once.

---

## Why it is built this way

### Why a schema at all

When a human and an LLM discuss a design, both come away believing they agree. The LLM
then builds from its own interpretation, and when asked whether the result matches the
discussion, evaluates it against that same interpretation. Artifact and assessment share
one possibly-wrong understanding. Their agreement is circular and proves nothing.

A schema is a fixed point outside both parties. "Does this conform?" is mechanically
checkable in a way "did we agree?" never is. That is the entire reason this layer
exists, and it is why the answer to "what's the schema?" must be **a file you can
point at** — not validation logic buried in code. Hand-rolled shape-checking in Python
is not schema validation; it is one party's interpretation wearing a costume.

### Why hand-authored YAML instead of hand-written JSON Schema

JSON Schema is a serialization format, not an authoring format. Written by hand it has
no composition, no reuse, and no way to enforce that a container may not reach past its
tier. The YAML hierarchy gives all three, and tier violations become **compile errors**
rather than subtly wrong output.

### Why not just write Pydantic models directly

Because one source feeds two consumers in two languages. The same YAML produces the
JSON Schemas that Rust gates embed *and* the Pydantic models that Python stages import.
Author the models directly and you own the job of keeping the Rust validator in sync
with the Python type by hand — forever, correctly, across every change.

That is the deeper principle: **if keeping two things consistent is a human's job, the
design is wrong.** Derive, never hand-sync.

### Why references may only flow downward

Tangles require lateral edges. Remove the possibility of lateral and upward references
and a tangled hierarchy cannot form — the same reasoning the code applies to its own
same-level imports.

The rule and the ladder are one mechanism rather than two. The levels are what "downward"
is measured along; without a strict ordering there is nothing for the rule to mean. A
single generic container level able to hold anything would let a container hold itself,
and the cycle would then have to be *detected* instead of being unrepresentable.

When two types appear to need each other, the mutual need is itself the finding: one of
them is holding something that belongs lower, where both can reference it. Splitting out
that shared piece is the move — adding a type *above* both does not help, since a higher
type can see them but they still cannot see each other.

---

## Working with it

**Edit the YAML. Never the generated schemas.** Files in `{project}/output/` are
derived artifacts; direct edits are silently overwritten on the next generation.

Anything you change here triggers the full forward cascade — regenerate schemas,
rebuild gates, regenerate models, re-run. See [[AGENT_BUILD_SYSTEM]].

**Read `COMPOSITION_RULES.md` in the repository before adding a level file.** It is the
formal specification of what keys each level accepts. Be aware that it and the files on
disk have drifted apart in several places — where they disagree, the files are what the
compiler actually consumes, and the disagreement is worth reporting rather than
silently resolving.
