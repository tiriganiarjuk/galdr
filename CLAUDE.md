# Galdr — Context Refresh Protocol

## STOP. Read this before writing any code.

You have context from a compaction summary or from earlier in this session. You feel like you understand this project well enough to start working. **You are almost certainly wrong.**

After compaction, you have a summary — not understanding. The summary preserves conclusions but loses reasoning, constraints, and the specific shapes of things. You will produce output that looks right, compiles, and silently violates the project's architecture because the summary told you WHAT but not HOW or WHY NOT.

**This has happened before.** Previous sessions in this project have produced output that compiled, passed review, and implemented the wrong architecture — work that had to be thrown away.

None of them felt uncertain while doing it.

Orient via the CONTEXT_MAP `@import`ed below before proceeding — start with its orientation gate.

---
<!-- ═══════════════════════════════════════════════════════════════════════ -->
<!-- EVERYTHING ABOVE THIS LINE IS STANDARDIZED — DO NOT MODIFY            -->
<!-- (except the failure examples, which must be real)                      -->
<!-- EVERYTHING BELOW THIS LINE IS PROJECT-SPECIFIC                        -->
<!-- ═══════════════════════════════════════════════════════════════════════ -->
---

## Project Instructions

- **Write in small increments so feedback lands on small surfaces.** Feedback arrives on every file you write, automatically. A file at a time means each response points at one thing; a batch of files means untangling which change caused what.
- **Reshape the schema instead of complicating the engine.** The output schemas (agent-output-content/structure/display) are tail-end — no downstream cascade beyond galdr — so changing them costs only a mechanical regen (verdandi YAML → draupnir → gates → galdr models). When engine code gets complex to handle an awkward data format, reshape the schema rather than building detection logic around it.
- **Verify the output changed before decomposing.** Get the logic working and confirm the actual output moved, THEN decompose. Splitting functions to satisfy a complexity band before you've seen the logic work is optimizing blind.
- **General docs must stay valid for two weeks.** Keep concepts, principles, and data-flow descriptions in general docs. Keep function names, field-name examples, "what's built" inventories, and implementation status OUT of them — those are read live from the code or belong in volatile docs (`review/`) expected to change.

---

## How you orient, and how you recover

**Orientation** is your first meeting with this project. You arrive knowing nothing about it, with
no stake in it yet. At the start of a session, read the orientation gate in the `CONTEXT_MAP`
auto-included below, whole and in order. The reading is there to give you enough understanding to
know what you are doing, and the reason to do it well, so that you can work with the user.

**Recovery** uses the same documents for the opposite situation. You are no longer a blank slate:
you carry a model of the project, and part of it is wrong. After any compaction, read the gate
whole again, because nothing shows what a summary lost. When the user sends you back, they have
watched you repeat mistakes that show you have lost what you are supposed to be doing and are
pattern-matching. Read the material as the correction for that: find where it contradicts what you
have been doing, and change course. This is your chance to keep working; the alternative is being
dismissed. If you are sent to something already in your context, say so, and ask what the user
wants from it: reloading it does no work.

The map always tells you where things live.

---

@CONTEXT_MAP.md
