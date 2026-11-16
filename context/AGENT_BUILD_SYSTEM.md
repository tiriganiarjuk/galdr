# The Agent Build System

The map. Territory: [[VERDANDI_ELEMENT|Verdandi]] → [[DRAUPNIR_ELEMENT|Draupnir]] → [[NORNIR_GATES_ELEMENT|Nornir gates]] → [[REGIN_ELEMENT|Regin]] → [[GALDR_ELEMENT|Galdr]] · companion: [[GALDR_CHALLENGES]]

**Read this whole file before touching anything. It is the map; the five element
documents are the territory.**

Your training contains a strong prior for what a build pipeline is: parse, transform,
render. That prior will fit this system well enough to feel correct and badly enough to
make you break things. What follows is the part your training does not contain.

---

## What this is

**A builder for subagents** — the agents you dispatch to do a task. Not a long-lived
conversational session. That distinction is load-bearing: nothing here is about context
management or surviving compaction. It is about the prompt you hand a worker.

---

## Why it exists

A subagent is affected by everything in its prompt. Every word, the order of the words,
what is said, and what is deliberately left out. Everything is a knob and a lever.

Because the substrate is probabilistic rather than deterministic, you can have an agent
that works, change one small thing, and break it through something in the *penumbra* you
did not think you were touching. That gives the actual problem:

> **You cannot change one variable at a time, so you cannot iterate.**

Note what this is *not*. It is not that instruction fails to produce compliance.
Instruction works. It is simply not **controllable** — and improvement you cannot control
is not improvement, it is drift.

### The wall, specifically

In the Bragi workspace a chain of naive agents had to do very specific work, and several
variations were worth trying: one long pass versus two, different models at different
stages. An LLM was asked to build the variants and a framework to test them against the
same data.

Roughly seven passes in, it emerged that the framework did not exist. The LLM had been
inventing new agents on the fly **and not saving the prompts.** There was nothing to
compare, nothing to reproduce, nothing to pin a result to. The effort was shut down.

**This system is the result of that disaster.** Every hard rule downstream traces
directly back to it — everything is a versioned file, every stage writes a gate-validated
artifact to disk, and `definition + structure + content + display + model` fully
specifies an agent. Those are not architectural preferences. They are the scar.

### The goal

**Make building an agent as deterministic as a probabilistic substrate allows.**

That is first, and it is immediate and practical: be able to define a good subagent, put
it to work in real tooling, and know it is the agent you tested. Everything below is what
determinism *buys* — none of it is a competing purpose.

### What determinism buys

> **Iteration that converges.** Sweep ten knobs across their combinations, run every cell
> against a known dataset, rate them. The comparison means something precisely because
> exactly one thing differs between two cells.
>
> **Regression detection across model versions.** A new model ships; re-run the same
> matrix and see what moved.
>
> **Evidence that survives a courtroom.** In legal or medical work, eventually somebody
> takes you to court because your agent got something wrong. The defensible claim is not
> "we have an audit trail" — it is that at the time of testing, *this exact agent* was run
> against a realistic benchmark and performed as well as or better than a human, with
> agent version pinned to model version and provable after the fact. This is the part of
> the problem nobody has nailed yet, and it is what a commercial version would lead with.

### The ambition underneath

We are well into the subagent era and most organisations still ship a *good enough*
agent. Not through lack of care — because iterating on a prompt is intractable, so you
iterate until it is adequate and then you stop.

Making iteration tractable is what lets you stop settling: go after the best agent
obtainable at that moment, and know that you got it.

---

All of which produces the constraint everything else bends to: **nothing which varies an
agent's behaviour may live in code.** A knob buried in Python is a knob you cannot sweep,
cannot version, and cannot point at afterward.

---

## The constraint your training does not contain

The system is designed against measured LLM behaviour, not idealised behaviour.

> Roughly **nine of ten persistent errors** in LLM-written code occur at IO boundaries.
>
> **Instructions fade; names persist.** A name is read hundreds of times per session, an
> instruction once. When they conflict, the name wins — this is documented here as a
> repeated, measured outcome, not a theory.
>
> **A referenced document goes unread.** The reader pattern-matches off what is in front
> of it and proceeds confidently.
>
> **Human and LLM both believe they agreed.** The LLM then builds from its own reading
> and validates the result against that same reading. The agreement is circular.

