# Regin — The Definition Resolver

[[AGENT_BUILD_SYSTEM|↑ the map]] · [[VERDANDI_ELEMENT|Verdandi]] → [[DRAUPNIR_ELEMENT|Draupnir]] → [[NORNIR_GATES_ELEMENT|Nornir gates]] → **Regin** → [[GALDR_ELEMENT|Galdr]]

## What it is

Regin takes an agent definition as a human authored it and resolves it into a single
vendor-ready data structure. It answers **"what is this agent?"** — not "how does it
read." Presentation is the next stage's problem and Regin knows nothing about it.

```bash
uv run regin <input.toml> -o <output_dir>
```

Input: an authored definition with workspace-relative paths and references to include
files. Output: `anthropic_render.toml`, gate-validated — Galdr's **data axis**. Galdr
takes three further inputs (structure, content, display) which have nothing to do with
Regin; this file is the only thing that crosses between the two stages.

Everything between is written to disk as a named TOML checkpoint.

---

## How it works

### It is a DAG, not a sequence

This is the single most important thing to get right, and the thing every previous
reader got wrong.

```
  defaults_inject → paths_resolve → paths_verify              run_trunk

        ┌──────────┬──────────┬──────────┬──────────────┐
   instructions  examples  guardrails  success      permissions    run_fanout
        └────┬─────┘          └────┬─────┘              │
      execution_merge        criteria_merge             │
             └──────────┬─────────┘                     │
                 includes_merge                         │          run_convergence
                        └──────────────┬────────────────┘
                                universal_merge
                                       │
                        render_regroup → anthropic_resolve
```

The four content reducers and the permissions resolver share no data and depend on nothing
from each other. **Everything on the same rank runs independently.**

### How the shape is expressed

Read `cli.py` — it is short, and it is the only place the ordering exists. Three functions
name the shape directly: `run_trunk`, `run_fanout`, `run_convergence`. The DAG is stated
once, in the wiring.

**Module names carry no sequence at all.** The convention is `{noun}_{verb}` — subject
first, action second: `defaults_inject`, `paths_resolve`, `content_reduce`,
`render_regroup`. There are no level numbers anywhere in the source; they survive only in
log lines and docstrings.

That is the third naming scheme this pipeline has had, and the history is worth knowing
because it is the clearest recorded case of names beating instructions.

> The modules were once `step_01_`, `step_02_`, `step_03_`. The recorded result: *every LLM
> that entered the workspace built a sequential pipeline, despite explicit DAG instructions
> in the documentation.* The instruction was read once; the numbers were seen hundreds of
> times. The numbering won.
>
> The first fix was `level{N}_{branch}_{operation}`, so that a shared level number meant
> parallel. It works, but it still smears an ordering across every filename and still asks
> the reader to reconstruct a graph from numeric prefixes.
>
> The current answer drops the numbers entirely. A module says what it operates on and what
> it does; the graph lives in the wiring. Nothing in a filename can imply a sequence,
> because no filename mentions one.

The one naming rule that survived every scheme is verb tense:

```
paths_resolve    the module — an action, this DOES the work
paths_resolved   the checkpoint — a state, this IS the output
```

Get the tense backwards and the next reader believes work is done that hasn't started.

### The delta principle

**Every branch transforms exactly the delta between its input checkpoint schema and its
output checkpoint schema. Nothing more.**

That is the whole contract. The two schemas define the job; the branch closes the gap
between them. It is what keeps each branch small enough to hold in your head, and it
means you can always answer "what does this stage do?" by diffing two schemas rather
than reading code.

Two branches have no transform at all — their docstrings read *"Delta: NONE. The gate
IS the branch."* They exist to validate and pass through. That is a legitimate stage,
not a stub.

### The uniform runner

Every branch has the same shape:

```
gate_in(path)  →  { work on typed models }  →  gate_out(path)
```

The work function receives a validated JSON string, parses it into models, does its
transformation, and serializes back out. **No filesystem access anywhere in between.**
Gates own the I/O; see [[NORNIR_GATES_ELEMENT]].

### What the levels do

