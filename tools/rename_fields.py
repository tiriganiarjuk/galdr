#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pydantic>=2.0",
# ]
# ///
"""Rename control-surface fields across Verdandi and Galdr from one map.

A field's name appears in several places, and a rename that misses one breaks
a link silently. This tool takes a single rename map and rewrites every place:

  verdandi agent-output shallowsections   the key, and any `only_when: field:`
                                           naming it as a sibling
  verdandi agent-output definition files   renamed so the file name equals the
                                           key it defines
  galdr/extracted/*.toml                   the key, sub-table headers, and
                                           mentions in comments of that table

It never touches values. Placeholders name data fields, and data is not renamed.

A map is TOML, one table per section, `old = "new"`:

    [critical_rules]
    fail_fast_body = "critical_rules_fail_fast_body"

Usage:
    tools/rename_fields.py --generate-domain-map tools/rename_maps/01_domain_prefix.toml
    tools/rename_fields.py tools/rename_maps/01_domain_prefix.toml            # dry run
    tools/rename_fields.py tools/rename_maps/01_domain_prefix.toml --apply

The domain map is generated once. Generation is not idempotent — run it against
a renamed tree and it prefixes again. Applying a map is idempotent: names it
cannot find are already renamed.

Why the domain prefix exists. The section prefix was in the names from the
start — every definition file is `{section}_{key}`. The engine works on the
short name, and that is correct; the keys were shortened too early, at
authoring time instead of at the engine boundary. That gave the engine nothing
it lacked and took the namespace away from everyone reading the files — the
only word in a name that says where a control lives. So the files carry full
names and the engine's boundary (local_field_view) strips the prefix once.
"""
import re
import sys
from pathlib import Path
from typing import Annotated, Literal

import read_toml_validate_json
from pydantic import BaseModel, ConfigDict, Field, JsonValue, RootModel

VERDANDI = Path.home() / "ai" / "smidja" / "verdandi" / "agent-output" / "source"
EXTRACTED = Path.home() / "ai" / "smidja" / "galdr" / "extracted"
CONFIG_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas" / "config"
AXES = ("content", "structure", "display")


class ReaderError(BaseModel):
    """Why the TOML reader refused: the failure class and its message."""

    model_config = ConfigDict(frozen=True)

    type: str
    message: str


class ReaderSuccess(BaseModel):
    """The file was read and matches its schema; `data` is the validated JSON."""

    model_config = ConfigDict(frozen=True)

    ok: Literal[True]
    data: str
    error: None


class ReaderRefusal(BaseModel):
    """The read was refused; `error` says in which class and why."""

    model_config = ConfigDict(frozen=True)

    ok: Literal[False]
    data: None
    error: ReaderError


class ReaderResult(RootModel[Annotated[ReaderSuccess | ReaderRefusal, Field(discriminator="ok")]]):
    """What read_toml_validate_json.read() returns: one of two outcomes."""


class RenameMap(RootModel[dict[str, dict[str, str]]]):
    """{section: {old: new}} — schemas/config/rename-map.schema.json."""


class SurfaceTables(RootModel[dict[str, dict[str, JsonValue]]]):
    """{section: {key: value}} — schemas/config/control-surface-tables.schema.json."""


def read_toml(path, schema_name):
    """Validated JSON for one TOML file, or exit with the reader's refusal."""
    outcome = ReaderResult.model_validate(
        read_toml_validate_json.read(str(path), schema_name, str(CONFIG_SCHEMA_DIR))).root
    if isinstance(outcome, ReaderRefusal):
        raise SystemExit(f"{outcome.error.type}\n{outcome.error.message}")
    return outcome.data

KEY_LINE = re.compile(r"^(    )([a-z][a-z0-9_]*):(.*)$")
REF_LINE = re.compile(r"^(\s+ref:\s*)([a-z]+)/([a-z][a-z0-9_]*)\s*$")
ONLY_WHEN = re.compile(r"^(\s+field:\s*)([a-z][a-z0-9_]*)\s*$")
INLINE_REF = re.compile(r"^\s*([a-z]+)/([a-z][a-z0-9_]*)\s*$")
TABLE_HEADER = re.compile(r"^\[([a-z_][a-z0-9_]*)(?:\.([a-z_][a-z0-9_]*))?\]\s*$")
TOML_KEY = re.compile(r"^([a-z][a-z0-9_]*)(\s*=.*)$")
RENAMEABLE_KINDS = ("field", "simplegroup")