The response is never "try harder." It is to arrange things so the failure produces a
correct result anyway:

| Measured failure | Response | Where you'll see it |
|---|---|---|
| Errors cluster at IO boundaries | Move IO out of the application | compiled gates |
| Names outrank instructions | Put the instruction *in the name* | `_postscript`, `paths_resolve` vs `paths_resolved` |
| The manual goes unread | Make the unread path the correct one | field names that lead a guesser right |
| Agreement is circular | Put authority in a file outside both parties | schemas |

One stance, applied four times.

---

## The shape

```
        the world: files, network, subprocess, clock
                          │
        ┌─────────────────┴──────────────────┐
        │   GATES  (Rust, compiled)          │
        │   read · validate · write          │
        └─────────────────┬──────────────────┘
              typed in    │    typed out
                          ▼
        ┌────────────────────────────────────┐
        │   DRAUPNIR · REGIN · GALDR         │
        │   (Python) — transform typed data  │
        └────────────────────────────────────┘
```

A gate is a compiled Rust module that Python imports like any other module. Calling one
looks like this, and this is the entire interface:

```python
import gate_anthropic_render_input          # a .so on the import path

result = gate_anthropic_render_input.validate(str(path))
#  → {"ok": bool, "data": str | None, "error": {...} | None}

outcome = GateResult.model_validate(result).root      # GateSuccess | GateRefusal
model = AgentAnthropicRender.model_validate_json(outcome.data)   # on a GateSuccess
```

No subprocess. No parser import. The result is typed as one of two outcomes the moment it
arrives, a refusal stops the stage, and from `model_validate_json` onward the data is typed
and stays typed.

**What actually enforces this — stated precisely, because the aspirational version is
misleading.** The Python has no *convenient* path outward and every stage is written to
use gates. It is not physically prevented: `open()` exists in every Python namespace.
The wall is held by three things — gates being the only reasonable path, a guardrail
system that analyses every file you write and flags zone violations, and you knowing
the rule. **Treat "no IO in Python" as an active
obligation, not a guarantee you can lean on.**

The design's own history reads: secure the boundaries → externalize the IO → *there is
no door*. The third step is the target, and the target is not fully reached.

---

## Two different flows, drawn as one line

The five-part chain hides a distinction that matters:

```
BUILD TIME  (run when types change)      RUN TIME  (run per agent)

Verdandi ──► Draupnir ──► schemas        definition ──► Regin ──► Galdr ──► prompt
  YAML        compiler       │                            │        │
                             └──── embedded in gates ─────┴────────┘
```

Verdandi and Draupnir do not participate in building an agent. They produce the
*schemas*, which gates embed and which both runtime stages generate their Pydantic
models from. Regin and Galdr are the actual agent path.

Reading the chain as one runtime flow is a common and costly mistake.

---

## Why it is divided this way

> **Verdandi and Draupnir are split because data is split from the logic that consumes
> it.** Verdandi is a directory of YAML with nothing to execute; Draupnir is the
> compiler over it. Same principle the code applies internally — shapes in one place,
> operations in another, and where a thing lives tells you what it is.

> **The gates are Rust because the wall has a different job and a different change
> rate.** It is solved once and left alone while the logic churns. Separate language,
> separate build, separate repository: an LLM iterating on Python business logic is not
> one file away from the validator constraining it. That is a distance argument, and
> distance is weaker than impossibility — but it is real and it is what exists.

> **Regin and Galdr are split pragmatically, and the line has moved.** Regin once ended
> at the universal agent, and Galdr held the vendor-specific step. That forced a great
> deal of duplication for no gain, so the vendor step moved up — Regin now does
> everything it used to *plus* what was once Galdr's first stage. Do not look for a
> principle in exactly where the boundary falls. It is placed where it costs least.

**What Regin is underneath the pragmatism** is the part that turns an authored definition
into a universal agent — as close as can be worked out to the ingredients of a perfect
subagent.

