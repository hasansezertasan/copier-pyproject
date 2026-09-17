"""The generated markdownlint config keeps table-destroying autofixes off.

``.markdownlint-cli2.jsonc`` ships ``fix: true``, so every enabled rule's
autofix rewrites files in place on each commit. MD060/table-column-style pads
the pipes of a table's delimiter row; when that row is compact and lacks a
leading pipe (``-|:-:|---``), the padded result (``- | :-: | ---``) parses as a
bullet list item and the table silently degrades to paragraph text (issue #276).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import yaml

RULES = ".github/linters/.markdownlint.yml"
CLI2 = ".markdownlint-cli2.jsonc"


def test_table_column_style_autofix_is_disabled(render: Callable[..., Path]) -> None:
    root = render()

    # The premise: autofix is on, so an unsafe fixer corrupts files silently.
    assert '"fix": true' in (root / CLI2).read_text(encoding="utf-8")

    rules = yaml.safe_load((root / RULES).read_text(encoding="utf-8"))
    assert rules["MD060"] is False
