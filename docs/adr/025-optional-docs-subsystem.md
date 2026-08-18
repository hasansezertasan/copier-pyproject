# ADR-025: Optional Sphinx docs subsystem (include_docs)

## Status

Proposed (2026-08). Implements #252.

## Context

Every generated project shipped the full Sphinx documentation subsystem with no
way to opt out: the `docs/` tree, the `docs` dependency group (~10 Sphinx
packages), the `docs-build` / `docs-server` / `docs-linkcheck` tox envs, the
`sphinx-lint` entry in the `style` env (and its prek hook), the `docs-preview.yml`
and `docs-linkcheck.yml` workflows, the manual `gh-pages.yml` redeploy workflow,
and the `deploy-docs` job in `release.yml`.

Docs was the only substantial subsystem in the template with no toggle — every
other one (web, worker, CLI, profiling, c-extensions, the devcontainer services,
the quality/distribution add-ons) is opt-in or opt-out. Not every adopter wants a
published documentation site: a small library, an internal tool, or an
early-stage project often wants a README and nothing more, yet still inherited the
whole docs stack and a GitHub Pages deploy it had to disable by hand.

## Decision

Add a single boolean toggle, **`include_docs`**, and gate the entire Sphinx
subsystem on it. Default **on** for every preset (`library`/`tool`/`web`/`full`),
so:

- existing behavior is unchanged and `copier update` is non-breaking for every
  current adopter — the toggle resolves to `true` on update; and
- the docs-by-default posture (a published site is the recommended baseline) is
  preserved. Turning docs off is a deliberate opt-out, not a preset accident.

### What is gated

`include_docs` guards: the nine Sphinx-site files under `docs/`
(`conf.py`, `check_warnings.py`, `expected_warnings.txt`, `index.rst`,
`installation.rst`, `usage.rst`, `modules.rst`, and the `web-interface.rst` /
`worker-interface.rst` component pages — the latter two additionally on their
component toggles); the `docs` dependency group; the three `docs-*` tox envs; the
`sphinx-lint` entry in both the `style` tox env and the prek hook; the `sphinx`
PyPI keyword and the `docs/conf.py` / `docs/check_warnings.py` ruff per-file
ignores; the `docs-preview.yml`, `docs-linkcheck.yml`, and `gh-pages.yml`
workflows (conditional filenames); the `deploy-docs` job in `release.yml`; the
README docs badge + installation-docs link, the `SUPPORT.md` docs link, the
`CONTRIBUTING.md` "Improving The Documentation" section, the `mise` `docs-build`
/ `docs-serve` tasks, and the "Documentation site (GitHub Pages)" step in
`docs/maintaining/setup.rst`. When docs are off the `settings.yml` `homepage`
falls back from the Pages URL to the repository URL.

### What is NOT gated — `docs/maintaining/setup.rst`

The maintainer **repository-setup guide** lives at `docs/maintaining/setup.rst`
but is not part of the Sphinx *site* in spirit: the `repo-setup` skill reads it as
plain text (its manifest), and it is hard-referenced from `README.md`,
`CONTRIBUTING.md`, `ci.yml`, `settings.yml`, `.sourcery.yaml`, and
`sonar-project.properties`. Dropping the whole `docs/` tree would break all of
those. So `docs/maintaining/` stays present regardless of `include_docs` — it
remains a readable `.rst` at a stable path with no Sphinx needed — and only its
GitHub Pages step is conditionalized. A project with `include_docs=false`
therefore keeps a `docs/` directory containing just the maintainer guide; this is
intentional and non-breaking, and preferable to relocating a path eight other
files depend on.

## Consequences

- A README-only project is now a supported first-class shape: no Sphinx deps, no
  docs tox envs, no docs CI, no Pages deploy.
- One more question in the prompt flow, defaulted from the preset like every other
  toggle.
- The docs-dependent feature issues (#162 tested doc examples, #163 CLI
  reference, #164 rendered project tree, #165 versioned docs, #186 config
  reference) become `include_docs`-gated by construction when implemented.
- The `repo-setup` `SKILL.md` (copied verbatim, not a `.jinja`) still names a
  deferred "GitHub Pages" step; with docs off, `setup.rst` simply omits that step
  and the skill — which drives off `setup.rst` — degrades gracefully.
