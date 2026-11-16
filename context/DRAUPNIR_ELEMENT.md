# Draupnir — The Schema Compiler

[[AGENT_BUILD_SYSTEM|↑ the map]] · [[VERDANDI_ELEMENT|Verdandi]] → **Draupnir** → [[NORNIR_GATES_ELEMENT|Nornir gates]] → [[REGIN_ELEMENT|Regin]] → [[GALDR_ELEMENT|Galdr]]

## What it is

A Python package that compiles the Verdandi YAML hierarchy into JSON Schema documents.
It is the only stage that *consumes* Verdandi — the files themselves are read by a gate
on its behalf — and the only thing that produces the schemas everything else depends on.

**It is the enforcement half of Verdandi.** Verdandi expresses the constraints as
directory structure and file shape; Draupnir is what makes violating one a compile error
rather than a convention someone might choose to follow. The same data-from-logic split
the system applies everywhere, applied here to the constraint system itself — and the
self-hosting loop closes the circle, because Draupnir's own input models *are* the
definition of what a Verdandi file may contain.

The property that matters most about it is that it is a **reliable, idempotent** schema
builder. Compiling twice produces the same output; nothing accumulates and nothing depends
on what happened to be on disk beforehand. That is what makes the forward cascade safe to
re-run at any point, what lets `--check` mean anything, and ultimately what the benchmark
matrix rests on — if regeneration drifted, no two cells would share the data they claim to
share.

Three entry points:

| Command | Does |
|---|---|
| `draupnir` | compile Verdandi YAML → JSON Schema documents |
| `draupnir-export-schemas` | export Draupnir's own models → the input schemas |
| `draupnir-generate-models` | generate Draupnir's input models from those schemas |

The last two are the self-hosting loop; see below.

**Invocation:** bare `uv run draupnir` is the generate-everything mode: it compiles every
Verdandi project that has a schema level, and `--project` narrows it to one. The flags are
`--check` (report drift without writing), `--list`, `--fragments`, `--project`,
`--verdandi-dir`, `--output-dir`, `--workspace`.

> There is no `--all` flag. Several documents in this ecosystem — including some in
> Draupnir's own repository — tell you to run `uv run draupnir --all`. That is wrong
> and has been verified wrong against the CLI. It will fail as an unrecognized
> argument.

---

## How it works

### Loading is the pipeline

Levels load in declaration order, which is deliberately bottom-up: patterns first,
schemas last. By the time a higher tier validates, every reference it names is already
in the cache. **There is no resolution step** — nothing is loaded half-formed and
fixed up later. Every model is in final form from the moment it validates.

The cache is keyed `level/name` — the same string used as a reference inside the YAML.
The reference syntax and the lookup key are the same thing.

### YAML enters through a reader

Draupnir imports no YAML parser. Not `yaml`, not anything. It calls
`read_yaml_validate_json` — a compiled Rust module — naming the level's schema per call.
The reader reads the file, converts YAML to JSON, validates against that schema, and
returns one of two outcomes: a success carrying the validated JSON string, or a refusal
carrying its failure class and message.
Draupnir's side is an `ffi.py` wrapper that types that outcome at once, and one
`model_validate_json` on a success. A refusal fails closed: the file stays out of the cache,
the error is reported, and the run exits non-zero. So does a run that finds no files at all.

This is the same rule every Python stage follows, and it applies to the schema
generator itself. There is no bootstrapping exception.

### Compilation is a graph walk, not a tree walk

Everything loaded becomes a node in a directed graph; every reference becomes an edge
carrying its zone (`required`/`optional`/`conditional`) and any conditional predicate.
Then:

```
build order        = topological sort, walked linearly
$defs selection    = nodes with in-degree ≥ 2 within the schema's induced subgraph
subtree extraction = descendants of the schema node
type dispatch      = a node attribute lookup into a builder table
```

**Zero recursion anywhere.** Deduplication is per-schema, not global — the same node
may be shared inside one schema's tree and unique in another's, so it becomes a `$def`
in the first and inlines in the second.

### The self-hosting loop

```
hand-written models  (structure/model/)
        │ export-schemas
        ▼
schemas/input/{level}.schema.json  ──►  named per call to read_yaml_validate_json
        │ generate-models                to validate Verdandi YAML
        ▼
generated input models  (structure/gen/input/)  ──►  parse the reader's output
```

One source of truth, two consumers, zero manual sync. The models that define what a
Verdandi file may contain also produce the validator that enforces it and the type that
parses it.

### Fragments — closing the second door

