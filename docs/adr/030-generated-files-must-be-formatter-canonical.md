# ADR-030: Generated files must be formatter-canonical

## Status

Proposed (2026-09).

## Context

The template's promise is that a freshly scaffolded project is green on its first
push. Several shipped files did not keep it: they rendered as *valid* YAML/TOML
but not in the form the generated project's own formatters produce, so the very
first `prek run --all-files` rewrote them, the generated repo's `hooks` CI job
failed, and every later `copier update` showed drift the adopter never caused.

On a pristine `v1.3.0` scaffold (issue #213):

| Command | Exit | Files rewritten |
| --- | --- | --- |
| `mise run prek` | 1 | `.github/workflows/ci.yml`, `.github/ISSUE_TEMPLATE/bug_report.yml` (yamlfmt) |
| `mise run style` | 0 | `pyproject.toml`, `prek.toml` (taplo, fix mode) |

Nothing caught either. This repo's own gates run only *checking* tools over a
render: `prek run zizmor` in `template-ci.yml`'s `render` job, plus
`tox run -e style`; [ADR-024](024-render-and-inspect-template-test-suite.md)'s
harness asserts rendered YAML *parses*, not that it is canonical. The taplo case
was worse than invisible — the `style` env ran taplo in **fix** mode, so it
rewrote the files and still exited 0, leaving CI green and the worktree dirty.

A third instance was latent rather than cosmetic: `.cspell.yml` rendered author
tokens through Jinja's `tojson`, which escapes non-ASCII to `\uXXXX`. yamlfmt
normalizes those back to the literal character, so **any** adopter with a
non-ASCII name plus MegaLinter enabled got a file their own hooks rewrote.

## Decision

**"Renders as valid YAML/TOML" is necessary but not sufficient. A generated file
must already be in the exact form the generated project's own formatters would
produce** — the auto-fixing hooks (yamlfmt, ruff-format, the prek builtins) and
taplo, not only the lint-only tools.

Three things follow.

### 1. Formatter configuration is chosen so the *hand-written* layout is canonical

Where a formatter's default would reflow shipped files by width, the shipped
config turns that off rather than the template chasing the output:

- `.github/yamlfmt.yml` sets `retain_line_breaks_single: true`. The basic
  formatter otherwise drops **every** blank line, and the blank lines between
  jobs and step groups in a 1,300-line `ci.yml` are deliberate structure. The
  `_single` variant (not `retain_line_breaks`) collapses runs of blank lines to
  exactly one, which keeps the formatter idempotent.
- A new `.taplo.toml` sets `array_auto_expand = false`, `array_auto_collapse =
  false` and `align_comments = false`. Width-driven reflow would make the
  canonical form of a generated file depend on *which components are enabled*
  (`prek.toml` one-lines mypy's `additional_dependencies` with two components and
  explodes it with six), and comment alignment would let a Renovate bump of one
  pin break the gate on a line nothing touched.

`max_line_length` is deliberately **not** set for yamlfmt: it re-wraps folded
scalars across files the template does not otherwise touch, trading one class of
churn for a larger one. Long rendered lines are acceptable — yamllint's
`line-length` is configured at `level: warning`.

### 2. Template sources are written in the canonical form

The remaining drift was in the templates, and is fixed at the source: folded
`>-` scalars are emitted on one line (yamlfmt joins them), a comment may not
trail a sequence (yamlfmt re-indents it to the sequence's level), TOML arrays are
2-space indented one-item-per-line with a trailing comma, trailing comments carry
one space, and Jinja whitespace control (`{%- … %}`) is used so a conditional
block never leaves more than two consecutive blank lines or a blank line at EOF.

`.cspell.yml` emits literal UTF-8 author tokens — double-quoted with `"`/`\`
escaped by hand — instead of `tojson`.

### 3. taplo runs as a strict `--check` gate

The `style` env's `taplo format` becomes `taplo format --check --diff`. Fix mode
was load-bearing for the invisibility of the defect: a gate that repairs its
input and exits 0 reports nothing. Its `NOTE` ("kept in fix mode because the
rendered TOML is not yet guaranteed taplo-formatted") is now obsolete.

### Guard

`template-ci.yml`'s `render` job gains one step per scenario, reusing the shape
of the existing `prek run zizmor` step — the rendered project's *own* hooks, no
generated-project install:

```yaml
run: |
  for hook in yamlfmt end-of-file-fixer trailing-whitespace; do
    uv run --group prek prek run "$hook" --all-files --show-diff-on-failure
  done
  git diff --exit-code
```

The `git diff --exit-code` is the gate, not the hooks' exit codes: a fixing hook
that rewrites a file and still exits 0 — exactly the taplo failure mode above —
would sail through an exit-code-only check. The other fixers are covered by
`tox run -e style`, which runs them in check mode (`ruff format --check`, and now
`taplo --check`).

An `integrations` scenario is added to the matrix for the toggles no other
scenario rendered (`include_megalinter`, `include_repo_settings`,
`include_repo_ruleset`, `include_homebrew`, `include_scoop`), with an explicitly
non-ASCII `author_full_name` so the `.cspell.yml` case stays guarded regardless
of what `.example-input.yml`'s own name is.

## Consequences

- A generated project is formatter-clean on first run: `prek run --all-files`
  and `tox -e style` leave the worktree untouched, and `copier update` diffs show
  only real template changes.
- Template YAML/TOML must be written the way the formatters want it. Hand-aligned
  trailing comments and hand-wrapped folded scalars are no longer available; the
  guard fails the PR that introduces one, with the diff in the log.
- Adding a conditional block to a rendered YAML/TOML file now requires thinking
  about Jinja whitespace control, because stray blank lines are a gate failure
  rather than cosmetic.
- The guard costs one extra step per `render` matrix cell (three prek hooks, no
  install) plus one more matrix cell.
- The two formatter configs are pinned to non-default behavior. If a future
  yamlfmt/taplo release changes those knobs' semantics, the guard fails loudly on
  the next render rather than drifting silently — which is the point.

## Amendment (2026-09): a shared helper for collection literals

A Python tuple or list literal rendered from a Jinja loop has no single correct
spelling: with `skip-magic-trailing-comma` on, ruff-format collapses it to one
line when the whole statement fits in 88 columns and explodes it one element
per line otherwise. A template that always emits one form ships a file the
adopter's first `prek run --all-files` rewrites — the exact failure this ADR
exists to prevent — and the width depends on values only known at render time
(a package name, a broker module, how many components are enabled).

`py_collection(name, items, kind)` in `_macros.jinja` does that branch once.
The file sits at the **repository root**, outside `_subdirectory`, so it is a
template input that can never be rendered into a generated project, and needs
no `_exclude` override (which would replace copier's default exclude list
wholesale). Templates import it on their first line.

Used for `__all__`, the component dependency allowlists and the guard tuples in
`__main__.py`, `cli/app.py` and `tests/test_main.py`. A second hand-written copy
of the width branch is the drift it replaced.
