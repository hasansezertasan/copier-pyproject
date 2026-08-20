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
included in the default CI run for inline `>>>` snippets that cannot use
`literalinclude`.

## Consequences

Documentation code now fails the same local and CI checks as a stale import in
the application. Examples remain close to the docs and out of built wheels;
users who need distributable demonstrations can use the independent
`include_examples` scaffold option.
