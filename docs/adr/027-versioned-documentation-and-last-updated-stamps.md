# ADR-027: Versioned documentation + per-page "last updated" stamps

## Status

Proposed (2026-08). Implements #165. Builds on ADR-006 (Sphinx + Shibuya) and
ADR-010 (PR docs previews); gated by ADR-025 (`include_docs`).

## Context

Generated projects build docs with Sphinx + Shibuya (ADR-006) and publish them to
GitHub Pages from `release.yml`'s `deploy-docs` job, with per-PR previews under
`pr-preview/**` (ADR-010). But only a single `latest` version is ever published —
the site is overwritten on every release. An adopter's users who are pinned to an
older release have no matching docs, and there is no way to browse the docs for a
specific version. Under ADR-002's `bump-minor-pre-major`, minors are the breaking
bump pre-1.0, so single-version docs are a real gap for any project that ships
breaking changes.

A second, smaller rot issue: docs pages carry no "last updated" signal, so readers
cannot tell how fresh a page is.

### What the ecosystem does

The Sphinx-native options are `sphinx-multiversion` (mature but effectively
unmaintained) and `sphinx-polyversion` (newer, active). **Both rebuild every
selected tag on every deploy** — `sphinx-multiversion` in a single current
environment, `sphinx-polyversion` in isolated per-version venvs.

That rebuild-old-tags model is a poor fit for *this* template specifically: a
generated project's `conf.py` runs build-time subprocess generators (FastStream
AsyncAPI, the Typer CLI reference, Litestar/FastAPI OpenAPI) against the live
`app` objects. Rebuilding a historical tag means re-running *that tag's*
generators against whatever dependency set the build resolves — fragile, slow, and
it forces every past `conf.py` to keep building cleanly forever, which constrains
how docs tooling can evolve.

Litestar (Sphinx + a Shibuya-family theme, the same stack as ours) sidesteps this
entirely. It does **not** use either multiversion library. A small
`tools/build_docs.py` builds only the *current* ref's docs at release time, then
copies the *already-built* older versions off the `gh-pages` branch to preserve
them. **Old versions are never rebuilt** — they were built when they were current
and are simply carried forward. The Shibuya theme already ships a native version
switcher (`components/nav-versions.html`) driven by
`html_context["versions"]` (a list of `[label, url]` pairs) + `current_version`,
so no theme swap is needed.

## Decision

Adopt the Litestar-style **build-current-preserve-rest** model, with one
deliberate deviation, and add a per-page last-updated footer.

### 1. Versioned publishing (always-on within `include_docs`)

Versioned publishing is not a new toggle — it is how a docs-enabled project always
publishes. A generated `tools/build_docs.py` orchestrates each deploy:

1. Compute the destination **slug** from the release version at the configured
   granularity (see below): e.g. `0.3.1` → `0.3` (minor) / `0` (major) / `0.3.1`
   (full).
2. Enumerate the version directories already present on `gh-pages`, union the new
   slug, and sort with `packaging.version`. `latest` is the highest
   non-prerelease.
3. Write `docs/_static/versions.json` into the source tree so *this* build's
   switcher lists every known version, then run the existing docs build
   (`sphinx-build -w … + docs/check_warnings.py`) unchanged.
4. Copy the freshly built HTML to `<out>/<slug>` and, when it is the newest
   stable, to `<out>/latest`; copy every *other* version directory across from
   `gh-pages` so the deploy folder is the complete site; write a root
   `index.html` that redirects to `latest`.
5. Deploy with the existing `clean-exclude: pr-preview/**` + `force: false`, so PR
   previews (ADR-010) are never wiped and version directories (`vX.Y/**`) and the
   preview tree stay disjoint.

### 2. Deviation from Litestar — stateless version list

Litestar **commits** `versions.json` and hand-edits it (fine at three major
lines). With per-minor granularity and automated release-please releases,
hand-editing every release is untenable, and having CI commit the file back to a
protected `main` adds real machinery. So the version list is **stateless**:
derived from the `gh-pages` directory listing at build time, with `gh-pages`
itself as the source of truth. `docs/_static/versions.json` is **generated** into
each build (and gitignored), never committed. Local `tox` `docs-build` runs have
no `gh-pages` and no generated file, so `conf.py` finds no `versions.json` and the
Shibuya switcher hides itself — local builds stay single-version and clean.

Accepted limitation (also called out in #165): an older version's switcher is
frozen at build time — it lists only the versions that existed when it was built.
The switcher therefore only appears from the first versioned release onward.

### 3. Version granularity — a scaffold-time choice

Granularity is the one knob adopters reasonably differ on, so it is a Copier
question, **`docs_version_granularity`** (`when: include_docs`), with choices
**minor** (`X.Y`, default), **major** (`X`), and **full** (`X.Y.Z`). Default
`minor` matches ADR-002's pre-1.0 minor-is-breaking posture; a big project can
pick `major`, an archival project `full`. The choice bakes a single slug-slicing
constant into the generated `build_docs.py`.

### 4. Manual `gh-pages.yml` stays, made version-aware

The manual redeploy escape hatch is kept but **must** route through
`build_docs.py` — a naive root publish with only `clean-exclude: pr-preview/**`
would wipe every `vX.Y/**` directory. It rebuilds the current release version and
preserves the rest, identically to the release path.

### 5. Per-page "last updated"

Add `sphinx-last-updated-by-git` to the `docs` dependency group (always-on within
`include_docs`). Every page footer shows the git commit date of its source — a
cheap freshness signal that works offline from local history. The
machine-generated `_generated/` fragments are already in `exclude_patterns`; if
the extension emits any untracked-source warning it is reconciled through the
existing `check_warnings.py` / `expected_warnings.txt` allowlist rather than by
blanket suppression.

## Consequences

- Docs-enabled projects publish per-version docs with an in-page switcher and a
  `latest` alias, at no extra build cost per deploy (only the current version is
  ever built; the rest are copied).
- `gh-pages` becomes load-bearing state: the version list is reconstructed from
  it, and both the release and manual deploy paths **must preserve `vX.Y/**`** (a
  load-bearing invariant recorded in `CLAUDE.md`).
- Old versions are never rebuilt, so a past `conf.py` need not keep building under
  future tooling — the constraint that sinks the multiversion libraries here does
  not apply.
- One new scaffold-time question (`docs_version_granularity`) and one new
  generated file (`tools/build_docs.py`, outside `src/` so the 99% coverage gate
  does not cover it; still ruff/mypy-clean).
- `sphinx-last-updated-by-git` requires full git history at build time; the docs
  CI jobs already check out with `fetch-depth: 0`.
- PR previews are unchanged and remain disjoint from version directories.
