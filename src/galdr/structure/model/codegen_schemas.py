"""The codegen config — which schema becomes which generated module.

Validated against schemas/config/codegen-schemas.schema.json by the TOML
reader before it reaches this model.
"""

from pydantic import BaseModel, ConfigDict


class CodegenSchemas(BaseModel):
    """src/galdr/codegen_schemas.toml: schema name -> module path, per source project."""

    model_config = ConfigDict(frozen=True)

    checkpoint: dict[str, str]
    output: dict[str, str]
