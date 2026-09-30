"""No generated package module is an empty placeholder (docstring and filler only).

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


def _is_filler(node: ast.stmt) -> bool:
    """Whether a statement adds nothing: ``pass``, ``...``, a ``__future__`` import."""
    if isinstance(node, ast.Pass):
        return True
    if isinstance(node, ast.ImportFrom):
        return node.module == "__future__"
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and node.value.value is Ellipsis
    )


def _is_placeholder(path: Path) -> bool:
    """Whether the module holds nothing beyond a docstring and filler."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    body = tree.body[1:] if ast.get_docstring(tree) is not None else tree.body
    return all(_is_filler(node) for node in body)


@pytest.mark.parametrize("preset", ["library", "tool", "web", "full"])
def test_no_placeholder_modules(
    render: Callable[..., Path],
    preset: str,
) -> None:
    src = render(preset=preset) / "src" / PKG
    modules = [path for path in src.rglob("*.py") if path.name != "__init__.py"]
    assert modules, f"no modules found under {src}"
    placeholders = sorted(
        str(path.relative_to(src)) for path in modules if _is_placeholder(path)
    )
    assert placeholders == []