| Level | Job |
|---|---|
| L0–L2 | inject defaults, absolutize workspace-relative paths, verify the paths exist |
| L3 content | four parallel reducers inline include files into instructions, examples, guardrails, criteria |
| L3 permissions | validate security declarations, derive explicit and implicit grants, assemble the output tool |
| L4–L6 | merge the branches back together into one platform-agnostic model |
| L7 | regroup domain sections into consumption sections |
| L8 | resolve for the vendor — model, tool discovery, hooks, frontmatter |

**L7 deserves a note**, because its purpose is not obvious. A definition is *authored*
by domain — security here, task there, execution over there. A prompt is *consumed* by
section — identity, then input, then instructions. Those are different groupings of the
same fields, and something has to turn one into the other.

The reason it happens *here* rather than in Galdr is the rule the stage exists to satisfy:

> **Each section must contain everything it needs to resolve its own rendering.**

Fields are copied into every section that will need them, and then the checkpoint is
written and gate-validated — at which point the arrangement is immutable and proven. Do the
same regrouping inside Galdr and you would be doing it *after the last gate*, on mutable
in-memory data, on the far side of the verifiability gradient where schema checking no
longer reaches. Here it is still on the strong side.

This is the same decision as the duplication described below, seen from the other end: L7
is where the duplication happens, and self-sufficiency is why.

**L8 is the vendor fan-out.** Everything above it is platform-agnostic. A second vendor
would be a second branch at this level, producing its own render format — not a second
pipeline, and not a change to Galdr.

---

## Why it is built this way

### Why checkpoints on disk instead of one process passing objects

Every checkpoint is a real TOML file validated by a real gate. That buys three things
an in-memory pipeline cannot:

> **Inspectability.** When output is wrong you can look at the exact artifact each
> stage produced and see where it went wrong, without instrumenting anything.
>
> **A schema per boundary.** Each checkpoint has a schema, so each stage's contract is
> mechanically checkable rather than a matter of interpretation.
>
> **Restartability.** A branch can be re-run against its recorded input.

The cost is serialization at every hop. That cost was accepted deliberately.

### Why resolution is separate from composition

This is the split that makes the product possible. Regin resolves once and produces one
frozen data structure. Galdr then renders it many times against different control
surfaces. If resolution and composition were one program, every cell of the benchmark
matrix would re-resolve the definition, and the data axis could not be held constant
while the other three vary — which is the only thing that makes the comparison mean
anything.

### Why values are duplicated across sections

The same value appears at several rendering sites, and Regin writes it into every
section that needs it rather than having sections reference each other. This looks like
denormalization and is not a mistake.

Normalization is a discipline for managing **mutation** — keeping one copy from
drifting out of step with another as things change. Once a checkpoint is written and
gate-validated it is never rewritten, so there is no update and no anomaly to prevent.

Be precise about what "frozen" means here, because two senses are in play. The *artifacts*
are immutable once written. The generated checkpoint models are not: across
`structure/gen/` there are **413** `extra='forbid'` declarations and **zero** `frozen=True`.
`model_copy` appears **nowhere** in the logic tree. The hand-written helper models under
`structure/model/` are genuinely frozen.

What the orchestrators actually do is assign attributes directly, at **three** sites — all
of them merges, all attaching a sibling checkpoint parsed from JSON, all immediately passed
out through an output gate.

So the mutation window sits between two gates, which is exactly the zone the architecture
declares free: correct going in, correct coming out, anything in between. Freezing the
models would buy little the gates do not already buy. Whether that is the intent or drift
from it is a question for the author — but the shape is defensible, not accidental-looking.

What the duplication buys is that each section resolves without reaching outside
itself.

---

## Working with it

The models under `structure/gen/` are generated from the JSON Schemas. **Editing them
does nothing** — they are overwritten on the next generation. Change the Verdandi YAML
and run the cascade.

The CLI is the truth about what runs.

The four L3 content reducers are named for what they inline: `instructions`, `examples`,
`guardrails`, `success`. Do not conflate the fourth with `criteria_merge` — some documents
treat `success` and `criteria` as two names for one branch, and they are two different
stages. `run_success` reduces at L3; `run_criteria_merge` joins guardrails *and* success at
L4.

**Fourteen checkpoints, thirteen schemas.** The odd one is `paths_verify`, which validates
against `PATHS_RESOLVED` — the same schema on both sides, because the branch transforms
nothing and the gate contributes the filesystem check. That is "Delta: NONE, the gate IS
the branch" visible in the artifact count.
