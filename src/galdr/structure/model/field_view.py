"""Field view — one section's fields as short name -> value.

What the universal engine receives instead of a Pydantic section model.
Names are the short universal names: the `{section}_` domain prefix is
stripped from control-surface fields once, at the boundary, so the engine
never deals with namespacing. Data field names pass through untouched —
they carry no domain prefix, and some happen to begin with their section's
name (`input_schema`), which stripping would corrupt.

Values are whatever the generated models hold: a Pydantic model (RootModel
wrappers, variant sub-tables), an enum member, or None for an unset
optional field.
"""

from enum import Enum

from pydantic import BaseModel

type FieldValue = BaseModel | Enum | None

type FieldView = dict[str, FieldValue]
