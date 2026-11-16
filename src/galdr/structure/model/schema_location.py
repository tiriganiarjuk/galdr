"""Which schema a Nornir reader or writer validates against, named at call time."""

from pydantic import BaseModel, ConfigDict


class SchemaLocation(BaseModel):
    """The schema file {directory}/{name}.schema.json; directory is absolute."""

    model_config = ConfigDict(frozen=True)

    name: str
    directory: str
