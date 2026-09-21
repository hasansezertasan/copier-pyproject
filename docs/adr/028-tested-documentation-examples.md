# ADR-028: Tested documentation examples

## Context

Pasted Python fences in generated documentation can silently drift from the
package API: neither the test suite nor the type-checker and lint gates execute
them. The template's high coverage threshold and broad static-analysis matrix
otherwise make that inconsistency particularly easy to miss.

## Decision

Generated projects keep complete Python examples in `docs/examples/`. Sphinx
pages render these files with `literalinclude`, so published code is the exact
source that the regular pytest suite imports and, when appropriate, calls.

`docs/examples/` is explicitly included in Ruff, mypy, basedpyright, ty,
pyrefly, zuban, and pylint scope. It is not part of the package or coverage
source set: examples document the package rather than constitute product code.

The Sphinx `doctest` extension is enabled, with a `docs-doctest` tox environment
for inline `>>>` snippets that cannot use `literalinclude`. CI runs it in a
dedicated `docs-doctest` job wired into the `check` gate — the per-component
`test-*` jobs pass `tox run -- -m <marker>`, which replaces tox's default env
list, so doctests would otherwise never run.

Markdown follows a separate, pytest-native convention: the generated top-level
`README.md` is a `testpaths` entry and pytest collects only that filename with
`--doctest-glob=README.md`. Its `pycon` examples therefore run in the ordinary
test suite, while other Markdown files remain prose unless they are explicitly
adopted as a doctest surface. Pytest enables `ELLIPSIS`,
`IGNORE_EXCEPTION_DETAIL`, and `NORMALIZE_WHITESPACE` for those examples.

Two mechanics make that boundary hold rather than merely describe it:

- `--doctest-glob` matches a **basename**, and `tests` is a recursive
  `testpaths` entry, so any future `tests/**/README.md` would be collected the
  moment it contained a `>>>` line. `tests/conftest.py` sets
  `collect_ignore_glob = ["*.md"]`, keeping the root README the whole surface.
- The generated prek `pytest` hook runs bare `pytest`, not `pytest tests`. An
  explicit target replaces `testpaths`, which would let a broken README doctest
  pass the advertised local hook and surface only in a later tox/CI run.

doctest cannot see Markdown: it ends an example's expected output at the first
blank line, so a closing ``` immediately after an output line is read as part
of that output. Every README example therefore leaves a blank line before its
closing fence, and the README's authoring TODO states the rule where the next
example gets written.

## Consequences

Documentation code now fails the same local and CI checks as a stale import in
the application. Examples remain close to the docs and out of built wheels;
users who need distributable demonstrations can use the independent
`include_examples` scaffold option.

The Sphinx builder owns `.rst` prose and pytest owns the curated Markdown
surface; neither collector overlaps the other.
