"""``copier.yml``'s ``_exclude`` keeps copier's defaults and the dropped paths.

``_exclude`` *replaces* copier's built-in exclude list, so the file re-lists
those defaults; if copier adds one, a template that only names its own paths
would start rendering files the default list exists to keep out.

The dropped-path entries stop ``copier update`` from deleting an adopter's copy
of a module the template no longer renders (#321).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from copier._template import DEFAULT_EXCLUDE

COPIER_YML = Path(__file__).parent.parent / "copier.yml"


def _exclude() -> list[str]:
    return yaml.safe_load(COPIER_YML.read_text(encoding="utf-8"))["_exclude"]


def test_exclude_keeps_copier_defaults() -> None:
    assert set(DEFAULT_EXCLUDE) <= set(_exclude())


def test_exclude_protects_dropped_placeholders() -> None:
    exclude = _exclude()
    assert "src/{{ github_repo_name }}/utils/app.py" in exclude
    assert (
        "{% if not primary_component %}"
        "src/{{ github_repo_name }}/core/app.py{% endif %}"
    ) in exclude
