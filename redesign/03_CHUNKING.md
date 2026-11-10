# Chunking

## What Chunking Does

Takes all four axes for one section. Sorts every field into the correct buffer slot. Gathers the associated controls for each field. Produces the intermediate container ready for resolution.

## Slot Assignment

Every content field declares its destination slot via its terminal suffix. The suffix convention is defined in `TOML_ARCHITECTURE.md`. Heading suffixes go to the heading slot, preamble suffixes to preamble, closing suffixes to closing. Everything else goes to body.

This is mechanical. Read the suffix, put it in the slot. No analysis, no heuristics.

## Two Input Streams

The body slot receives fields from two sources:

**Content fields** — walked in declaration order. Their suffix determines their slot. Body-suffix fields go to body. The rest go to their declared slot.

**Data fields** — walked in declaration order. All data fields go to body (data never appears in heading, preamble, or closing).

## Gathering

Chunking isn't just sorting — it's also gathering. For each field placed in a slot, collect everything that affects how it renders:

For a content field: find its visibility toggle in structure (if one exists). If it's a variant, find the selector value in structure. If it has display controls by trunk, collect those.

For a data field: find all content that decorates it (by trunk matching — see `08_NAMING_REQUIREMENTS.md`). Find the display format and threshold. Collect the data value itself.

The result: each entry in the intermediate container is a bundle with all its inputs gathered. Nothing left to look up during rendering.

## Body Ordering

Body has two streams that must interleave correctly:

**First: data-driven content** — in data field declaration order. Each data field produces one or more bundles: a label before, the data rendering itself, a postscript after. The data model's field order IS the body rendering order.

**Then: standalone content** — content body fields that didn't match any data field. These go at the end, in content declaration order. Examples: standalone prose rules, content with `_body` suffix, anything the trunk matching didn't consume.

Gates (boolean/enum data fields) produce no output — they're skipped. Nested models are handled by a different mechanism — also skipped.

## What Chunking Produces

An intermediate container with four arrays of bundles. Each bundle is self-contained: raw data, raw content, visibility state, variant info, display controls, shape classification. Ready for the resolver.