An agent definition is not one file. It is a definition *plus include files*, and those
includes are the one path by which data could otherwise enter unvalidated — the definition
gate-checked, its includes trusted on arrival.

`--fragments` closes that. It exports seven standalone schemas, each matched by a
`gate_include_*_input` in Nornir. Input gates only: an include is read and inlined, never
written back.

What makes this more than "validate the includes too" is the registry
(`structure/config/fragments.py`):

```python
include_success_criteria       = "array/success_criteria_reduced"
include_example_group          = "group/example_group_reduced"
include_guardrails_constraints = "simplearray/guardrails_constraints"
```

Those are cache keys pointing at **nodes inside the checkpoint schemas**, not separately
authored shapes. An include's schema *is* the node that will hold its content after
inlining, extracted and published as its own document. The include and its destination
cannot drift, because they are one definition with two exports — the same
derive-rather-than-hand-sync rule the system applies everywhere.

Note the `_reduced` in those keys: the fragment is the *post-inlining* shape, so an include
file must already be in the form it will occupy. **Inlining is a splice, not a transform,**
which is why Regin's four content reducers can be as thin as they are.

Seven fragments across those four branches — instructions one, examples two (entries and
group), guardrails two (constraints and anti-patterns), criteria two (success and failure).

---

## Why it is built this way

### Why a graph — the expensive lesson

The obvious implementation of "compile a nested type hierarchy" is recursive descent:
a builder that walks down, calling itself. That was tried. It required threading a
`build_fn: Callable` through every builder so leaves could call back into the
dispatcher, which the architecture forbids.

Three consecutive attempts were made to keep the recursion and satisfy the constraints:
a context object holding the dispatch function; a bottom-up rewrite with a lookup dict;
loosening the shared reference types to accept strings. The first two reproduced the
same violation in new clothes. The third was worse than a failure — it widened type
aliases shared between input loading and output generation, which would have poisoned
every downstream schema and contaminated the entire pipeline through the gates.

The diagnosis, recorded in the repository:

> "We kept trying to fix the symptom while preserving the disease. Recursive descent
> requires the leaf to know how to call the root. That's an upward dependency, and the
> architecture correctly forbids it."

The constraints were not obstacles. They were reporting a true fact about the algorithm.
Schemas are a topological problem — the data is a directed acyclic graph — so the
solution is a graph, and every workaround disappears because the need for them does.

**Carry this as the general rule: if you cannot solve a problem while staying inside
the structure, you have not found the right architecture yet.**

### Why the dead code was deleted rather than kept for reference

When the recursive implementation was replaced, it was removed entirely — directories
and all. The stated reason: *even if you know the code is wrong, its presence pulls you
toward it.* Training-data gravity does not care that you labelled something obsolete. A
label is just more tokens; the code is a working example of the pattern you are trying
not to write.

(Galdr makes the opposite call for one specific body of code, deliberately and with the
tradeoff named. See [[GALDR_ELEMENT]].)

### Why bottom-up load order rather than resolve-on-demand

Resolve-on-demand means models exist in a half-resolved state, which means every
consumer must handle "maybe resolved, maybe not." Loading in dependency order removes
the state entirely: a model either validated — with every reference already present —
or it did not.

---

## Working with it

Draupnir sits at the head of the cascade. It produces the schemas that gates embed and
that the runtime stages — Regin and Galdr — generate their Pydantic models from.
Running it is the first of four commands (compile → rebuild gates → regenerate models →
re-run the pipeline); stopping after it leaves gates validating against schemas that no
longer exist.

`--check` compiles in memory and reports drift without writing. It is the right tool
for "did someone edit a generated schema by hand."

### One gap that is load-bearing

Draupnir turns every reference into a typed graph edge — except one. A conditional
predicate's target field is carried through as an opaque string: `build_if_condition` in
`logic/transform/conditional_build/simple.py` places `when.field` straight into the
emitted `required` and `properties` without checking that a field of that name exists in
the enclosing container.

So a mistyped predicate target **fails open.** `only_when` quietly stops being exclusive;
`always_when` quietly stops requiring anything. Both failures are invisible in the
generated schema, which looks entirely well-formed.

There is one such typo in the tree today, and its effect is that the schema constraining
an agent's own structured output is never required when that output is JSON or JSONL. The
detection script and the confirmed instance are in `TODO.md` in the Verdandi repository.

State it plainly when you meet it: a predicate target is a reference like any other, and
it is currently the only kind that is not resolved.

### The level count

The `Level` enum has 15 members and the builder table has 14, because `schema` is assembled
rather than built.
