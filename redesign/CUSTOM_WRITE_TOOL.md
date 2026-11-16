# Custom Write Tools

How an agent's output tool gets from its definition into its prompt.

## Overview

Agents that produce structured output (JSON or JSONL) don't use generic file writes. They use **enforcement output tools** — purpose-built Nornir writer binaries, each fixed at compile time to one schema, one format and one destination, validating every write before it reaches disk.

This document follows the tool through the agent pipeline:

1. **Agent definition** — declares what output tool it needs
2. **Regin discovery** — matches that declaration against the deployed writers
3. **The prompt** — the matched tool's invocation arrives in Galdr's data

How a writer is built, generated and deployed is Nornir's own subject, and its documents are the home for it:

| Need | Read |
|------|------|
| how any Nornir tool is made, and why constraints are fixed in | `~/ai/smidja/nornir/HOW_A_NORNIR_TOOL_IS_MADE.md` |
| the contracts a tool exposes (CLI, PyO3, failure classes) | `~/ai/smidja/nornir/MUST_READ_BEFORE_BUILDING.md` § Approved interfaces |
| writer and store composition, naming, adding a writer | `~/ai/smidja/nornir/NORNIR_CONVENTIONS.md` § Naming, § Writers |
| generating a writer crate | `~/ai/smidja/nornir/generate_writer.py` (its docstring is the usage) |

## The Demand Signal

The agent definition's task-processing and security declarations together produce an `enforcement_output_tool` group, assembled by Regin's security resolver. Its definition is Verdandi's, and that file is the authority for the fields and their conditions: `~/ai/smidja/verdandi/agent-builder/source/group/enforcement_output_tool.yaml`.

Every field in the group is conditional:

| Field | Present when |
|-------|--------------|
| `output_tool_format` | the definition declares an output file format |
| `output_tool_write_frequency` | the format is `jsonl` |
| `output_tool_batch_size` | the write frequency is `batch` |
| `output_tool_schema_path` | the format is `jsonl` or `json` |
| `output_tool_file_path` | `task.processing.output_file_name_known` is `known` |
| `output_tool_directory_path` | it is `partially` or `unknown` |
| `output_tool_name_needed` | it is `partially` or `unknown` |
| `output_tool_name_pattern` | it is `partially` |

So the filename the definition knows decides the shape:

- `known` — a `file_path`; the full path is fixed at definition time
- `partially` — a `directory_path` and a `name_pattern`; the agent provides the prefix or stem
- `unknown` — a `directory_path`; the agent provides the full filename

## The Tool Registry

`~/ai/smidja/nornir/tool_registry.toml` is the inventory of deployed writers. It lives in Nornir because the binaries do. Regin reads it through `read_toml_validate_json`, against `nornir/schemas/tools/tool-registry.schema.json`.

```toml
[[tools]]
binary_name = "append_truth_qc_report_record"
invocation = "append_truth_qc_report_record <<'EOF'\n{json_data}\nEOF"
output_format = "jsonl"
write_frequency = "record"
output_path_kind = "fixed_file"
schema_path = "spaces/bragi/schemas/qc-report.schema.json"
file_path = "spaces/bragi/truth/qc_semantic_report.jsonl"
```

| Field | Present | Purpose |
|-------|---------|---------|
| `binary_name` | always | Name of the deployed binary |
| `invocation` | always | Canonical invocation pattern — the one statement of how to call this binary |
| `output_format` | always | `jsonl` or `json` |
| `write_frequency` | always | `record` or `batch` |
| `output_path_kind` | always | `fixed_file`, `directory_name`, or `directory_prefix` |
| `schema_path` | always | The `.schema.json` file the writer embeds |
| `file_path` | `fixed_file` only | The output file |
| `directory_path` | directory kinds | The output directory |
| `name_extension` | `directory_name` | File extension without dot (e.g., `json`) |
| `name_suffix` | `directory_prefix` | File suffix including dots (e.g., `.summaries.jsonl`) |

