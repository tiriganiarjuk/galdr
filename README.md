# Galdr

Composition engine for the agent definition pipeline. Transforms gate-validated agent data into deployable artifacts across independently swappable configuration axes — enabling systematic benchmarking of agent configurations from a single source definition.

**Final stage of the agent definition pipeline:** [Verdandi](https://github.com/tiriganiarjuk/verdandi) → [Draupnir](https://github.com/tiriganiarjuk/draupnir) → [Nornir](https://github.com/tiriganiarjuk/nornir) Gates → [Regin](https://github.com/tiriganiarjuk/regin) → Galdr

## Status

Galdr is being rearchitected to production standard. The architecture and design documents in `redesign/` are current. The source code is mid-build. This repository is published because the architectural approach is the important contribution — the four-axis independence, the benchmarking matrix, and the composition model are what make auditable agent deployment possible.

## Why This Matters

The agent definition pipeline produces validated, gate-enforced agent data. But the last step — turning that data into a deployable prompt — is where auditability either holds or collapses. If the composition step entangles what the agent *does* with how the output *looks*, you cannot systematically compare configurations. You cannot prove that two agents differ in exactly one variable. You cannot benchmark.

Galdr exists to ensure that the final output step preserves the determinism and auditability that the pipeline enforces at every prior stage.

## The Four-Axis Architecture

Galdr separates its inputs into four strictly independent axes:

- **Data** — from the pipeline (gate-validated, frozen). What the agent *is*. This axis is not authored in Galdr — it arrives as validated TOML from Regin.
- **Structure** — which sections appear, in what order, with what visibility. The *skeleton* of the output.
- **Content/Style** — labels, prose, section headings, template wording. The *voice* of the output.
- **Display** — formatting choices: markdown heading levels, list styles, separator patterns. The *appearance* of the output.

**These axes must never entangle.** If a structure decision depends on a content value, or a display choice requires knowing the data, the benchmarking matrix collapses. One agent definition multiplied across N content styles × M structure variants × K display formats should produce N × M × K independently valid agent configurations — each differing in exactly the variables that were changed.

This is what makes systematic agent evaluation possible: generate fifty variants from one definition, benchmark them against a test suite, and know exactly which configuration variable produced which performance difference. The axes are the mechanism that makes this tractable.

## Composition, Not Templating

Galdr does not use templates. Early iterations used Jinja2 and the result was a system where data and presentation were inseparable — a template encodes structure, content, and display decisions in a single artifact, making independent variation impossible.

The current architecture uses a recipe-based composition model. Fourteen data sections map one-to-one to recipe modules. Each recipe receives validated data and the three configuration axes as independent inputs, and produces a rendered section. The composition engine assembles sections according to the structure axis. No recipe knows about any other recipe. No axis knows about any other axis.

## What Galdr Produces

From a single gate-validated agent definition:

- **Agent prompt** (`.md`) — the deployable prompt document with identity, instructions, security boundaries, success criteria, and all other sections composed according to the selected configuration
- **Dispatcher skill** (`SKILL.md`) — a companion document enabling the agent to be invoked by a dispatcher or orchestration system

Both are fully determined by the four input axes. The same inputs always produce the same outputs.

## Supervision Contract Export (Projected)

As the enforcement infrastructure migrates from vendor-dependent hooks to the [Bifrost](https://github.com/tiriganiarjuk/nornir) traffic-layer proxy, Galdr will produce a third output: a **Bifrost supervision schema** derived from the same agent definition.

This schema defines the agent's behavioural boundaries, alignment signals for context management, security policy with graduated enforcement thresholds, and operational envelope metrics (API budget, request rate limits, time bounds). Because it derives from the same source definition as the agent itself, the supervision contract cannot diverge from what the agent is configured to do — deploying an agent without deploying its monitoring contract becomes structurally impossible.

The agent definition already contains the information needed to derive minimum permissions, expected operational patterns, and security boundaries. Galdr is the natural place to export this because it already has access to the fully resolved, gate-validated agent data and produces all other deployment artifacts.

## Design Documentation

The `redesign/` directory contains the current architecture:

- `FOUR_AXIS_SPEC.md` — the four-axis model, axis boundaries, benchmarking matrix
- `COMPOSITION_ENGINE_DESIGN.md` — recipe architecture, section mapping, rendering pipeline
- `01_PROCESSING_FLOW.md` through `08_NAMING_REQUIREMENTS.md` — detailed design decisions

The `review/` directory contains per-section analysis for each of the fourteen output sections.

## Licence

Copyright (c) 2025–2026 John Oker-Blom

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE](LICENSE) for the full licence text.
