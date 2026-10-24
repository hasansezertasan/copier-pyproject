"""The generated README credits the template it came from, in one consistent wording."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


def test_readme_links_back_to_the_template(render: Callable[..., Path]) -> None:
    readme = (render() / "README.md").read_text()
    assert (
        "Generated from [copier-pyproject](https://github.com/hasansezertasan/copier-pyproject)."
        in readme
    )
