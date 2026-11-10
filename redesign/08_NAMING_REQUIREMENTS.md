# The Names Are the Engine

Read this before the engine design and before any file in `extracted/` or `src/`.
It exists because the same misreading has stopped this project more than once, and
it is the misreading your training will produce first.

---

## 1. Stop here if any of this is happening

You are about to read several hundred field names across four files. They will look
like a convention applied inconsistently: one heading field is `section_start`,
another is `section_start_template`, a third is `section_start_variant_template`.
Your training will say *these are three names for the same thing, and two of them are
wrong*.

That is the trap, and it is detectable from the inside. The signs:

- You are about to say "these are different names for the same thing".
- You are about to say "this name is wrong" or "this is inconsistent" before you have
  opened the field's definition file.
- You are comparing names to each other instead of reading what each name says.
- A proposal to normalise, simplify or unify names is forming.

When any of these appears: stop, and read section 3 against the actual field. The
names here are not labels on things. They are a small language, and every part of a
name is an instruction to the engine. Two names that differ by one suffix are two
different instructions. The variation you see is the mechanism working, not a
convention slipping.

This project matches nothing in your training. Your sense that a name is odd is
information about your training, not about the name.

---

## 2. The idea, in one paragraph

There are fourteen sections and one engine. The engine never asks which section it is
in. It can do that because every control field is named by a fixed pattern, and when
the engine peels that pattern apart, layer by layer, each layer tells it one thing:
where the field lives, what kind of lever it is, what operation it needs, where it
renders, and which data it decorates. Strip the section prefix and a section-specific
name becomes a universal one. The tail of the name is a signpost pointing at the
formatting and wording that applies. Follow the signposts and everything lands in the
right slot, in the right order, with the right partners, with no per-section code.
That is the whole design. Naming is not a side concern of it; naming *is* it.

In Johnny's words (2026-10-11): *"the real trick is the abstraction itself, from tons
of disparate specific names we derive a universal shared abstraction that means we can
build one engine that can process all sections"*.

---

## 3. How a name is read

A control-surface name is peeled from the outside in. Each removal yields one fact and
a shorter name. The order is fixed.

| Step | Remove | The removed part tells you | What is left |
|---|---|---|---|
| 1 | `{section}_` prefix | Which section table and which Verdandi file. Removed exactly once, at the engine boundary. | The **universal name**: what every section calls this |
| 2 | Control suffix, if any | What kind of lever this is and which axis owns it: structure `_visible`, `_selector`, `_override`, `_auto_threshold`; display `_format`, `_format_threshold`, `_visibility_threshold`, `_activation_threshold` | The name of the **thing it governs** |
| 3 | Modifiers `_template`, `_variant` | What the waist must do to the value before it can render (section 4) | The **positional name** |
| 4 | Positional suffix | Which slot, and where within the body: `_start`, `_preamble`, `_closing` choose the slot; `_heading`, `_label`, `_declaration`, `_intro`, `_entry_template`, `_separator`, `_postscript`, `_transition`, `_body` position within the body | The **trunk** |
| 5 | Nothing | The trunk names the data field this decorates. If no data field has that name, the content stands alone and renders after the data-driven body. | |

Data field names are never peeled. They carry no prefix, no suffix, no modifier; they
are what the trunks point at. Some happen to begin with their section's name
(`input_schema`). That is coincidence, and stripping would corrupt them.

Names beginning `pre_` after step 1 are preprocessing fields. They are consumed before
any slotting, control section-level behaviour (skip the section, cap the entries, pick
a field order, force a tier) and never enter a bundle.

---

## 4. What the end of a name demands at the waist

Step 3 is where the trap in section 1 lives. The two modifiers are not type hints to
be ignored. They are the operation the resolver must perform, and they imply a partner
field. Four shapes exist. Read against the live heading fields:

| Shape | Verdandi type | The value is | The waist must | Partner |
|---|---|---|---|---|
| `…_start` | string text | one fixed heading | render as is | none |
| `…_start_template` | string template | one heading with a hole | fill the hole from the scope chain | the data or computed value the hole names |
| `…_start_variant` | group of string text | several alternative headings keyed by an enum | pick one | a structure `_selector` whose trunk this name begins with |
| `…_start_variant_template` | group of string templates | several alternatives, some with holes | pick one, then fill it | a `_selector` and the hole's value |

Live instances, one per shape: `critical_rules_section_start`,
`identity_section_start_template`, `security_boundary_framing_section_start_variant`,
`instructions_section_start_variant_template`. Four kinds of field. Same slot. Not one
thing spelled four ways.

The same four shapes recur on every positional suffix: `_preamble_variant`,
`_closing_variant_template`, `_declaration_variant_template`, `_label_template`.
The suffix says where; the modifier says what to do; together they say what the
author must write (holes, alternatives, or plain prose) and what the engine must do
with it.

---

## 5. Which partner each control finds, and how

Every control suffix names, by its remaining trunk, the thing it governs. The engine
finds that thing by name alone. There is no mapping table anywhere.

