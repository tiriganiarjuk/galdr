"""Codegen clean primitives — fix code-generation artifacts.

CC=1. No branching. No cross-module dependencies.

The RootModel name collection is the first step of the constraint stripping
pipeline (see composed.py for why constraints need stripping).
"""

import re


def collect_rootmodel_names(content: str) -> set[str]:
    """Find all class names that extend RootModel.

    Handles both single-line and multi-line class definitions
    where the base class wraps to the next line.
    """
    return set(re.findall(r"class (\w+)\(\s*RootModel", content))
