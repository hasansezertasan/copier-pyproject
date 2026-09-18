"""The generated markdownlint config keeps table-destroying autofixes off.

``.markdownlint-cli2.jsonc`` ships ``fix: true``, so every enabled rule's
autofix rewrites files in place on each commit. MD060/table-column-style pads
the pipes of a table's delimiter row; when that row is compact and lacks a
leading pipe (``-|:-:|---``), the padded result (``- | :-: | ---``) parses as a
bullet list item and the table silently degrades to paragraph text (issue #276).

The assertions cover the wiring as well as the value, since a rule file the
CLI never loads would disable nothing: the ``extends`` chain from the config
markdownlint-cli2 discovers must actually reach the file carrying the disable.
Whether markdownlint then honors ``MD060: false`` is upstream's contract — the
harness renders and inspects, it does not install the generated project's node
toolchain (ADR-024).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import yaml

RULES = ".github/linters/.markdownlint.yml"
CLI2 = ".markdownlint-cli2.jsonc"
# The MegaLinter entry point, which reaches the same rules via its own relative
# extends (template/.github/linters/.markdownlint-cli2.yaml).
LINTERS_CLI2 = ".github/linters/.markdownlint-cli2.yaml"


def test_table_column_style_autofix_is_disabled(render: Callable[..., Path]) -> None:
    root = render()

    # The premise: autofix is on, so an unsafe fixer corrupts files silently.
    cli2 = (root / CLI2).read_text(encoding="utf-8")
    assert '"fix": true' in cli2
    # ... and the rule file below is the one that run actually loads.
    assert f'"extends": "{RULES}"' in cli2

    rules_path = root / RULES
    rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    assert rules["MD060"] is False

    # MegaLinter's entry point extends the same file by a relative path.
    linters_cli2 = yaml.safe_load((root / LINTERS_CLI2).read_text(encoding="utf-8"))
    assert (
        rules_path.parent / linters_cli2["config"]["extends"]
    ).resolve() == rules_path.resolve()