Paths are relative to the ai root (`~/ai`).

The `invocation` field is written by `generate_writer.py` when the crate is created and read through unchanged by Regin. Two forms:

- `fixed_file`: `binary_name <<'EOF'\n{json_data}\nEOF`
- `directory_name` / `directory_prefix`: `binary_name {name} <<'EOF'\n{json_data}\nEOF`

The path kind decides what the agent supplies at run time:

| Kind | The writer fixes | The agent provides | Written to |
|------|------------------|--------------------|------------|
| `fixed_file` | the whole path | nothing | the file |
| `directory_name` | directory + extension | filename stem | `{dir}/{stem}.{ext}` |
| `directory_prefix` | directory + suffix | prefix | `{dir}/{prefix}{suffix}` |

The component the agent provides is checked as a plain name before any path is built, so it cannot leave the directory.

## Tool Discovery (Regin Level 8)

`discover_tool` (`regin/logic/pure/tool_resolve/composed.py`) matches the agent's output spec against the registry, entry by entry; the first match wins. A match requires the output format to be equal, and each of these to be equal wherever the spec states it:

1. `write_frequency`
2. `schema_path`
3. `file_path`
4. `directory_path`

A field the spec leaves out matches any entry.

**Two outcomes:**

- **Match** — a `ResolvedTool`: the binary name, the invocation variant (`no-name` for `fixed_file`, `with-name` otherwise), and the registry's `invocation` string.
- **`None`** — the agent declared no output tool, or no registry entry matched. Either way the agent is built as one with no output tool. `context/NORNIR_GATES_ELEMENT.md` § The Regin side, and where it stops, covers what follows from that.

## What the Agent Is Given

The matched tool reaches Galdr as data: `writing_output` carries the invocation, `critical_rules` the tool name, and the frontmatter the hook and tool allowlist that hold the agent to it.

**Fixed file (no name needed):**
```bash
append_embedding_normalize_batch_20 <<'EOF'
{"uid":"...","description":"..."}
EOF
```

**Directory output (name needed):**
```bash
append_interview_summaries_record my-interview-id <<'EOF'
{"uid":"...","summary":"..."}
EOF
```

The binary handles everything else — the agent never constructs a file path.

**What comes back.** A writer answers under Nornir's CLI contract:

| Outcome | stdout | stderr | exit code |
|---------|--------|--------|-----------|
| written | the receipt | nothing | 0 |
| refused or failed; nothing is written | nothing | first line: the failure class; then the message, which says what to do next | 1 |
| wrong arguments | nothing | the usage | 2 |

The receipt is one line of JSON: `{"written": 1}`, and for a writer that stamps fields the agent may not supply, also the last record's stamps under the writer's own field names — `{"written": 3, "last_record_stamps": {"exchange": 43, …}}`. Its schema is `~/ai/smidja/nornir/schemas/tools/write-receipt.schema.json`.

`binary_name --help` prints the writer's fixed configuration and this contract; `--dump-schema` prints its embedded schema.

## End-to-End Flow

```
Agent definition TOML
    │
    ▼
Regin levels 1-7 (resolve paths, permissions, merge, regroup)
    │
    ▼
Regin level 8: discover_tool against nornir/tool_registry.toml
    │
    ├─ match → ResolvedTool (binary name, invocation)
    │       │
    │       ▼
    │   the Anthropic render carries:
    │     - writing_output (invocation pattern for the agent)
    │     - critical_rules (workspace path, tool name)
    │     - frontmatter.hooks (Bash hook validates tool usage)
    │     - frontmatter.tools (tool allowlist)
    │       │
    │       ▼
    │   Galdr composes the prompt's writing_output section from that data
    │       │
    │       ▼
    │   the agent calls: binary_name [name] <<'EOF'
    │
    └─ None → the agent is built with no output tool
            │
            ▼
        a writer for it is made in Nornir (generate_writer.py, registry entry,
        nornir_deploy --build writers), and Regin is run again
```
