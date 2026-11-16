# ATTENTION — Galdr's documents describe nornir tools that have changed

The nornir tools Galdr's documents describe now work this way
(`~/ai/smidja/nornir/HOW_A_NORNIR_TOOL_IS_MADE.md`, and the contracts in
`~/ai/smidja/nornir/MUST_READ_BEFORE_BUILDING.md` § Approved interfaces):

- **Every refusal comes from one registry**, `nornir/core/failure_mode_core/failure_modes.toml`:
  its class, what was refused and where, and a route that never leads around the constraint that
  refused.
- **Writers** (`append_*`, `write_*`) follow the CLI contract: success prints nothing and exits 0;
  a refusal exits 1 with the failure class on stderr's first line, then the message; wrong
  arguments exit 2. Stores print the stored session's id.
- **Gates are generated variants**, made from `nornir/gates/gate_recipes.toml` by
  `nornir/generate_gates.py`. Every input gate also runs from a shell: `gate_{stage}_input <file>`.
- **A schema named at call time** (the readers) and **a schema embedded in the binary** (the
  gates) are two levels of one constraint over one engine, `reader_io` with its `SchemaSource`.

## Left here

- `context/NORNIR_GATES_ELEMENT.md`: `FAIL:batch too large…` held up as the model refusal
  (:181-186); a schema named at call time called "a real inconsistency" (:132-142); "There is no
  self-service procedure" (:293-297), where the gates now have recipes.
- `context/AGENT_BUILD_SYSTEM.md`: wherever it says the same as the passages above.
- `redesign/CUSTOM_WRITE_TOOL.md`: describes the writers' output as `OK` / `FAIL:<reason>`.

Delete this file when every item above is done.
