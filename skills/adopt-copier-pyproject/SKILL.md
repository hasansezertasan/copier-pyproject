---
name: adopt-copier-pyproject
description: Use when adopting the hasansezertasan/copier-pyproject Copier template into an EXISTING or already-published Python package (not a fresh scaffold), or when a `copier update` from that template overwrites source/config and needs reconciling. Covers the source-skeleton collision, ruff auto-fix source corruption, the release-please/hatch-vcs version clash, and the TODO/placeholder content the template plants in issue templates and docs.
---

# Adopt copier-pyproject into an existing package

## Overview

`copier-pyproject` is documented as **new-projects-only**: `copier copy` scaffolds a
whole project and overwrites whatever it lands on. Adopting it into an existing
package is a **migration-with-reconciliation**, not a scaffold.

**Division of ownership:** the template owns *tooling / CI / config*; the project
owns its *runtime source and identity* (`src/<pkg>/**`, README, LICENSE, keywords,
CHANGELOG). `copier copy` overwrites both — so **`git diff` on a clean branch is the
safety net, and the reconciliation between "copier wrote files" and "commit" is the
entire job.** Run copier, let it overwrite everything, then restore your side from git.

## Procedure

1. **Pre-flight.** Clean working tree on a dedicated branch. Delete cache/venv cruft
   (`.venv/`, `.*_cache/`, stray `.coverage*`) so the diff is pure. Record the current
   version (`uv run hatch version`) to detect release drift later.

2. **Run copier, overwrite everything:**
   ```bash
   copier copy --overwrite --defaults --data <k=v>... gh:hasansezertasan/copier-pyproject .
   ```
   **No `--trust` is needed** — the template deliberately defines **no `_tasks`** (or
   other unsafe features) so Renovate's copier manager can run it (ADR-015), and it
   does **not** auto-`git init`; run `git init` yourself afterward. (Only add
   `--trust` if you target an older template version that still defined
   `_tasks`/migrations.) Pass every answer via `--data` (reproducible). Defend the two
   **zero-dependency guarantees**: `include_cli=false` and
   `include_pydantic_settings=false`.

