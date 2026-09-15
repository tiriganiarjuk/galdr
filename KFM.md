<!-- ═══════════════════════════════════════════════════════════════════════ -->
<!-- DO NOT EDIT THE PRELUDE. Before editing ANY part of this file, read     -->
<!-- /Users/johnny/ai/CONTEXT_MANAGEMENT_SYSTEM.md — the KFM section        -->
<!-- defines what this file is for and why it is not linked from anywhere.   -->
<!--                                                                          -->
<!-- DO NOT LINK THIS FILE. Not from the CONTEXT_MAP, not from CLAUDE.md,    -->
<!-- not from the README. Its name is uninformative on purpose.              -->
<!--                                                                          -->
<!-- Entries are FAILURE SHAPE with concrete facts routed out. An entry that -->
<!-- names files and functions is a clock: it will outlive them and then     -->
<!-- assert something false to a reader who arrived here because something   -->
<!-- had already gone wrong.                                                  -->
<!-- ═══════════════════════════════════════════════════════════════════════ -->

# KFM — Galdr

Known failure modes. Each entry records something that actually went wrong here, badly
enough or often enough to be worth writing down: a mistake that kept recurring, one that
was tedious to rediscover, or one that cost hours nobody wanted to spend twice.

**This file is deliberately not linked from anything.** Not the CONTEXT_MAP, not CLAUDE.md,
not the README. It has a name that tells you nothing on purpose. That is not tidiness — it
is the point:

> A list of failure modes read *before* you have a model of the project is not a warning,
> it is a set of suggestions. Naming a mistake supplies it. And a vivid catalogue of nine
> concrete failures shadows the orientation gate it sits above — a reader absorbs the
> stories, feels informed about the project, and skips the documents that would actually
> have oriented them.
>
> Read at the right moment — when something has already gone wrong, or when you are about
> to touch a part with a known history — the same entries are worth what they cost. The
> content is not the problem. The timing is.

The mechanism for *when* a reader gets sent here is undecided. Until it is decided, nothing
points here, and that is intentional rather than an oversight.

**If you have landed here anyway:** read it as history, not as instruction. Nothing below
is a description of the tree as it stands now — check anything concrete against the code
before acting on it.

**Maintenance:** an entry retires when its vector is gone. A trap guarding code that no
longer exists is worse than no trap, because it is the rigid layer asserting something
false. This has already happened once. Nothing automatic enforces it.

---

## Scrapped work — what these cost

Previous sessions in this project:

- Built a 14-class OOP inheritance hierarchy inside what was supposed to be a functional architecture — the entire renderer had to be scrapped
- Used `dict[str, Any]` for gate output instead of `GateResult.model_validate()` — broke the type-safety chain at the exact point it matters most
- Created a "pure" function that took and returned `dict[str, Any]` — a pure function with `Any` is nonsensical
- Entangled the four input axes by putting content decisions in the data model — destroying the benchmarking matrix that is galdr's entire purpose
- Wrote per-section composer code twice — once as OOP classes, once as per-section functions — when the engine is generic by design

None of them felt uncertain while doing it.

---

## You Will Get These Things Wrong

### Entangling the Four Axes
**Detection:** If you find yourself putting a heading string, a list format choice, or a visibility toggle inside the data model... or reading a structure toggle from the content config... or anything that makes one axis depend on another...
**Why it's wrong:** Galdr exists to multiply one agent definition across content × structure × display variants for benchmarking. If axes are entangled, swapping one changes the others. The benchmarking matrix collapses.
**Recovery:** Re-read `redesign/FOUR_AXIS_SPEC.md` — the four-axis section defines the boundaries.

### Putting IO in Python Code
**Detection:** If you find `Path.read_text()`, `open()`, `write()`, or any filesystem access in logic code...
**Why it's wrong:** Gates own all file IO. Python between gates transforms typed data and nothing else. Treat this as an obligation you maintain rather than a guarantee you inherit — `open()` still exists in every namespace, and there is a known standing violation in the output path that is not a pattern to copy.
**Recovery:** `context/NORNIR_GATES_ELEMENT.md` for what a gate is and the four call patterns; then the gate wrappers in regin's `logic/impure/`, which are the reference this project follows.

