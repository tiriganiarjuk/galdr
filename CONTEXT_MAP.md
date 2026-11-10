<!-- ═══════════════════════════════════════════════════════════════════════ -->
<!-- DO NOT EDIT THIS BLOCK. Before editing ANY part of this file, you MUST  -->
<!-- first read /Users/johnny/ai/CONTEXT_MANAGEMENT_SYSTEM.md — it defines  -->
<!-- what this file is for and what may NOT go in it.                        -->
<!--                                                                          -->
<!-- This file is a MAP (a router), not a source. Its only job is to tell    -->
<!-- you WHERE the context lives — it never holds the context, state, or     -->
<!-- progress itself. Reading this map does NOT orient you; you are NOT      -->
<!-- oriented until you have read the Orientation-gate docs it points to, in -->
<!-- the order given.                                                         -->
<!--                                                                          -->
<!-- THE WHITELIST RULE: if a doc is not in this map, it is not for           -->
<!-- orientation — do not read it. A stale doc is UNLINKED or DELETED, never -->
<!-- flagged in place. No freshness tags. No "do-not" guards. No state.       -->
<!-- Behavioral rules live in CLAUDE.md, not here.                            -->
<!--                                                                          -->
<!-- This file is LOW-CHURN. It changes only when how-to-get-oriented        -->
<!-- changes — i.e. a doc is added or removed. It is not a worklog and is    -->
<!-- not regenerated per session.                                            -->
<!-- ═══════════════════════════════════════════════════════════════════════ -->

# CONTEXT_MAP — Galdr

## Purpose

Galdr is the composition engine — the final stage of the agent pipeline (Verdandi → Draupnir → Nornir → Regin → **Galdr**): it combines one gate-validated agent data model with three independently swappable control surfaces (structure, content, display) into deployable agent prompts.

---

## Orientation gate — read these, in this order, to be oriented

> Start with `context/`. It answers *why this system exists* — which is the one thing that
> cannot be recovered from the tree, and the thing every previous session got wrong by
> inferring it from the structure. Read the map, then the element document for wherever you
> are working. Everything after it will land differently.

1. `context/AGENT_BUILD_SYSTEM.md` — the pipeline-wide map: what the whole system is for, why determinism is the goal, and the double gate that makes LLM-written transformation safe. Wikilinked to the five element documents; follow them as needed.
2. `context/GALDR_ELEMENT.md` — Galdr itself: the four axes, the invariance test that decides where a field belongs, how names carry the mechanism, and **what of the engine actually exists today** (stage 1; stages 2–4 are not built).
> The next one is the frame for everything that follows. The names will look inconsistent to
> you; that look is the mechanism. Read it before you form any opinion about a field name.
3. `redesign/08_NAMING_REQUIREMENTS.md` — the names are the engine: how a control name is peeled, layer by layer, into where it lives, what lever it is, what the waist must do to it, where it renders and which data it decorates. Ends in its own proof.
4. `context/GALDR_CHALLENGES.md` — volatile companion. Its C, D and E sections are *requirements for the unbuilt waist*, not a bug list; A, B, F and G are live. Its own header says how to read it — do not skip that.
5. `redesign/FOUR_AXIS_SPEC.md` — the four-axis model and the benchmarking matrix: what each axis contains, and why entangling any two of them destroys the product.
6. `redesign/COMPOSITION_ENGINE_DESIGN.md` — the generic engine: one `compose_section()` for all sections, buffer slots, data gates, zero per-section code.
7. `redesign/01_PROCESSING_FLOW.md` — the four-stage pipeline (chunk, gather, resolve+render, buffer) and why each stage shrinks the problem.
8. `redesign/TOML_ARCHITECTURE.md` — the naming law: positional suffixes, field interface patterns, threshold types, section categories. The engine reads names mechanically; this doc is the authority on what names mean.
> The next four are read by you, personally, in this context — never delegated
> to a subagent, never absorbed via a summary.

9. `WHY_THIS_FEELS_WRONG.md` — the frame: what this environment is, and why it
   will feel over-constrained until you understand it
10. `EVERY_CHECK_IS_A_PROXY.md` — why the feedback steers where it steers; what
   each constraint is a proxy for. Read before doc 11, so the level system reads
   as engineering rather than as limits.
11. `THE_LEVEL_SYSTEM.md` — zones, levels, and the decision procedure for where
   every piece of code lives. Prerequisite to writing anything.
12. `HOW_DATA_ENTERS.md` — the boundary: how external data becomes typed, and
   why unknown data never gets in. Prerequisite to reading any file.

**Proof:** before writing anything: (a) state three project-specific constraints
that diverge from how you'd normally do this work, with reasons; (b) from the
four environment docs, state the one item you found most interesting, the one
that most surprised you, and the one you are most eager to put into practice —
chosen by you, in your own words. Generic acknowledgment means you are not
oriented — go back and read.

---

## Refresh guide — want X → read Y

| Need | Read |
|------|------|
| why any of this exists / what a stage is for | `context/AGENT_BUILD_SYSTEM.md` and the element doc for that stage |
| what an upstream stage does and why | `context/{VERDANDI,DRAUPNIR,NORNIR_GATES,REGIN}_ELEMENT.md` |
| what of the engine is actually built | `context/GALDR_ELEMENT.md` § What exists today |
| where does this function go / what zone / what level | `THE_LEVEL_SYSTEM.md` |
| how external data becomes typed / a shape has no model | `HOW_DATA_ENTERS.md` |
| bundle container design | `redesign/02_INTERMEDIATE_CONTAINER.md` |
| chunking / slot assignment | `redesign/03_CHUNKING.md` |
| hourglass resolver (visibility, variants, interpolation, suppress-on-incomplete) | `redesign/04_HOURGLASS_RESOLVER.md` |
| body ordering (data drives, decorations, standalone content) | `redesign/05_BODY_ORDERING.md` |
| renderer set / data shape detection | `redesign/06_RENDERER_TYPES.md` |
| how a name resolves: peel, shape, partners, trunk matching | `redesign/08_NAMING_REQUIREMENTS.md` |
| enforcement output tools, end to end | `redesign/CUSTOM_WRITE_TOOL.md` |
| per-section four-axis field inventory | `review/{SECTION}.md` |
| bundle snapshot + probes | `review/BUNDLE_INSPECTION.md`, `probe/*.py` |
| data / content / structure / display model shapes | `src/galdr/structure/gen/*.py` |
| the live control-surface TOMLs | `extracted/content.toml`, `extracted/structure.toml`, `extracted/display.toml` |
| how to run | `src/galdr/cli.py` — the CLI is the truth; `uv run galdr --help` |
| a live data input to run against | produced by regin, in bragi: `~/ai/spaces/bragi/definitions/agents/{name}/anthropic_render.toml` |
| gate pattern / orchestrate wiring reference | `~/ai/smidja/regin/src/regin/logic/` |
| level progression reference | `~/ai/smidja/draupnir/src/draupnir/logic/` |
| current state | read live: the code + `git log`. Nothing is stored. |
| what is left to do | `TODO.md` — forward-only; finished items are deleted |