def section_files():
    """{(section, axis): shallowsection path}, read from the schema assembly."""
    section_paths = {}
    for axis in AXES:
        text = (VERDANDI / "schema" / f"agent-output-{axis}.yaml").read_text()
        for section, stem in re.findall(r"^\s+([a-z_]+):\s*shallowsection/([a-z0-9_]+)\s*$",
                                        text, re.MULTILINE):
            section_paths[(section, axis)] = VERDANDI / "shallowsection" / f"{stem}.yaml"
    return section_paths


def declared_keys(path):
    """[(key, kind, ref_stem)] for every key a shallowsection declares."""
    lines = path.read_text().splitlines()
    found = []
    for index, line in enumerate(lines):
        match = KEY_LINE.match(line)
        if not match:
            continue
        field_key, rest = match.group(2), match.group(3)
        inline = INLINE_REF.match(rest)
        if inline:
            found.append((field_key, inline.group(1), inline.group(2)))
            continue
        for follow in lines[index + 1:index + 4]:
            ref_match = REF_LINE.match(follow)
            if ref_match:
                found.append((field_key, ref_match.group(2), ref_match.group(3)))
                break
    return found


def generate_domain_map(out_path):
    """Every key becomes `{section}_{key}`. Written as a reviewable map."""
    by_section = {}
    for (section, _), path in section_files().items():
        for field_key, _, _ in declared_keys(path):
            by_section.setdefault(section, {})[field_key] = f"{section}_{field_key}"
    lines = ["# Step 1 — domain prefix. Generated by tools/rename_fields.py.",
             "# Every key becomes {section}_{key}. Generate once; see the tool's docstring.",
             ""]
    for section in sorted(by_section):
        lines.append(f"[{section}]")
        lines += [f'{old_name} = "{new_name}"'
                  for old_name, new_name in sorted(by_section[section].items())]
        lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines))
    total = sum(len(section_table) for section_table in by_section.values())
    sys.stdout.write(f"wrote {out_path}: {total} keys across {len(by_section)} sections\n")


def plan_file_renames(rename_map):
    """Definition files whose name will not equal their new key."""
    renames, exceptions = [], []
    for (section, _), path in section_files().items():
        table = rename_map.get(section, {})
        for field_key, kind, stem in declared_keys(path):
            new_key = table.get(field_key)
            if new_key is None or stem == new_key:
                continue
            if kind not in RENAMEABLE_KINDS:
                exceptions.append(
                    f"{section}.{field_key}: {kind}/{stem} is a shared type, not renamed")
                continue
            renames.append((kind, stem, new_key))
    return renames, exceptions


def rewrite_shallowsection(path, table, file_renames):
    """New text for one shallowsection, and how many lines changed."""
    stems = {(kind, old_stem): new_stem for kind, old_stem, new_stem in file_renames}
    rewritten, changed = [], 0
    for line in path.read_text().splitlines():
        new_line = line
        key_match = KEY_LINE.match(line)
        if key_match and key_match.group(2) in table:
            new_line = f"{key_match.group(1)}{table[key_match.group(2)]}:{key_match.group(3)}"
            inline = INLINE_REF.match(key_match.group(3))
            if inline and (inline.group(1), inline.group(2)) in stems:
                new_line = (f"{key_match.group(1)}{table[key_match.group(2)]}: "
                            f"{inline.group(1)}/{stems[(inline.group(1), inline.group(2))]}")
        ref_match = REF_LINE.match(line)
        if ref_match and (ref_match.group(2), ref_match.group(3)) in stems:
            new_line = (f"{ref_match.group(1)}{ref_match.group(2)}/"
                        f"{stems[(ref_match.group(2), ref_match.group(3))]}")
        sibling = ONLY_WHEN.match(line)
        if sibling and sibling.group(2) in table:
            new_line = f"{sibling.group(1)}{table[sibling.group(2)]}"
        changed += new_line != line
        rewritten.append(new_line)
    return "\n".join(rewritten) + "\n", changed


def rewrite_comment(comment, table):
    """Rename whole-word field mentions in a comment, leaving other words."""
    pieces, position = [], 0
    for match in re.finditer(r"\b[a-z][a-z0-9_]*\b", comment):
        pieces.append(comment[position:match.start()])
        pieces.append(table.get(match.group(0), match.group(0)))
        position = match.end()
    pieces.append(comment[position:])
    return "".join(pieces)


