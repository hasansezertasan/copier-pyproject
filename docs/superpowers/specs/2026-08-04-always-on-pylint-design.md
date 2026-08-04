# Design: Always-on pylint as a template quality gate

**Date:** 2026-08-04
**Status:** Approved (design)
**Repo:** hasansezertasan/copier-pyproject

## Motivation

Generated projects run a broad static-analysis stack (ruff `select=ALL`, mypy,
basedpyright, ty, pyrefly, zuban, vulture, slotscheck, import-linter). `ruff`
already ports a large part of pylint via its `PL*` rules, so pylint was not part
of the template. This adds **pylint as a first-class, always-on gate** anyway —
a deliberate belt-and-suspenders choice: pylint's inference-based and
refactoring/similarity checks (and some design checks) are not fully reproduced
by ruff's `PL*` port, and running it as its own gate catches issues the other
tools miss. The duplicate findings and added `style`-gate runtime are accepted
trade-offs.

## Decisions

1. **Full pylint, its own gate.** Run stock pylint (not scoped to only the
   checks ruff lacks). Overlap with ruff `PL*` is intentional.
2. **Always-on, no toggle.** Every generated project gets pylint, wired into the
   `style` gate like ruff/mypy — no `include_pylint` question. Simplest template
   logic; the trade-off (overlap, runtime) is uniform across projects.
3. **Curated generalized baseline config.** Ship a `[tool.pylint]` config that is
   usable out-of-the-box: disable only what must go (formatter-owned checks,
   docstring family, `too-few-public-methods`) and set sane design limits;
   everything else (refactor/similarity/inference) stays on.
4. **`src`-only scope, with a defensive guard.** Canonical invocation is
   `pylint src`; tests are linted by ruff, not pylint. Keep
   `ignore-paths = ["^tests/.*$"]` under `[tool.pylint.main]` as a self-documenting
   scope guard for broader/accidental invocations (`pylint .`, filename-passing
   hooks).

## Template changes (`template/…`, Jinja-rendered)

### `template/pyproject.toml.jinja`

- **`[dependency-groups].style`** — add `"pylint==<version>"` alphabetically
  (between `pyrefly` and `ruff`), where `<version>` is the latest pylint release
  resolved at implementation time (olink's reference pin was `4.0.6`). Pin exact
  (repo uses `add-bounds = "exact"`); Renovate-managed thereafter.
- **New `[tool.pylint]` block:**
  ```toml
  [tool.pylint.main]
  # pylint's canonical invocation is `pylint src`, so it never descends into
  # tests; this is a defensive scope guard for broader invocations (`pylint .`,
  # filename-passing hooks). Tests are linted by ruff, not pylint.
  ignore-paths = ["^tests/.*$"]

  [tool.pylint."messages control"]
  # pylint runs as an independent gate deliberately overlapping ruff's PL* rules.
  # Only formatter-owned checks, the docstring family, and too-few-public-methods
  # are disabled so it is usable out of the box; everything else stays on.
  disable = [
    "line-too-long",              # C0301 — ruff-format owns line length
    "missing-module-docstring",   # C0114
    "missing-class-docstring",    # C0115
    "missing-function-docstring", # C0116
    "too-few-public-methods",     # R0903 — trips dataclasses / config / Protocol classes
  ]

  [tool.pylint.design]
  max-args = 10
  max-positional-arguments = 10
  max-branches = 20
  ```
- **`[tool.tox.env.style].commands`** — add `["pylint", "src"]` after the
  type-checker cluster (basedpyright/ty/pyrefly/zuban), before `vulture`.
- **Style-env import resolution** — pylint does import-based inference, so the
  `style` env must be able to import the package and its optional components.
  Verify the `style` env installs extras (it currently type-checks component code
  with basedpyright/mypy, so extras appear resolvable); if pylint emits
  `import-error` on an optional component (e.g. `textual`), add `extras = ["all"]`
  to `[tool.tox.env.style]`.

### `template/prek.toml.jinja`

- Add a **`local`** pylint hook (not an upstream `rev`-pinned repo):
  ```toml
  { id = "pylint", name = "Pylint", entry = "uv run --locked --group style pylint src",
    language = "system", pass_filenames = false, always_run = true }
  ```
  Rationale: pylint needs the installed package for inference, and a local hook
  single-sources its version in the `style` group — matching how `basedpyright`,
  `editorconfig-checker`, and `sphinx-lint` are already wired. `pass_filenames =
  false` keeps the invocation to the canonical `pylint src`.

### Docs

- If the template documents its quality gates (README / a tooling doc), add
  pylint to that list. (Confirm location during implementation.)

## Verification (before opening the PR)

1. `copier copy` the branch into a scratch project with representative components
   (at least `include_cli` + `include_tui`, matching olink).
2. `tox -e style` → pylint runs and passes green on the generated skeleton; tune
   the baseline only if the *generated* code legitimately trips a check.
3. `prek run pylint` → green.
4. Confirm no `import-error` on optional components (apply the `extras` fix if
   needed).
5. `copier update --pretend` on an existing generated project still converges
   (no unrelated churn).

## Rollout to olink (separate follow-up, not this PR)

After this merges and the template tags a new version, olink pulls it via
`copier update` (3-way merges the pylint config + `style` dep). Then verify
olink's `tox -e style` passes with pylint and tune olink source or the shared
baseline if needed. olink's original project-specific `ignore-paths` for tests is
subsumed by the generalized baseline.

## Risks / trade-offs (accepted)

- **Duplicate findings** vs ruff `PL*` — accepted (belt-and-suspenders).
- **Slower `style` gate** — pylint is the slowest linter in the stack.
- **Baseline tuning** — heavy-component projects may surface findings needing a
  small addition to the shared `disable` list; discovered in verification.

## Out of scope

- Making pylint optional/toggleable (explicitly rejected — always-on).
- Linting tests with pylint (ruff owns tests).
- Reconciling ruff/pylint overlap by trimming either rule set.
