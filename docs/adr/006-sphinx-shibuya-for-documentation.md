# ADR-006: Sphinx + Shibuya for documentation, replacing MkDocs

## Status

Accepted (2026-06).

## Context

The template originally scaffolded documentation with **MkDocs** + the
`mkdocs-material` theme: a `mkdocs.yml.jinja`, four Markdown pages
(`index`/`installation`/`usage`/`modules`), tox `docs-build`/`docs-server` envs
running `mkdocs build`/`mkdocs serve`, and a CI `deploy-docs` job running
`mkdocs gh-deploy`.

Two problems motivated revisiting that choice:

1. **The MkDocs 2.0 release line has been unstable.** Pinning to the 1.x line
   indefinitely is a dead end, and adopting 2.0 as it stabilized risked churn in
   every generated project.
2. **The shipped setup never actually used what it installed.** `mkdocs-material`
   was a dependency but was *not* configured in `mkdocs.yml` (no
   `theme: name: material`), so generated projects built with the stock MkDocs
   theme. The `modules.md` "API reference" was hand-maintained prose that did not
   track the code — there was no autodoc.

The reference point for the desired result was the Litestar organization's
projects (Litestar, Advanced Alchemy, Polyfactory), whose documentation sites are
the visual target. Investigation showed those sites are **not MkDocs** — they are
**Sphinx**, and the attractive look is the **[Shibuya](https://shibuya.lepture.com/)**
theme. Two flavors exist in that ecosystem:

| Project | Theme | Markup | API docs |
|---------|-------|--------|----------|
| Litestar | `litestar-sphinx-theme` (git `@v3`, wraps Shibuya) | RST | autodoc + napoleon |
| Advanced Alchemy | `litestar-sphinx-theme` | RST | autodoc + napoleon |
| Polyfactory | bare `shibuya` (PyPI) | RST + MyST | autodoc + napoleon |

`litestar-sphinx-theme` is Shibuya plus Litestar-org branding, footer, and
Discord/GitHub chrome, distributed as a **git dependency**. For a *generic* Python
package template, that branding is wrong and a git dependency is an undesirable
default. Polyfactory's setup — bare Shibuya from PyPI — is the right model.

## Decision

Generated projects document with **Sphinx + the bare Shibuya theme**, replacing
MkDocs entirely. Documentation remains unconditional (no `include_docs` toggle).

Specifics:

- **Theme:** `shibuya` from PyPI (not `litestar-sphinx-theme`), so projects carry
  no third-party branding and depend only on versioned PyPI releases.
- **Markup:** reStructuredText (`.rst`). `myst-parser` is enabled so `.md` pages
  also work, but the scaffolded pages are RST to match the Litestar-org reference.
- **API reference:** `sphinx.ext.autodoc` + `sphinx.ext.napoleon` (Google-style
  docstrings). `modules.rst` is generated from `.. automodule::` directives,
  conditional per enabled component (`cli`, `web`, `gui`, `tui`, `mcp`, `worker`),
  so the API reference tracks the source instead of being hand-maintained.
- **Extensions:** `sphinx-design`, `sphinx-copybutton`, `sphinx-togglebutton`,
  `sphinx-paramlinks`, `auto-pytabs` (the Python-version code tabs Litestar uses),
  `intersphinx`, `autosectionlabel`, `viewcode`, and `sphinx-click` **only when
  `include_cli`**.
- **tox:** `docs-build` runs `sphinx-build -b html docs docs/_build/html`;
  `docs-server` runs `sphinx-autobuild`. Both set `extras = ["all"]` (see
  Consequences — autodoc must import the package and its optional dependencies).
- **CI deploy:** the `deploy-docs` job and `gh-pages.yml` build with `sphinx-build`
  and publish with `ghp-import -n -p -f docs/_build/html`. `ghp-import` is the same
  tool MkDocs invoked under the hood for `gh-deploy`, so the **gh-pages-branch
  publishing model is unchanged** and no GitHub Pages settings change is required.
- **Pins:** the `docs` dependency group uses exact `==` pins (Renovate-managed),
  consistent with the `style`, `tool`, and `prek` groups.

This complements [ADR-002](002-release-please-for-release-automation.md), which
established the inline `deploy-docs` job: that job's *placement* and gating are
unchanged here; only its build/publish commands moved from MkDocs to Sphinx.

## Rationale

- **Matches the visual target by using its actual stack.** The Litestar-org look is
  Shibuya + Sphinx; adopting Sphinx is the direct path, not an approximation.
- **Bare Shibuya over `litestar-sphinx-theme`.** A generic template must not ship
  another project's branding, and a PyPI dependency is a healthier default than a
  pinned git ref.
- **Real API docs.** autodoc + napoleon makes `modules.rst` track the code; the old
  hand-written `modules.md` could silently rot.
- **Leaves the unstable MkDocs 2.0 line behind** without trading into churn.
- **No deployment-model change.** Reusing `ghp-import` keeps the gh-pages branch
  contract identical, so existing Pages configuration in generated repos keeps
  working.

## Consequences

- **Docs build installs the package, not just the docs group.** MkDocs deployed
  with `--only-group docs`; autodoc must *import* the package and any optional
  dependencies of the modules it documents. The tox envs therefore set
  `extras = ["all"]`, and the CI steps run
  `uv run --no-default-groups --extra all --group docs sphinx-build …`. Without the
  extras, `.. automodule:: pkg.web.app` would fail to import its framework.
- **`mkdocs.yml.jinja` and the four `*.md.jinja` pages are removed**, replaced by
  `docs/conf.py.jinja` and `docs/{index,installation,usage,modules}.rst.jinja`.
- **`check-yaml --unsafe` is dropped from `prek.toml`.** The `--unsafe` flag existed
  only to parse `mkdocs.yml`'s `!!python/name` tags; with `conf.py` (plain Python)
  there is no YAML using Python tags, so standard safe parsing is restored.
- **A `docs/conf.py` per-file ignore (`INP001`) is added to ruff** — `conf.py` is a
  standalone config module, not part of an importable package.
- **A redundant module-docstring `Attributes:` section was removed from
  `core/logging_setup.py`.** It duplicated the `logger` variable's own attribute
  docstring, which produced a duplicate-object autodoc warning once real autodoc
  was enabled (MkDocs never surfaced it).
- **`gh-pages.yml` remains** for manual `workflow_dispatch` redeploys, now building
  with Sphinx.
- The `documentation` project URL and the GitHub Pages target are unchanged.
