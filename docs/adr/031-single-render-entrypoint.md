# ADR-031: One render entrypoint, and generate-and-verify on top of it

## Status

Accepted (2026-09). Builds on
[ADR-024](024-render-and-inspect-template-test-suite.md) (the render harness)
and generalizes [ADR-012](012-cobo-for-gitignore-generation.md)'s drift-guard
posture. Resolves issues #181, #183, #164, #184.

## Context

"Render this template with these answers" is the repo's single most-performed
operation, and it had started to fork. The render harness (ADR-024) put a real
`copier.run_copy` in `tests/conftest.py`; `template-ci.yml` carried its own
inline `uvx copier copy`; the `example` mise task carried a third; and three
open proposals each shipped a fourth, fifth and sixth — a `scripts/regenerate.sh`
(#181), a `scripts/render-doc-trees.sh` (#164), and a `scripts/watch.py` (#184).

Six spellings of one operation means six places where the answers baseline, the
`vcs_ref`, or the `--defaults` handling can quietly disagree — and a CI matrix
that renders a shape no other consumer can reproduce is exactly the failure the
harness exists to prevent.

Separately, #181 asked for a *generate-and-verify convention*: the cobo
`.gitignore` fence proves a derived file still matches its source, and the repo
has other files that should be derived but are hand-maintained — most
importantly the documented structure of a generated project (#164), which is the
first thing a scaffolding template's docs get wrong.

## Decision

### 1. `tools/render.py` is the only place `copier.run_copy` is called

A plain Python module, not a shell script — the pytest harness must be able to
call the same code path (a shell script it cannot import would leave two
renderers again). It carries PEP 723 metadata, so it is equally runnable as
`uv run tools/render.py …` with no root Python project and no mise shim, which
is what CI and the mise tasks use.

Consumers:

| Consumer | Call |
| --- | --- |
| render harness (ADR-024) | `tests/conftest.py`'s `render` fixture wraps `render()` |
| generate-and-run CI (#183) | `uv run tools/render.py render ../rendered --data …` |
| committed docs artifacts (#164) | `regenerate()` |
| authoring watch loop (#184) | `watch()` |
| `mise run example` | `render` subcommand |

Answers layer as `IDENTITY` → `--data-file` → explicit answers. Programmatic
renders (the harness) use only `IDENTITY`, a neutral `octocat`/`example` pair
that keeps golden files stable no matter what a maintainer puts in their own
`.example-input.yml`; the CLI defaults to `.example-input.yml` on top, which is
what CI and `mise run example` want.

### 2. `docs/generated-project-trees.md` is generated, not typed

`regenerate` renders each of the four presets (ADR-016) and writes the exact
file set each produces into one committed Markdown page. A preset that gains or
loses a file updates the docs mechanically, and the diff — "this toggle adds
these five files to `full`" — is review signal that hand-written structure prose
never produced. Plain fenced blocks, no `<details>`: the repo's markdownlint
config leaves MD033 (inline HTML) enabled.

The page is **committed** (not built into a gitignored `_generated/` dir) for
exactly that diff. `example/` stays gitignored and stays a pure smoke-test
target of the same entrypoint — a diff-based guard cannot apply to an untracked
tree, which answers #181's open question.

### 3. Two drift guards, one per direction of drift

The artifact can go stale two ways, and each gets the check that fits it:

- **This repo changed** (a toggle gains or loses a file) —
  `tests/test_doc_trees.py` asserts the committed page equals a fresh render, in
  the existing **blocking** `render-tests` job. It costs nothing extra (that job
  already renders every preset) and fails on the PR that causes the drift, not a
  week later.
- **The toolchain changed underneath us** — the render path installs copier
  unpinned, so a new copier release can change what the template emits with no
  commit here at all. That is the same upstream-drift shape cobo's weekly check
  exists for, and a PR-time check cannot see it, so `artifact-drift.yml` runs
  `regenerate` + `git diff` on a **weekly schedule + `workflow_dispatch`**,
  non-blocking, never on `pull_request` — the posture of `gitignore-drift.yml`
  (ADR-012) and `docs-linkcheck` (ADR-011).

Golden files (ADR-024) are deliberately **not** folded into `regenerate`: they
are already gated by the same job, and `--force-regen` is their documented
regeneration path.

### 4. Generate-and-run brackets the presets

`template-ci.yml`'s render matrix — render → zizmor → formatter-canonical →
`tox -e style` → `tox run -e 3.12` — already was the generate-and-run guard #183
asked for; what it lacked was the preset bracket. Its kitchen-sink scenario is
now spelled `--data preset=full` instead of a hand-listed toggle set (with
`minimal` as the `library` bracket), so a component added to `preset_map`'s
`full` is exercised end-to-end without editing the matrix.

### 5. The watch loop is an authoring aid, never a gate

`watch` re-renders into the gitignored `.watch-render/` on every save under
`template/`, `copier.yml` and `.example-input.yml`, printing a per-rebake status
line and surviving a failed render. Because each rebake `rmtree`s its target,
`--out` is validated first: never a path touching a watched source (either
direction), and never a directory that is non-empty without a
`.copier-answers.yml`. The second rule is the load-bearing one — "do not delete
what this tool did not render" is checkable, whereas enumerating which
directories are precious (`docs/`, `tools/`, someone's `~/notes`) is not. `watchfiles` is not a dependency of the
script — `mise run watch` supplies it with `uv run --with watchfiles` — so no
consumer pays for a dependency only the loop needs.

## Consequences

- One code path to change when rendering changes (a Copier API shift, a new
  always-on answer). A new consumer imports `render()` or calls the CLI; adding
  a seventh `copier copy` invocation is a review defect.
- The documented project structure cannot silently rot: a PR that changes what a
  preset renders must run `mise run regenerate` or fail `render-tests`.
- `regenerate` is the extension point for future derived artifacts (an AsyncAPI
  schema, a CLI reference) — they plug in there rather than growing a second
  generator, and inherit both drift guards for free.
- One more weekly cron to keep an eye on (`artifact-drift.yml`). It renders and
  diffs, so it costs a few CI minutes a week and fails only on a real upstream
  change; a failure is fixed by `mise run regenerate`.
- The `full` preset is now exercised by the heaviest CI scenario, so a
  toggle-interaction break in the kitchen sink fails against the offending diff.
  Its cost is one existing matrix cell, not a new job.
- `tools/render.py` is import-reachable from the tests because the repo root is
  on `sys.path` under pytest (`tests/__init__.py` + prepend import mode). A
  future root `pyproject.toml` must keep that true.