def rewrite_toml(path, rename_map):
    """New text for one control surface, and how many lines changed."""
    rewritten, changed, table = [], 0, {}
    for line in path.read_text().splitlines():
        new_line = line
        header = TABLE_HEADER.match(line)
        if header:
            table = rename_map.get(header.group(1), {})
            if header.group(2) and header.group(2) in table:
                new_line = f"[{header.group(1)}.{table[header.group(2)]}]"
        else:
            body, separator, comment = line.partition("#")
            key_match = TOML_KEY.match(body)
            if key_match and key_match.group(1) in table:
                body = f"{table[key_match.group(1)]}{key_match.group(2)}"
            if separator:
                comment = rewrite_comment(comment, table)
            new_line = f"{body}{separator}{comment}"
        changed += new_line != line
        rewritten.append(new_line)
    return "\n".join(rewritten) + "\n", changed


def collisions(rename_map):
    """A new name that equals some other old name in the same section."""
    found = []
    for section, table in rename_map.items():
        unchanged = {old_name for old_name, new_name in table.items() if old_name == new_name}
        clash = set(table.values()) & (set(table) - unchanged)
        found += [f"{section}: {name}" for name in sorted(clash)]
    return found


def verify(rename_map):
    """After applying: every ref resolves, every TOML key is declared."""
    problems = []
    declared = {}
    for (section, axis), path in section_files().items():
        for field_key, kind, stem in declared_keys(path):
            declared.setdefault((section, axis), set()).add(field_key)
            if not (VERDANDI / kind / f"{stem}.yaml").exists():
                problems.append(f"{path.name}: {field_key} -> {kind}/{stem} does not exist")
    for axis in AXES:
        tables = SurfaceTables.model_validate_json(
            read_toml(EXTRACTED / f"{axis}.toml", "control-surface-tables")).root
        for section, body in tables.items():
            known = declared.get((section, axis), set())
            problems += [f"{axis}.toml [{section}] {field_key} is not declared"
                         for field_key in body if field_key not in known]
    stale = [old_name for table in rename_map.values()
             for old_name, new_name in table.items() if old_name != new_name]
    for axis in AXES:
        text = (EXTRACTED / f"{axis}.toml").read_text()
        problems += [f"{axis}.toml still has key {old_name}" for old_name in stale
                     if re.search(rf"^{old_name}\s*=", text, re.MULTILINE)]
    return problems


def report(*lines):
    """Write the tool's report lines to stdout."""
    sys.stdout.write("\n".join(lines) + "\n")


def main(argv):
    if len(argv) == 3 and argv[1] == "--generate-domain-map":
        generate_domain_map(Path(argv[2]))
        return 0
    if len(argv) not in (2, 3):
        report(__doc__)
        return 2
    rename_map = RenameMap.model_validate_json(read_toml(Path(argv[1]), "rename-map")).root
    apply = len(argv) == 3 and argv[2] == "--apply"

    clash = collisions(rename_map)
    if clash:
        report("ABORT — new names collide with existing ones:" + "".join(
            f"\n  {name}" for name in clash))
        return 1
    file_renames, exceptions = plan_file_renames(rename_map)
    for kind, old_stem, new_stem in file_renames:
        if (VERDANDI / kind / f"{new_stem}.yaml").exists():
            report(f"ABORT — {kind}/{new_stem}.yaml already exists")
            return 1

    writes = []
    for (section, _), path in section_files().items():
        text, changed = rewrite_shallowsection(path, rename_map.get(section, {}), file_renames)
        if changed:
            writes.append((path, text, changed))
    for axis in AXES:
        path = EXTRACTED / f"{axis}.toml"
        text, changed = rewrite_toml(path, rename_map)
        if changed:
            writes.append((path, text, changed))

    report(f"{'APPLY' if apply else 'DRY RUN'}")
    for path, _, changed in writes:
        report(f"  {changed:>4} lines  {path}")
    for kind, old_stem, new_stem in file_renames:
        report(f"  rename    {kind}/{old_stem}.yaml -> {kind}/{new_stem}.yaml")
    for note in exceptions:
        report(f"  kept      {note}")
    if not apply:
        return 0

    for path, text, _ in writes:
        path.write_text(text)
    for kind, old_stem, new_stem in file_renames:
        (VERDANDI / kind / f"{old_stem}.yaml").rename(VERDANDI / kind / f"{new_stem}.yaml")
    problems = verify(rename_map)
    if problems:
        report(f"\nVERIFY FAILED — {len(problems)} problems:" + "".join(
            f"\n  {problem}" for problem in problems[:40]))
        return 1
    report("\nverified: every reference resolves, every TOML key is declared")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