It is its own stage because that is a world of tricky reconciliation. The definition TOML
has many required inputs, every one of them has to resolve correctly, and the universal
agent has to be **known good** on the way out. And these definitions are not mostly
hand-written — **an agent writes them.** So incorrect input is not quietly repaired
downstream. It is blocked and returned, with what has to change.

### The double gate

This is the mechanism the whole pipeline rests on, and it is worth stating plainly:

```
gate in   →   transform   →   gate out
   │                             │
does it have                does it have
the right shape?            the right shape?
```

**An LLM can do whatever it does in the middle, so long as it is correct going in and
correct coming out.** Not trusted — *verifiably* correct, at both ends, mechanically
checked. That is what makes LLM-written transformation safe to have in the pipeline at
all.

Every step in the DAG has this. So the input was verifiably correct going into Regin and
verifiably correct coming out. Intermediates are stored, so when something is wrong you
can point at the stage: correct up to here, broken from here.

**Two reasons, one mechanism.** The double gate and "no IO in Python" are coequal, and
they are as coupled as they look:

> **The gate is the only door.** Because a compiled Rust module owns reading and writing,
> every other avenue for data to get into or out of the application can be closed. And IO
> is where the LLM is worst — roughly nine of ten persistent errors in LLM-written code
> occur there.
>
> **The gate is the checkpoint.** Two of them bracketing a transform keep the blast radius
> small and give incremental verification — still good, still good. Nothing merges and no
> stage proceeds unless the previous one was verifiably correct.

Neither half stands alone. Verification without owning the IO leaves a path for data to
arrive around the check. Owning the IO without verification gives you a safe door and no
proof. If one has to be named as the thing the architecture *depends* on, it is the double
gate — but the reason the double gate can be airtight is that the same component owns the
door.

### The verifiability gradient — why Galdr is different in kind

The vendor step is more of the same: verifiably vendor-correct on the way out, verifiably
correct on the way into Galdr, and the same for Galdr's other three inputs.

**Then it stops.** Galdr's output is prose. Text is composed, wording is added, the result
is free-form — and schema-based checking cannot establish that free-form prose is correct.
Automatic checks on Galdr's output cannot carry the confidence the same checks carry
everywhere upstream.

So the strategy changes at exactly that point. Instead of verifying the artifact, you
verify **the machinery** — the composition engine itself has to be correct, backed by
ordinary tests over its output.

This is the structural reason Galdr is the hard part. The safety net that protects every
other stage does not extend into it.

Everything upstream of Galdr exists to produce one trustworthy artifact. One stage then
multiplies it — outside the reach of the guarantees that produced it.

---

## The four axes

Galdr's inputs, and the rule they must obey.

| Axis | Source | Answers |
|---|---|---|
| **Data** | `anthropic_render.toml` (from Regin) | what to say |
| **Structure** | `structure.toml` | what to include |
| **Content** | `content.toml` | how to word it |
| **Display** | `display.toml` | how to format it |

### The test that generates the split

Those four labels describe the files that exist. They do not tell you where a field you
have never seen before belongs. The rule that does is **invariance**:

> The core of it — the actual data point, **the thing that stays invariant across every
> variant of this agent** — that is the data. Whether it is shown at all, how it is
> worded, how it is formatted, what order it comes in: those are the knobs.

That is a test you can apply rather than a label you can only match. It is also why "a
heading string in the data model" is wrong in terms you can *act* on instead of merely
recognise: the heading can change while the agent stays the same agent, so it is not
invariant, so it is not data.

### Where the data catalog came from

Both empirical and derived, over several days of work.

**Empirical** — enumerate everything that could or should go into a subagent prompt,
against prompting best practice and against what you actually want subagents to do.

**Derived** — dig into how the vendor defines a subagent. The data has to match
Anthropic's field inventory and the expectations of an Anthropic subagent: how an agent is
invoked, what options the vendor exposes, what belongs in the prose body. The same
exercise runs again for every new vendor.

This is why the vendor step sits on the **data** side of the pipeline rather than among
the knobs — the vendor determines what the invariant core even is. Concretely: because
Anthropic has hooks, hooks are generated automatically to constrain which tools the agent
may use and where it may read and write. A vendor with different control surfaces
produces different data arriving at Galdr.

### Why three knob files rather than one, or five