| Control, after step 1 | Finds, by its trunk | Match |
|---|---|---|
| `X_visible` | the content field `X` | exact, after modifiers are stripped from both |
| `X_selector` | every `_variant` table whose name begins with `X` | prefix: one selector may govern several tables |
| `X_format` | the data list `X` | exact |
| `X_format_threshold` | its sibling `X_format` | exact |
| `X_auto_threshold` | its sibling `X_visible` set to `"auto"` | exact |
| `X_visibility_threshold` | the content field `X`, counted against the data list `X` is tied to | exact |
| `X_override` | the data value it may substitute | exact; a base value must exist |
| content `X_label`, `X_postscript`, … | the data field `X` | exact |
| `{{hole}}` in a template | a data field, a list-item field, or an engine-computed value | by name, case-insensitive |

Two rules govern how matches are consumed. Data is exhausted: each data field is
bundled once, in declaration order, and that order is the body order. Controls are
greedy: a control field is matched into every bundle it governs, as many times as it
applies. Johnny, 2026-10-04: *"only the data sections are exhausted as they are
bundled... the other .toml fields are matched greedily to every instance that they
control"*.

---

## 6. Five walks, from the live files

Every name below was read from `extracted/` and its Verdandi file at the time of
writing. Redo any walk against the live files before relying on it; the subject words
are expected to change, the pattern is not.

**One trunk across four axes.**

```
data        role_expertise                         a list, in IdentityAnthropic
content     identity_role_expertise_label          → label          → trunk role_expertise
content     identity_role_expertise_postscript     → postscript     → trunk role_expertise
structure   identity_role_expertise_postscript_visible
                                                   → _visible       → governs role_expertise_postscript
display     identity_role_expertise_format         → _format        → formats the list role_expertise
display     identity_role_expertise_format_threshold
                                                   → pairs with role_expertise_format
```

One data field, five controls, one bundle. Nothing in code says "identity has an
expertise list with a label". The names say it.

**One selector, three fragments, three slots.**

```
structure   security_boundary_framing_selector = "territory"
            → _selector → trunk framing → every variant table beginning with framing:
content     security_boundary_framing_section_start_variant        heading slot
content     security_boundary_framing_section_preamble_variant     preamble slot
content     security_boundary_framing_declaration_variant_template body slot, then fill {{WORKSPACE_PATH}}
```

One knob changes the posture of a whole section. The selector's trunk is a prefix, not
an exact name, and that is what lets one choice reach three fragments.

**Whether, which, and the words.**

```
structure   constraints_section_preamble_visible = true      whether it renders
structure   constraints_section_preamble_selector = "standalone"   which alternative
content     [constraints.constraints_section_preamble_variant]     the three alternatives
```

Three fields, one universal name `section_preamble`, three different jobs. A reader
who merges them has lost the whether-which-words distinction the matrix depends on.

**Auto visibility, counted.**

```
content     input_parameters_heading = "Parameters"           _heading: a sub-heading inside the body
structure   input_parameters_heading_visible = "auto"
structure   input_parameters_heading_auto_threshold = 2       render when the parameter count exceeds 2
data        parameters                                        the list being counted
```

`"auto"` is a third state the Boolean cannot express. The threshold field exists only
because the toggle can say "count it". Its Verdandi description says exactly this.

**Standalone prose.**

```
content     critical_rules_fail_fast_body                     _body: standalone, no data trunk
structure   critical_rules_fail_fast_body_visible             its only partner
```

The `_body` suffix says: nothing in the data drives this; render it after the
data-driven body, in content order. Its trunk matches nothing on purpose.

---

## 7. What a mismatch is, and what it is not

A trunk that names no data field is either standalone content by design or a typo.
The engine cannot tell them apart. The probes that count unmatched fields are the only
detector, and a person reads the count. That is the price of having no mapping table,
and it is why naming discipline is load-bearing rather than tidy.

When a real mismatch is found, the fix is in the surface schema: rename the control
so its trunk matches the data. The data model is never bent to fit a control, and the
engine never grows a special case. Johnny, 2026-09-19: *"all of these things are
really critical to finding what belongs where. And we have to be and become very clear
about what these rules are... in this way, we can add stuff without changing the code
much."*

Before you call any name wrong, do all of the following, in this order:

1. Peel it by section 3 and write down what each layer says.
2. Open its Verdandi field file under `~/ai/smidja/verdandi/agent-output/source/`
   and read the description. The file name is the full field name.
3. Find its partners by section 5, in the other surfaces and in the data model.
4. Open the section's sheet in `review/` for the intent behind any name that still
   does not line up.

Only after step 4 is "this does not link" a finding. Before it, it is a guess, and a
guess about a name here has cost whole sessions.

---

## 8. Proof of reading

Before writing anything: take three control fields from the live surfaces, one each
from structure, content and display, chosen by you. For each, give the peel from
section 3, the shape from section 4, the partners from section 5, and the
one-sentence description from its Verdandi file. If you cannot do that from the files,
you are not ready to touch a name, a bundle, or the engine.
