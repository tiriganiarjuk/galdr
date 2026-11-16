"""Typed result of a Nornir gate, reader or writer call.

The contract has two outcomes and no others: a success, or a refusal
carrying its failure class and message. A gate or reader succeeds with the
validated JSON string; a writer succeeds with nothing, because the write is
the effect. Each outcome is its own model, so a result that is none of them
fails validation where it arrives.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class GateError(BaseModel):
    """Why the call was refused: the failure class, and the message for people."""

    model_config = ConfigDict(frozen=True)

    type: str
    message: str


class GateSuccess(BaseModel):
    """The file was read and matches its schema; `data` is the validated JSON."""

    model_config = ConfigDict(frozen=True)

    ok: Literal[True]
    data: str
    error: None


class GateRefusal(BaseModel):
    """The call was refused; `error` says in which class and why."""

    model_config = ConfigDict(frozen=True)

    ok: Literal[False]
    data: None
    error: GateError


class GateWritten(BaseModel):
    """The data matched its schema and the file was written."""

    model_config = ConfigDict(frozen=True)

    ok: Literal[True]
    data: None
    error: None


class GateResult(RootModel[Annotated[GateSuccess | GateRefusal, Field(discriminator="ok")]]):
    """What an input gate's validate() or a reader's read() returns."""

    model_config = ConfigDict(frozen=True)


class WriteResult(RootModel[Annotated[GateWritten | GateRefusal, Field(discriminator="ok")]]):
    """What a text writer's write() returns."""

    model_config = ConfigDict(frozen=True)