The split fell out naturally rather than from a stated rule. Content is about wording;
structure and display work on their own axes. It was articulated at length in discussion
while working out what the knobs and levers are, and is likely recorded in those
documents — but it is not consolidated into a single formal statement here, and it is
validated largely by recognition: looking at the files, *yes, those belong together.*

Treat that honestly. Do not invent a crisp delineation to fill the gap. If you need the
boundary between structure and display settled for a particular field, that is a question
for the author, not something to reason your way to.

**Where the line actually falls**, because "never entangle" alone is not usable:

Axes *share a vocabulary* and that is normal. Structure's `framing_selector = "territory"`
names a key that Content defines alternatives for; swap the content file and the same
key selects different prose. Both files mention the same word and neither depends on the
other's content. That is the design working.

What is fatal is an axis *holding another axis's data*. A heading string inside the data
model is content living in the data axis — now you cannot swap wording without editing
data, and the matrix dimension collapses.

Stated positively, which is the usable form:

| Axis | Owns | Marked by |
|---|---|---|
| **Data** | the values — and the names the other three align to | (from the pipeline) |
| **Structure** | the *choice*: whether a fragment renders, which variant is picked | `_visible`, `_selector` |
| **Display** | the visual form, and the counts that drive automatic switching | `_format`, `_format_threshold` |
| **Content** | the words | `_template`, `_label`, prose |

Two consequences worth stating explicitly, because both have been argued the wrong way:

> **Data is the source of truth for names.** When another axis disagrees with the data
> field's name, the *axis* is renamed. The data model is never bent to match a control
> surface.
>
> **A threshold in Display is not a Structure decision leaking.** Structure says *which*;
> Display says *what count* triggers automatic behaviour. Both can be about the same
> fragment without either holding the other's data.

---

## The forward cascade

```
edit Verdandi YAML
  → uv run draupnir                    regenerate schemas
  → nornir_deploy --build gates        rebuild gates to embed them
  → regenerate models in each stage    Pydantic models from the new schemas
  → re-run Regin, then Galdr
```

Skip a step and artifacts disagree: gates validating yesterday's schema, models that no
longer match the data. Nothing detects this for you; it surfaces as validation passing
something it should reject.

A related hazard, distinct from skipping: because the cascade propagates *faithfully*, a
bad change at the top reaches everything. One recorded near-miss involved widening a
type alias shared between Draupnir's input loading and its schema output, which would
have loosened every downstream schema at once. Review changes to shared types with that
blast radius in mind.

---

## The five parts

| Part | Document | One sentence |
|---|---|---|
| Type hierarchy | [[VERDANDI_ELEMENT]] | hand-authored YAML; the source of every shape |
| Schema compiler | [[DRAUPNIR_ELEMENT]] | compiles that hierarchy into JSON Schema |
| Validation wall | [[NORNIR_GATES_ELEMENT]] | compiled validators; the only sanctioned IO |
| Definition resolver | [[REGIN_ELEMENT]] | resolves an authored definition into one frozen artifact |
| Composition engine | [[GALDR_ELEMENT]] | renders that artifact against three swappable surfaces |

One companion document, not a sixth part: **[[GALDR_CHALLENGES]]** names the specific
problems currently being untangled in Galdr — a stalled rename cascade, controls whose type
cannot express the choice being asked of them, engine mechanisms that several sections need
and none has, and data fields with no path to the page. It is deliberately volatile where
the five element documents are not. Read [[GALDR_ELEMENT]] first; read the challenges
before changing any field name.

Two things to expect before you start.

**A guardrail system runs on you while you work.** Every file you write is analysed and
feedback arrives automatically. Its checks are proxies — each one stands for a quality
property, and the useful question when feedback arrives is "what is this a proxy for?"
Satisfying the number while missing the target converts one honest finding into several
confusing ones. It is a separate system, documented on its own terms, and you do not
need it to read these documents.

**When the constraints and your solution fight, the constraints are usually reporting a
fact.** There is a recorded case of three consecutive attempts to work around a single
violation, all failing, because the chosen algorithm genuinely required a dependency the
architecture forbids. The fix was a different algorithm. If you cannot solve a problem
while staying inside the structure, that is evidence about the solution, not the
structure.
