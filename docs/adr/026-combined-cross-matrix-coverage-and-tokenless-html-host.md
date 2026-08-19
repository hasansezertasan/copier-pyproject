# ADR-026: Combine coverage across the CI matrix + optional tokenless HTML host

## Status

Proposed (2026-08). Extends the intra-job coverage merge documented in
[ADR-008](008-worker-broker-testing-strategy.md) to the whole CI fan-out.
**Superseded in part** by [ADR-027](027-per-component-markers-and-path-filtered-ci.md):
the single union `fail_under` gate below is decomposed into N per-component gates
once the `ci` job splits per component, so a path-skipped component keeps the merge
gate green. The union-over-cells *principle* still holds — ADR-027 applies it
per component (across that component's OS cells) rather than once across all code.

## Context

Coverage was handled **per matrix cell**: each `ci` job ran `coverage combine`
(merging its own per-interpreter `.coverage` files), `coverage report`, and
`coverage xml`, and each OS uploaded its own `coverage.xml` to Codecov
independently. `[tool.coverage.paths]` remaps the `src/` and `site-packages/`
layouts so per-interpreter data merges correctly *within* a job (ADR-008), and
the `fail_under = 99` gate fired *per cell* — every OS had to hit 99% on its own.

Two gaps remained:

1. **No authoritative cross-fan-out number.** Each OS uploaded separately, so a
   line covered on Linux but version/OS-gated off on Windows was reported
   inconsistently depending on which upload Codecov reconciled. There was no
   single combined report spanning every OS × interpreter cell, and the per-cell
   `fail_under` gate measured each cell rather than the union it should.
2. **Coverage HTML had nowhere to live by default.** Codecov is opt-in and
   non-blocking (a private repo with no token gets only a `::notice::` skip), so
   a self-contained project had no hosted, browsable coverage report at all.

## Decision

### 1. Per-cell coverage artifacts → a single `coverage-combine` job

Each `ci` matrix cell now `coverage combine`s its per-interpreter data, keeps a
**non-gating** `coverage report --show-missing --fail-under=0` for fast per-OS
feedback, renames `.coverage` → `.coverage.${{ matrix.os }}`, and uploads it as a
per-OS artifact (`coverage-${{ matrix.os }}`, `include-hidden-files: true` — the
data file is a dotfile).

A dedicated `coverage-combine` job (`needs: ci`) downloads every `coverage-*`
artifact (`merge-multiple: true`), then runs the merge once:

```text
coverage combine
coverage report --show-missing --fail-under=99   # the single gate
coverage html
coverage xml
```

This is now the **only** place the `fail_under = 99` gate is enforced, and it
measures the **union** of every OS × interpreter cell — the correct scope. A line
covered on one OS but gated off on another only balances in the union, so a
per-cell gate would either be too strict or mask a real cross-OS gap. The per-cell
`coverage report` stays for quick local feedback but deliberately does not gate.

`relative_files = true` is added under `[tool.coverage.run]` so `.coverage` files
produced on different runners/OSes merge without absolute-path mismatches. It
complements (does not replace) the existing `[tool.coverage.paths]` remap, which
unifies the `src/` vs `site-packages/` layouts.

The single combined `coverage.xml` becomes the **one** Codecov upload point,
carrying forward the existing opt-in/non-blocking gating unchanged
(`CODECOV_TOKEN_SET` / `REPO_IS_PUBLIC` presence flags, tokenless on public repos,
`::notice::` skip only on a private repo with no token). `coverage-combine` joins
the `check` aggregation gate. When `include_sonarcloud` is set, the `sonar` job
now `needs: coverage-combine` and consumes the **combined** `coverage-xml`
artifact rather than the former Ubuntu-only per-cell one.

Because the matrix is symmetric (three OSes, each running the full `tox run`),
there is no skipped-component subtlety: every cell measures the same code, so the
combined gate runs on every push/PR with no full-build-only carve-out.

> **Amended by [ADR-027](027-per-component-markers-and-path-filtered-ci.md).** Once
> the `ci` job splits into path-filtered per-component jobs, the matrix is no longer
> symmetric — an unchanged component is skipped, dropping its subtree from a single
> union. ADR-027 therefore decomposes this one gate into per-component gates, each
> combining across its own OS cells and scoped to its subtree via
> `coverage report --include`/`--omit`.

### 2. Optional tokenless HTML host via smokeshow (`include_smokeshow`)

For public repos there is a zero-account way to publish `htmlcov/`:
`smokeshow upload htmlcov` uploads to an ephemeral public URL and prints it, with
no secret required (an optional key only raises rate limits). This matches the
template's self-contained, "green on first push, no external accounts" posture —
it gives a public project a browsable coverage report without a Codecov account.

It is gated behind a new `include_smokeshow` boolean (`default: false`), following
the ADR-009 opt-in posture, and — like the Codecov upload — runs only on public
repos (`if: ${{ env.REPO_IS_PUBLIC == 'true' }}`) so a private report is never
published. Codecov remains the primary coverage host; smokeshow is a
supplementary, account-free HTML mirror.

Because smokeshow's tokenless endpoint has lower rate limits, the step is
**best-effort** (`continue-on-error: true`) and ordered **last** in the job —
after the Codecov and `coverage-xml` uploads. A transient outage or rate-limit
must never fail the `coverage-combine` job (which would block the merge-required
`check` gate) nor abort the authoritative Codecov upload; this gives smokeshow the
same non-blocking guarantee the Codecov step gets from `fail_ci_if_error: false`.

## Consequences

- New `copier.yml` boolean `include_smokeshow` (`default: false`) with `help`
  describing the tokenless, public-repo-only scope; added to the `full`
  `preset_map`. `.example-input.yml` uses the `library` preset, so the smokeshow
  step's rendered form is only validated when generated explicitly (CLAUDE.md
  testing convention).
