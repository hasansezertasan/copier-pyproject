# ADR-028: Per-component pytest markers + path-filtered CI jobs

## Status

Proposed (2026-08). Generalizes the single `integration` marker from
[ADR-008](008-worker-broker-testing-strategy.md) to a per-component scheme, and
**supersedes in part** [ADR-026](026-combined-cross-matrix-coverage-and-tokenless-html-host.md):
its single **union** coverage gate is decomposed into N per-component gates.
Its matrix and draft policy are defined by
[ADR-029](029-asymmetric-ci-matrix-and-draft-pr-skip.md).

## Context

ADR-008 introduced one `integration` marker, deselected from the default suite and
run only in the Ubuntu-only `worker-integration` job — a binary default-vs-integration
split. ADR-026 then combined coverage across a **symmetric** OS × interpreter matrix
into a single `fail_under = 99` union gate, explicitly noting "there is no
skipped-component subtlety" because every cell measured the same code.

As the template grew optional components (`cli`/`web`/`gui`/`tui`/`mcp`/`worker`),
two coarsenesses remained:

1. **All component tests always ran**, even on a PR touching one component's tree —
   a one-line `web` change reran every other component's suite on every OS.
2. **No per-component selection knob** — a contributor could not say "run only the
   CLI tests" without hand-writing a `-k`/path filter.

## Decision

### 1. Per-component pytest markers, auto-applied by directory

`[tool.pytest.ini_options] markers` registers one marker per enabled component
(`core`, `cli`, `web`, `gui`, `tui`, `mcp`, `worker`) alongside `integration`. A
root `tests/conftest.py` `pytest_collection_modifyitems` hook applies `core` to
root-level tests and `pytest.mark.<dir>` from each test's top-level
`tests/<dir>/`, so no per-test
decoration or per-package `__init__.py` edit is needed and new files are covered
automatically. The recognised directory set is rendered from the enabled toggles.

The **default `tox run` is unchanged** (still everything minus `integration`).
Locally, `pytest -m web` / `-m "not worker"` now work out of the box; the worker's
integration subset stays reachable as `-m "worker and integration"`.

### 2. Path-filtered per-component CI jobs

A `dorny/paths-filter` `changes` job emits one boolean output per component plus
`core`. The monolithic `ci` job splits into `test-core` (always runs) and one
`test-<component>` per component, each gated on
`needs.changes.outputs.<component> == 'true' || needs.changes.outputs.core == 'true'`.
`core` is the escape hatch — it watches deps (`pyproject.toml`/`uv.lock`/`tox.ini`),
the shared `core/` tree, the package-root modules, the root `conftest.py`, and
root-level tests, so any change that underpins every component forces the full
fan-out (mirroring the import-linter layering, [ADR-014](014-import-linter-for-architecture-contracts.md)).
`worker-integration` gains the same gate, skipping its container spin-up on
unrelated PRs.

`check` already uses `re-actors/alls-green` with `toJSON(needs)`, which treats
**skipped** jobs as non-failing — so path-skipped and draft-skipped jobs keep the
merge gate green with no aggregator change.

### 3. Coverage decomposition (supersedes ADR-026's single union gate)

Per-component skipping is incompatible with a single union gate: a skipped job
drops its subtree from the combined data, so `fail_under = 99` fails on any partial
PR. The union gate is therefore **decomposed into N per-component gates**, one per
job:

- Each `test-<component>` cell uploads `coverage-<component>-<os>`; a
  `coverage-<component>` job merges that component's OS cells (preserving ADR-026's
  cross-OS union *within* a component — a per-cell gate would wrongly fail on a
  `sys.platform`/version branch) and enforces `fail_under = 99` **scoped** to the
  subtree via `coverage report --include="*/<pkg>/<component>/*,*/tests/<component>/*"`.
- `coverage-core` gates the package **minus** every component subtree via `--omit`.
  Because a CLI `--omit` overrides the pyproject `[tool.coverage.report] omit`, it
  re-adds `*/_version.py`; component gates pass only `--include`, so the config
  `omit` (including the worker integration file) still applies to them.
- Skipping a component is now **sound**, not a coverage loophole: an unchanged
  subtree has nothing to regress, so it needs no gate.

`source_pkgs` measures both `src/<pkg>` and `tests`, so each scope spans the
component's source **and** test subtree. All patterns are `*/`-anchored to match
both the editable `src/` and installed `*/site-packages/` layouts — the same
requirement as ADR-008's `omit` globs, verifiable only via a real `tox run`.

A central, **non-gating** `coverage-report` job (`if: !cancelled() &&
draft != true`) merges whatever component data is present, renders combined
HTML/XML, uploads to Codecov (unchanged opt-in/tokenless gating), optionally
publishes via smokeshow (ADR-026 §2), and feeds the SonarCloud job. Gating lives
in the per-component jobs; publishing stays centralized. The aggregate
report/HTML/XML is **scoped to the components that ran** (it `--omit`s any
component skipped this run, derived from the `changes` outputs): `source_pkgs`
otherwise makes coverage discover a skipped component's unexecuted files and
report them at ~0%, which would misreport the combined number on a path-filtered
PR.

### Matrix and draft policy

The per-component jobs use ADR-029's asymmetric matrix (full interpreter sweep on
Linux, one representative interpreter elsewhere; full grid under
`include_c_extensions`) and compose its draft guard into each job's `if`. Style
and installed-CLI checks are separate jobs so component marker arguments reach
pytest only.

## Consequences

- **More jobs on a full run.** A `core` change fans out to `(1 core + N components)`
  × OS jobs versus ADR-026's single 3-OS job; the win is on component-scoped PRs,
  which skip the rest. ADR-029's asymmetric matrix blunts the off-Linux per-job
  cost.
- **Coverage-scope patterns are the load-bearing risk.** `--include`/`--omit` must
  match both layouts; verify via `tox run` (installed wheel), never editable
  `pytest`. The root `conftest.py`'s defensive `except ValueError` branch carries a
  per-site `# pragma: no cover` (unreachable — all collected items are under
  `tests/`), following the ADR-008 pragma convention.
- **New components touch more surfaces.** Adding a component now updates: the
  marker list + `tests/conftest.py` `_COMPONENT_DIRS`, the `changes` filters, its
  `test-<component>` + `coverage-<component>` jobs, and the coverage
  `--include`/`--omit` lists. The CLAUDE.md "Adding New Optional Components"
  checklist enumerates these so they stay in lockstep.
- **No new toggle.** The markers and jobs derive from the existing `include_*`
  toggles; nothing added to `copier.yml` or `preset_map`.
- Files: `template/pyproject.toml.jinja` (markers), `template/tests/conftest.py.jinja`
  (new), `template/.github/workflows/ci.yml.jinja` (`changes` + `test-*` +
  `coverage-*` + `coverage-report`), `tests/test_markers.py` +
  `tests/test_ci_component_jobs.py`, and this ADR. Documented in `CLAUDE.md`,
  `docs/template-architecture.md`, and `README.md`.