3. **Reconcile from git (the real work), area by area:**
   - **Restore your real source + identity**, then delete the template's app skeleton:
     ```bash
     git checkout -- src/<pkg>/__init__.py src/<pkg>/__main__.py README.md CHANGELOG.md LICENSE
     rm -rf src/<pkg>/core src/<pkg>/utils src/<pkg>/__metadata__.py
     ```
   - **`pyproject.toml`** — take the template's `[tool.*]` blocks, but re-add your
     load-bearing settings: `[project.scripts]`, real keywords/classifiers
     (`Development Status`), `[tool.coverage.paths]` src↔site-packages remap,
     `omit=["*/_version.py"]`, the sdist `include` list, and every deliberate
     `per-file-ignores` (see example below).
   - **Docs** — the template ships Sphinx `.rst`; your old `index.md` **collides** with
     `index.rst` (same docname). Delete the mkdocs `.md` pages, port content into the
     `.rst`, and **rewrite `modules.rst`** — its `automodule` directives point at the
     deleted skeleton (`<pkg>.core.config`, `<pkg>.utils`), not your real modules.
   - **Tests** — the generated tests import the deleted skeleton
     (`<pkg>.__metadata__`, `<pkg>.core.config`, `<pkg>.__main__:main`). Remove or
     replace them; keep the smoke test.
   - **release-please manifest** — set `.github/release-please-manifest.json` to your
     **actual current released version** (not the template's `0.1.0`), or the first
     release mis-computes the next version.
   - Delete superseded originals: `mkdocs.yml`, `requirements.docs.txt`,
     `.pre-commit-config.yaml`, old release-drafter/dependabot/`cd.yml`.

4. **Gate ruff BEFORE it runs.** The template sets `fix=true` + `unsafe-fixes=true` +
   `select=ALL`. The first `ruff check` (or any hook) **rewrites `src/**` in place**,
   silently deleting things like a CLI's `print()`. Run `ruff check --diff` first, or
   add `per-file-ignores` for your deliberate patterns, *then* let it fix.

5. **Verify, then commit as one baseline:** `uv sync`; import + console script +
   `python -m <pkg>`; `ruff check`/`ruff format --check`; `mypy`; `basedpyright`;
   `pytest`; `sphinx-build -W`; `uv build`. Then the update-anchor gate:
   `copier update --pretend` **must report up-to-date** — if it wants to re-apply
   changes, your reconciliation diverged and future updates will conflict-storm. (If
   the template HEAD has moved past your anchor, pin the check with
   `--vcs-ref=<your _commit>` so a newer commit is not mistaken for divergence — see
   the `copier update` section.)

6. **External one-time setup** (can't be tested from the branch): PyPI Trusted
   Publishing, `CODECOV_TOKEN`, enable GitHub Pages after first `gh-pages` build,
   install Renovate app.

## Updating an already-adopted project (`copier update`)

The Procedure above is the **first adoption** (`copier copy --overwrite` → blow away,
restore from git). Once the project carries a `.copier-answers.yml` with a `_commit:`
anchor, pulling later template changes is a **different, cleaner flow.** `copier
update` does a **3-way git merge** against your recorded answers, so it preserves the
reconciliations you already committed and only emits conflicts where the template and
your edits touch the same lines. **Do NOT `copier copy --overwrite` an already-adopted
project** — it discards every prior reconciliation and forces the full manual restore
again.

1. **Invoke** (the `mise` shim is often unresolvable — `No version is set for shim:
   copier`; `uvx` is reliable):
   ```bash
   uvx copier@latest update --defaults
   ```
   No `--trust` needed (the template defines no `_tasks`/migrations). `--defaults`
   accepts stored answers; a genuinely new template question takes its default —
   check the answers diff so a new answer does not silently enable a dependency.

2. **Resolve conflicts, not a full restore.** Conflicts surface as `UU` files with
   `<<<<<<< before updating` / `=======` / `>>>>>>> after updating` markers (`before`
   = your committed version, `after` = template). Resolve per hunk:
   - **Machine config / CI logic / SHA-pin bumps** → take `after` (template).
   - **Project identity + prose** (README features, real CONTRIBUTING content, issue-
     template examples) → keep `before`, but **graft in genuinely new template
     capabilities** (e.g. a new managed-`.gitignore` / cobo feature bullet).
   - Planted TODOs appear on the `after` side of prose conflicts — drop them, keep your
     real content (see Manual adjustments).
   Then `git add -A` to clear the merge state; `git grep -nE '^(<<<<<<<|>>>>>>>) '` must
   be empty.

3. **Still restore project-owned files the merge deletes/resets** (same as first
   adoption): `copier update` deletes `CHANGELOG.md` and resets
   `.github/release-please-manifest.json` to `0.0.0` — `git checkout --` both (manifest
   → your real released version, gotcha #3). Re-run the ruff + taplo gates
   (gotchas #1, #10) and confirm `docs/conf.py` kept your custom `exclude_patterns`
   (gotcha #9).

4. **Anchor gate — pin to YOUR anchor when template HEAD has moved.** A plain
   `copier update --pretend` targets the template's current HEAD; if HEAD advanced
   since your update (common — it can move mid-session) it reports wanting to move to
   the *newer* commit, which is **not** reconciliation divergence. Test convergence
   against the commit you actually reconciled to:
   ```bash
   uvx copier@latest update --vcs-ref=<your _commit> --pretend --defaults
   ```
   Must print **`Keeping template version …<your _commit>`** (nothing to re-apply) — the
   real proof your reconciliation converged. If a newer commit exists and you want it,
   just run `update` again: it is a fresh, usually-tiny merge, committed separately.
   (`--pretend` refuses on a dirty tree, so run it after committing the baseline.)

## Manual adjustments the template plants (CI will NOT catch these)

The template renders **prose content assuming a generic web/CLI app** that is wrong
for your project but is *valid markdown* — so it passes every linter, type check,
and the coverage gate. The full green sweep gives false confidence; **only a human
read catches it.** Do this pass before opening the PR.

- **Resolve every planted TODO interactively — one at a time, with the maintainer.**
  Do NOT batch-delete or batch-fill; each TODO is a real decision the maintainer owns.
  1. **Find them all.** The template plants HTML-comment TODOs as well as plain ones:
     ```bash
     grep -rnI -E 'TODO|FIXME|XXX|@<user>:|<!-- *TODO' . \
       --exclude-dir=.git --exclude-dir=.tox --exclude-dir=.venv \
       --exclude-dir=node_modules --exclude-dir=_build --exclude-dir=htmlcov \
       --exclude-dir=megalinter-reports | grep -viE '\.lock:|# noqa'
     ```
     Filter false positives (e.g. a `XXXXXXXX-XXXX-…` UUID **format** placeholder in an
     example file is intentional, not a TODO).
  2. **Ask the maintainer about each one**, showing its file/line and surrounding
     context. Offer concrete options: *write real project-specific content*, *remove
     the placeholder*, or *leave it in place*. Recommend based on the project's nature
     (e.g. a zero-dep library has no services/env vars to document → the setup TODO is
     often just removed or kept).
  3. **Apply each decision, then move to the next** — resolve them one by one so the
     diff stays legible and no decision is silently skipped.
  Typical locations: `CITATION.cff` (verify author given/family-name split),
  `CONTRIBUTING.md` (project-specific setup, docs workflow, "Join The Project Team"),
  and issue templates.
- **Review the GitHub issue templates** (`.github/ISSUE_TEMPLATE/*.md`) and
  `CONTRIBUTING.md`/`SECURITY.md`/`SUPPORT.md`. `bug_report.md`, `usage.md`,
  `installation.md`, `compatibility.md`, `performance.md` ship example blocks
  referencing **FastAPI / uvicorn / ReDoc**, non-existent CLI subcommands
  (`<pkg> version`, `<pkg> info`), a **stale `<pkg>==0.1.0`** pin, and
  `Backend: [FastAPI]` fields. Rewrite them for your project's real surface, or
  delete the framework examples if it's a plain library.
- **`config.yml`** and rendered URLs are usually fine (correctly interpolated) — the
  danger is the *example bodies*, not the frontmatter.

## Gotchas (each cost real time in a live migration)

| # | Gotcha | Fix |
|---|--------|-----|
| 1 | `ruff fix=true`+`unsafe-fixes`+`select=ALL` rewrites source on first contact | Gate with `--diff` / `per-file-ignores` before any fix runs |
| 2 | Template `src/<pkg>/` skeleton (`core/` **package** vs your `core.py` **module**, `utils/`, `__metadata__.py`, blanked `__init__.py`) collides with real code | Restore real files from git; `rm -rf` the skeleton |
| 3 | Version-source clash: `hatch-vcs` (dynamic, from tags) vs release-please | Keep dynamic version; release-please tags → hatch-vcs reads tag. Set manifest to current version |
| 4 | Zero-dep divergences (`include_cli`, `include_pydantic_settings`=false) must be re-applied on **every** `copier update` | After each update, verify `dependencies=[]` and no transitive deps |
| 5 | Docs `index.md` vs `index.rst` docname collision; `modules.rst` autodocs the deleted skeleton | Delete `.md`, port to `.rst`, rewrite `automodule` to real modules |
| 6 | Generated tests import the deleted skeleton; `fail_under=99` coverage gate with no real suite | Replace tests; a real suite is a separate follow-up |
| 7 | Breaking Python-floor drop (e.g. `>=3.10`) mis-bumps under `bump-minor-pre-major` | Land with a `feat!:`/`BREAKING CHANGE:` commit footer |
| 8 | Template plants generic prose (FastAPI/CLI examples, `TODO @`, stale `0.1.0`) in issue templates + docs — **invisible to every gate** | Human read before PR; start with `grep -rn 'TODO @' .` (see Manual adjustments) |
| 9 | A `copier update` drops a project-added `exclude_patterns` entry in `docs/conf.py` (e.g. `superpowers/**`) → Sphinx discovers + **publishes internal design specs** to GitHub Pages | Re-add the project's custom `exclude_patterns` after every update; diff `docs/conf.py` |
| 10 | Template ships `prek.toml` — and often `pyproject.toml` — **not** taplo-formatted → the `style` tox env's `taplo format --check` fails, cascading into **every** `Run Tests` matrix job (they run `style`) | `taplo format prek.toml pyproject.toml`; re-run `tox -e style`. taplo reformats `pyproject.toml` aggressively (collapses arrays to one line) — expected churn, required by CI |
| 11 | MegaLinter (new CI layer) `cspell` flags project terms, tool names, the author handle, and the template docs' **British spellings** (`behaviour`, `licence`, …) | In `.github/linters/.cspell.yml` set `language: en,en-GB` and extend `words:` with project/tool/name terms; MegaLinter only lints `.md` by default. **Recent template versions auto-inject the project name, author handle, and author-name tokens** (YAML-escaped) into `words:` — verify they survived the update rather than re-adding by hand |
| 12 | `Verify linked issue` CI check fails a chore/`copier update` PR that has no issue to link | Create + apply the `no-issue` label (the action's `skip-linked-issues-check-label`) |

## Deliberate per-file-ignores to re-add (example)

The template's generic ruff config drops project-specific ignores. Native, shipped
patterns need them back:

```toml
[tool.ruff.lint.per-file-ignores]
"src/<pkg>/main.py" = ["T201"]              # CLI deliberately prints to stdout
"src/<pkg>/impl/*.py" = ["S404", "S602"]    # backends shell out to OS tools (intended)
"examples/**/*.py" = ["N999", "INP001"]     # dash-named standalone example dirs
```

## Common mistakes

- **Answering copier conflict prompts one-by-one.** Unreliable at scale — overwrite
  everything and reconcile from git instead.
- **Running any tool before gating ruff.** Auto-fix corrupts source first.
- **Skipping the `copier update --pretend` gate.** A wrong update-anchor makes every
  future update a merge conflict. Pin it with `--vcs-ref=<your _commit>` — a plain
  `--pretend` after the template HEAD moved reports a false "diverged".
- **`copier copy --overwrite` on an already-adopted project.** Use `copier update` —
  overwrite throws away every committed reconciliation and forces the full restore again.
- **Treating coverage `fail_under=99` as met.** A package with no prior tests won't
  pass; scope a real test suite separately.
- **Treating a fully-green CI/style sweep as "done".** The planted prose (see Manual
  adjustments) is valid markdown — every gate passes while `TODO @` and FastAPI
  examples ship. Do the human content pass before opening the PR.
- **Running `markdownlint-cli2` locally to spot-check one file.** The template's
  `.markdownlint-cli2.yaml` sets `fix: true`, so it auto-reformats **all** discovered
  `.md` files (table-pipe padding, etc.), not just your target — silently churning
  unrelated files. Use `cspell`/`sphinx-lint` for local spot-checks, or `git checkout`
  the unintended churn afterward. CI runs MegaLinter with `APPLY_FIXES: none`, so it
  only reports — the auto-fix is a local-only footgun.