- `template/.github/workflows/ci.yml.jinja`:
  - The `ci` job's `Coverage`/`Upload coverage`/`Note skipped`/per-cell
    SonarCloud-upload steps are replaced by `Store coverage data` (combine +
    non-gating report + rename) and `Upload coverage data` (per-OS artifact). The
    now-unused `env:` presence flags move off the `ci` job.
  - A new `coverage-combine` job holds the single merge, the `fail_under` gate,
    the HTML/XML render, the `coverage-html` artifact, the single Codecov upload
    (with the unchanged gating), the SonarCloud `coverage-xml` upload
    (`{% raw %}{% if include_sonarcloud %}{% endraw %}`), and — ordered last and
    best-effort — the optional smokeshow step
    (`{% raw %}{% if include_smokeshow %}{% endraw %}`).
  - `sonar.needs` and `check.needs` gain `coverage-combine`.
  - The job stays zizmor/ghalint-green like every workflow (`permissions: {}`
    top-level, `contents: read`, `persist-credentials: false`, `timeout-minutes`,
    SHA-pinned `uses:`; `matrix.os` in `run:` mirrors the existing System Info
    step, a trusted context).
- `template/pyproject.toml.jinja`: `relative_files = true` under
  `[tool.coverage.run]`. Captured by the golden `pyproject.toml` snapshots
  (`tests/test_golden_files/`).
- Coverage measurement is **unchanged** — only how it is aggregated (union, not
  per-cell) and published (single Codecov upload, optional smokeshow HTML). What
  *when* a regression fails shifts from per-cell to the union, which is more
  correct: the gate should measure the union.
- `coverage` in the combine job runs via `uv run --locked --only-group test
  coverage` — this pins the **same** coverage version that produced the
  `.coverage.*` data files (via the locked `test` group) so it never drifts from
  an unpinned resolve, while `--only-group` skips building the project (reading
  data + config needs no project install).
- `CLAUDE.md`, `README.md`, and `docs/template-architecture.md` document the
  toggle and the new job.
