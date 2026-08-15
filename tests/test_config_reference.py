"""The pydantic-settings Configuration reference wiring (issue #186).

When ``include_pydantic_settings`` is on, ``docs/configuration.rst`` renders the
settings model via autodoc-pydantic. autodoc-pydantic 2.2.0 has no option to
render each field's *fully-qualified* environment variable name (``env_prefix``
+ field name); it only surfaces the model-level ``env_prefix`` (via the config
summary) plus the field names (via the field summary). These tests pin the
inputs that produce that rendered output — the registered extension, the
``show_config_summary`` toggle that emits ``env_prefix``, the settings model's
fields, and the prose composition rule — so a regression is caught without
standing up a full Sphinx build (the render harness does not install the
generated project or its docs dependencies).
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

CONF = "docs/conf.py"
CONFIG_RST = "docs/configuration.rst"
SETTINGS_MODEL = "src/example/core/config.py"

# The example settings fields autodoc-pydantic lists in the field summary; the
# reference is only useful if every one appears.
SETTINGS_FIELDS = ["debug", "log_level", "config_dir"]
# The uppercased, dash-normalized project name copier derives the env_prefix
# from (github_repo_name="example").
ENV_PREFIX = "EXAMPLE_"


def test_pydantic_settings_wires_config_reference(
    render: Callable[..., Path],
) -> None:
    root = render(include_pydantic_settings=True)

    conf = (root / CONF).read_text(encoding="utf-8")
    assert '"sphinxcontrib.autodoc_pydantic",' in conf
    # ``show_config_summary`` is what surfaces the model's ``env_prefix`` in the
    # rendered page (issue #186 review: env-var prefix must actually appear).
    assert "autodoc_pydantic_settings_show_config_summary = True" in conf
    assert "autodoc_pydantic_settings_show_field_summary = True" in conf

    config_rst_path = root / CONFIG_RST
    assert config_rst_path.is_file()
    config_rst = config_rst_path.read_text(encoding="utf-8")
    # autopydantic_settings pointed at the live model — the source of truth for
    # the rendered fields/types/defaults/constraints.
    assert "autopydantic_settings:: example.core.config.Settings" in config_rst
    # The env_prefix and the composition rule the page documents (autodoc-
    # pydantic cannot render fully-qualified per-field names itself).
    assert ENV_PREFIX in config_rst

    # The field summary renders these straight from the model, so they must be
    # defined on it for the reference to list them.
    model = (root / SETTINGS_MODEL).read_text(encoding="utf-8")
    assert "BaseSettings" in model
    for field in SETTINGS_FIELDS:
        assert f"{field}:" in model, f"settings field {field!r} missing"


def test_library_preset_has_no_config_reference(
    render: Callable[..., Path],
) -> None:
    root = render(preset="library")

    assert not (root / CONFIG_RST).exists()

    conf = (root / CONF).read_text(encoding="utf-8")
    assert "autodoc_pydantic" not in conf
    assert "sphinxcontrib.autodoc_pydantic" not in conf
    # The guarded autodoc-pydantic block trims cleanly when the toggle is off:
    # exactly one blank line survives where the conditional was elided, between
    # the Napoleon and auto-pytabs sections (CodeRabbit/Copilot whitespace nit).
    assert (
        "napoleon_numpy_docstring = False\n\n# -- auto-pytabs" in conf
    ), "autodoc-pydantic conditional left a whitespace regression when off"
