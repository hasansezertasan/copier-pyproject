"""No generated package module is a docstring-only placeholder.

An empty module has no importers and no tests, and nothing downstream flags it
(not vulture, not coverage), so a placeholder stays in every generated project
indefinitely — and reads as guidance about where code belongs. ``utils/app.py``
and the library preset's ``core/app.py`` both shipped that way (#321). A module
belongs in the template only once it has contents; a layer that has none yet is
carried by its ``__init__.py``.

Scoped to ``src/``: ``examples/*/main.py`` are deliberate usage stubs the
adopter fills in (``include_examples``).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Callable

import pytest

PKG = "example"


def _is_placeholder(path: Path) -> bool:
    """Whether the module's body is empty apart from an optional docstring."""
    body = ast.parse(path.read_text(encoding="utf-8")).body
    if body and ast.get_docstring(ast.Module(body=body, type_ignores=[])):
        body = body[1:]
    return not body


@pytest.mark.parametrize("preset", ["library", "tool", "web", "full"])
def test_no_docstring_only_modules(
    render: Callable[..., Path],
    preset: str,
) -> None:
    src = render(preset=preset) / "src" / PKG
    placeholders = sorted(
        str(path.relative_to(src))
        for path in src.rglob("*.py")
        if path.name != "__init__.py" and _is_placeholder(path)
    )
    assert placeholders == []
