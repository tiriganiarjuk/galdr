"""The stage-1 slot inspection report, in the shape the markdown writer takes.

Validated against schemas/output/slot-inspection-report.schema.json by the
writer before anything reaches disk.
"""

from pydantic import BaseModel, ConfigDict


class SlotInspectionReport(BaseModel):
    """A markdown document as {frontmatter, body}; this report has no frontmatter."""

    model_config = ConfigDict(frozen=True)

    frontmatter: dict[str, str] = {}
    body: str
