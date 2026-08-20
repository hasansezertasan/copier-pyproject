# ADR-028: Asymmetric OS/Python CI matrix + draft-PR skip

## Status

Proposed (2026-08). Narrows what the `ci` job in
`template/.github/workflows/ci.yml.jinja` runs per cell; leaves the coverage
aggregation of [ADR-026](026-combined-cross-matrix-coverage-and-tokenless-html-host.md)
and the packaging/worker guards of [ADR-007](007-standalone-executable-toggles.md)
/ [ADR-008](008-worker-broker-testing-strategy.md) untouched.

## Context

The generated `ci` job ran a 3-OS matrix (`ubuntu`/`macos`/`windows`) and, on
**each** OS, `uv run --locked tox run` executed the entire `env_list` — Python
3.10 through 3.14, plus `style` and (when `include_cli`) `cli`. That is
`3 × 5 = 15` full test runs per push, plus three redundant `style` runs, before
the standalone-build and worker-integration jobs even start.

The redundancy is structural, not incidental:

- Cross-platform bugs — path separators, line endings, signal handling, file
  locking — are overwhelmingly **interpreter-independent**. Finding them needs
  every OS, not every OS × interpreter pair.
- Interpreter bugs — a removed stdlib alias, a syntax/typing feature, a
  deprecation — are overwhelmingly **OS-independent**. Finding them needs every
  interpreter, not every pair.
- `style` is a lint/type-check env pinned to one interpreter; running it on three
  runners produces the same verdict three times.

Contributors also paid the full bill on **draft** PRs — work explicitly marked as
not ready for review.

## Decision

### 1. Full interpreter depth on Linux, one representative interpreter elsewhere

The `ci` matrix becomes an explicit `include:` list carrying a `tox_args` field
that the test step passes through:

```yaml
      matrix:
        include:
          - os: ubuntu-latest
            tox_args: ""
          - os: macos-latest
            tox_args: "-e py"
          - os: windows-latest
            tox_args: "-e py"
    # ...
      - name: Run the tests
        run: uv run --locked tox run ${{ matrix.tox_args }}
```

`-e py` runs the single tox env for the interpreter that invoked tox — the
`.python-version` interpreter `setup-python` installs — inheriting
`[tool.tox.env_run_base]` unchanged (same `coverage run --module pytest`, same
`package = "wheel"`). It therefore also skips the OS-independent `style`/`cli`
envs on the non-Linux cells.

Every OS still runs the suite; every interpreter still runs the suite. What is
dropped is only the *cross product*: 15 heavy runs become `5 + 1 + 1 = 7`.

Interpolating `matrix.tox_args` into `run:` is not a template-injection concern —
the values are literals defined in the workflow, not event-controlled input.

### 2. `include_c_extensions` keeps the full grid

A compiled extension makes each wheel ABI-specific — which is why the tox config
already switches to `package = "sdist"` so every interpreter compiles the
extension itself. There, every OS × interpreter pair genuinely *is* a distinct
build, so under `include_c_extensions` all three cells render `tox_args: ""` and
the matrix is the old full grid.

This is the only carve-out. **No new `copier.yml` toggle** was added: the one
class of project that needs the full grid is already declared by an existing
answer, and a `ci_full_matrix` question would add a prompt, a `preset_map` entry,
a README row, and documentation surface to express something the template can
already infer.

### 3. Draft PRs skip CI — every job, including `check`

Each job carries:

```yaml
    if: ${{ github.event.pull_request.draft != true }}
```

Two details make this correct rather than merely short:

- **`!= true`, not `== false`.** On `push` and `workflow_dispatch` there is no
  `pull_request` context, so `github.event.pull_request.draft` is empty;
  `== false` would be falsy and silently disable CI on pushes to `main`.
- **`check` is gated too.** `re-actors/alls-green` treats a *skipped* `needs` job
  as a failure unless it is listed in `allowed-skips`. Gating the work jobs while
  letting `check` run would therefore turn every draft PR red. Skipping `check`
  as well avoids that. Note what a job-level skip actually reports: GitHub
  records a skipped job as **success** for required-status-check purposes (only a
  *workflow*-level skip — path/branch filters, `[skip ci]` — leaves a check
  unreported and therefore pending). So a drafted PR ends up with a green,
  non-blocking `check` rather than a pending one. That is harmless: a draft PR
  cannot be merged regardless, and `ready_for_review` starts a fresh `check` run
  on the same head SHA that supersedes the skipped one, so the authoritative
  status once the PR is reviewable always comes from a real run. `check` keeps
  its `always()`:
  `if: ${{ always() && github.event.pull_request.draft != true }}`. `sonar`
  likewise keeps its existing fork guard, combined with the draft guard via `&&`.
- **`ready_for_review` is added to the `pull_request` `types:`.** It is *not* in
  the default set (`opened`, `synchronize`, `reopened`). Without it, a PR opened
  as a draft would skip CI and then never re-run it on "Ready for review" — the
  guard would silently become permanent. This line is load-bearing, not cosmetic.

## Consequences

- Roughly a 2× reduction in `ci` runner minutes per push for the default
  (non-c-extension) project, and no CI spend at all while a PR is drafted.
- A bug that requires a *specific* interpreter on a *specific* non-Linux OS
  (e.g. only Windows + 3.10) is no longer caught pre-merge in a default project.
  This is the accepted trade: such bugs are rare, and the escape hatch is a
  one-line edit to the rendered `ci.yml` (or enabling `include_c_extensions`'
  grid) in the projects that hit them.
- Coverage stays sound. The `fail_under = 99` gate lives in `coverage-combine`
  over the **union** of all cells (ADR-026), and the Linux cell still contributes
  every interpreter, so no version-gated line loses its covering cell. The
  non-Linux cells contribute one interpreter each, as before.
- `style` now runs exactly once (Linux), which is also where the `hooks` job's
  prek run already lives.
- The rendered `ci.yml` is the only file that changes; no `copier.yml` question,
  no `preset_map` entry, no new generated file.
- Guarded by `tests/test_render_validity.py`: the exact asymmetric `include:`
  list, the `include_c_extensions` full-grid fallback, the draft guard on *every*
  job (with `sonar`/`check`'s pre-existing conditions preserved), and the
  `ready_for_review` trigger type.