### Writing a Module Without Reading Its Reference Implementation
**Detection:** If you're writing a module without first re-reading the specific draupnir/regin pattern for what you're building — a gate wrapper, a transform, an orchestrate wiring...
**Why it's wrong:** Regin and draupnir are working implementations of this architecture. The equivalent of what you're building almost certainly exists in one of them, already correct. Matching a working reference is faster than converging on one through feedback.
**Recovery:** Before writing ANY module, find the equivalent pattern in draupnir or regin. Read it. Match it.

### Using isinstance for Type Safety in the Pure Zone
**Detection:** If you're writing `isinstance(field_value, RootModel)` or `isinstance(x, str)` to determine what type a value is...
**Why it's wrong:** Inside the sandbox, all types are known by construction. Gates validated everything. The schema metadata (`model_fields[name].annotation`) tells you the type without runtime checks. Runtime isinstance for type safety is re-securing an already-secured boundary.
**Recovery:** Use Pydantic model introspection (field annotations) for type information. Write specific functions for known types instead of generic dispatchers.

### Modifying Generated Files
**Detection:** If you open any file in `structure/gen/` to edit it...
**Why it's wrong:** Files in `structure/gen/` are generated by `generate_structures.py` from JSON Schemas. Manual edits are silently overwritten on next generation.
**Recovery:** Change source → run draupnir → run `generate_structures.py`.

### Writing Per-Section Code
**Detection:** If you're creating `compose_identity()`, `render_constraints()`, or ANY function named after a specific section...
**Why it's wrong:** The engine is GENERIC. One `compose_section()` processes all sections. Section-specific knowledge lives in the models and TOML, not in code. Field-name suffixes encode position; trunk matching links content to data. There is no per-section code. This mistake has been made twice before — once with OOP classes, once with per-section composer functions.
**Recovery:** Re-read `redesign/COMPOSITION_ENGINE_DESIGN.md` — especially "Core Principle."

### Recovering Deleted Code to Learn From It
**Detection:** If you reach for `git show`, `git log -S`, or a branch to recover the old walker-based composition, the `archive/` directory, or any deleted implementation — to see "how it was done."
**Why it's wrong:** Whatever is missing was deleted deliberately, not lost. Code you know is wrong still pulls you toward it, and reading it "just for reference" is the mechanism by which a scrapped design comes back. Anything worth keeping from it was extracted before the deletion.
**Recovery:** `context/GALDR_ELEMENT.md` for what exists now and why the removed things were removed; `context/GALDR_CHALLENGES.md` § *Design rules the rest of this document assumes* for what was kept from them.

### Auditing One Naming Aspect at a Time
**Detection:** If a naming audit checks positional suffixes but not trunk alignment, or trunk alignment but not placeholder matching.
**Why it's wrong:** The engine reads field names mechanically — suffix, trunk and placeholder each drive a different mechanism. Wrong names cause wrong *rendering*, not wrong style, and every one of them fails open and silent. All three conventions must hold at once; past audits each fixed one and declared success with the other two still broken.
**Recovery:** `redesign/TOML_ARCHITECTURE.md` for what the names mean, and `context/GALDR_ELEMENT.md` for how the three conventions differ — note that placeholders do *not* all resolve to data fields, so "matches a data field" is the wrong test for that third one.

### Prototyping in /tmp
**Detection:** If you reach for `Write` with a `/tmp/*.py` path for an inspection or experiment script.
**Why it's wrong:** `/tmp/` scripts evaporate on session end/compaction. A full session of prototyping was lost this way — git had nothing, and it was unrecoverable. `/tmp/` is only for destination output files, never for source/work.
**Recovery:** Put experimental/inspection code in the project — `probe/` exists for exactly this. "Wire in" means wire into the real tree, not a scratch script.

### Analyzing Cross-Axis Alignment in Isolation
**Detection:** If you analyze data/content/structure/display alignment alone and present conclusions instead of the raw interleaved mapping.
**Why it's wrong:** The user designed the patterns across axes and needs to SEE the actual data interleaved per section to find where patterns hold and where they break. The fix for a break is usually a schema/naming change to complete the pattern — NOT engine code to work around it. ~20 hours were wasted declaring patterns "complete" without showing the user the data.
**Recovery:** Always produce interleaved views (data + content + structure + display together, per section), present them, and let the user identify patterns and breaks. Reshape data, then write a simple engine — don't write a complex engine for messy data.

---
