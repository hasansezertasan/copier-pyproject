# ADR-024: Render-and-inspect test suite for the template

## Status

Proposed (2026-08).

## Context

The template's correctness — "does it still render, and is the output
structurally valid, across the presets and toggle combinations we ship" — is its
single most important property, and until now it had no automated guard. It was
validated by hand: regenerate `example/` from `.example-input.yml` and eyeball
it, or run the generated project's own suite. That covers exactly **one** option
set (the `library` preset) and only when a human remembers.

A Jinja mistake that emits malformed YAML in a *conditional* file, a broken
render under the `tool`/`web`/`full` presets, or a whitespace-control regression
in a guarded block can all merge green — the `example/`-based check never renders
the other presets, and CI never renders the template at all outside the heavier
`template-ci.yml` generate-and-run matrix.

Two distinct testing strategies are possible, with very different cost:

- **Render-and-inspect** — render the template programmatically and assert on the
  *output tree* (files exist, YAML/TOML parse, key artifacts match a snapshot).
  No installation of the generated project, so it is fast and can fan out across
  many option combinations.
- **Generate-and-run** — render, then `uv sync` and run the generated project's
  own `tox`/`pytest`. This proves the generated project *works*, but is slow and
  heavy; it already exists as the `template-ci.yml` matrix.

## Decision

Adopt **render-and-inspect** as the fast, matrixed correctness layer, distinct
from and complementary to the heavier generate-and-run matrix.

### Render via Copier's Python API, not `pytest-copie`

The `render` fixture in `tests/conftest.py` calls `copier.run_copy` directly with
`vcs_ref="HEAD"`, giving full control over `data=` and adding no dev dependency
beyond copier itself (which the harness already needs). `pytest-copie`'s terser
fixture does not earn a second dependency here.

### Three structural failure modes hand-regeneration misses

1. **Renders at all** for every preset — `library`, `tool`, `web`, `full`
   (ADR-016) — plus high-signal toggle combos: one render per `worker_broker`
   and one per `web_framework`, so every conditional broker/framework branch is
   exercised without an exhaustive cross-product.
2. **Every generated YAML parses** (`yaml.safe_load_all` over `rglob("*.y*ml")`)
   — the cheapest guard against a Jinja conditional or whitespace-control bug
   emitting broken YAML in a file the single-preset `example/` never renders.
   `yaml` is available in the harness as a transitive dependency of copier.
3. **`pyproject.toml` is valid TOML** (`tomllib.loads`, stdlib).

These live in `tests/test_render_validity.py`.

### Golden-file snapshots for a few high-value artifacts

`tests/test_golden_files.py` uses `pytest-regressions`' `file_regression` to
snapshot the rendered `pyproject.toml` for the `library` and `full` presets — the
two extremes of the toggle space — into `tests/test_golden_files/`. An unintended
change to a core rendered file becomes a reviewable diff instead of silent drift.

Snapshots are regenerated with `pytest ... --force-regen` (wrapped as
`mise run test-golden-update`); the diff is reviewed before committing — a
legitimate template change updates the golden, an unexpected one is the
regression this catches. The scope is kept **deliberately small** (a couple of
stable artifacts) so the snapshots stay signal rather than churn: `pyproject.toml`
carries dependency pins that move on template updates, so a broad golden set
would be a churn magnet without added coverage.

### Wiring

The suite runs in the existing `render-tests` job of `template-ci.yml` (`uv run
--with pytest --with pytest-regressions --with copier pytest tests/`). No root
Python project exists — the template repo's tooling is mise-managed — so the
harness deps come from an ephemeral uv env, consistent with the pre-existing
render harness.

## Consequences

- Preset and conditional-file render regressions fail against the offending diff
  in CI, not silently at release time or when a human next regenerates `example/`.
- This is the foundation the author watch/rebake loop and further inspection
  tests build on; it reuses the one `render` fixture.
- It does **not** replace the generate-and-run guard (`template-ci.yml`'s render
  → style → tox matrix): "does it render and is it structurally valid" is a
  strictly weaker (and far cheaper) property than "does the generated project's
  own suite pass". The two layers are kept separate on purpose.
- Golden files add a maintenance contract: an intentional change to the rendered
  `pyproject.toml` for `library`/`full` requires a `--force-regen` and a reviewed
  diff. Kept to two artifacts so that cost stays negligible.
- No `copier.yml` `_tasks` are introduced (ADR-015): rendering happens in-process
  from the test harness, never as a post-copy task, so Renovate's hosted copier
  manager (which disallows `--trust`) is unaffected.
