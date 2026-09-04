# ADR-029: Asymmetric CI matrix and draft-PR skip

## Status

Proposed (2026-08). Extends the per-component CI topology from
[ADR-028](028-per-component-markers-and-path-filtered-ci.md) with the cost policy
from [issue #159](https://github.com/hasansezertasan/copier-pyproject/issues/159).

## Context

Running every supported interpreter on Ubuntu, macOS, and Windows repeats two
mostly independent dimensions. Cross-platform behavior usually needs every OS
at one representative interpreter; interpreter compatibility usually needs every
interpreter on one OS. Draft pull requests also paid for the entire generated CI
fan-out before they were ready for review.

The per-component split in ADR-028 adds two constraints. Style checks must not be
repeated in every component job, and marker arguments forwarded to pytest must
not reach the `cli` tox environment: doing so would call the installed command
with pytest's `-m` option instead of its default `version` argument.

## Decision

### Separate style and installed-CLI jobs

`style` runs once on Ubuntu. Because type checkers prune `sys.platform` branches
against their host, the style tox environment additionally runs mypy with
`--platform win32` and `--platform darwin`.

When `include_cli` is enabled, `cli-installed` runs `tox run -e cli` on all three
operating systems. This preserves the installed console-script check, including
Windows shims, without mixing its arguments with component marker selection.

### Asymmetric component-test matrix

Each `test-*` job runs Python 3.10 through 3.14 on Ubuntu and the invoking `py`
environment on macOS and Windows. With `include_c_extensions`, every OS runs all
five interpreter environments because each OS/interpreter pair is a distinct
extension build. The workflow uses explicit tox environment lists so style and
CLI execution remain owned by their dedicated jobs.

### Skip every generated CI job on draft pull requests

Every job in `ci.yml` includes the falsy-safe condition
`github.event.pull_request.draft != true`. Unlike `== false`, this continues to
run on push and manual events where the pull-request object is absent. Existing
conditions are composed, not replaced: `check` retains `always()`, SonarCloud
retains its fork guard, and path-filtered component jobs retain their change
conditions.

The pull-request trigger explicitly includes `ready_for_review`. GitHub does not
include that action in the default trigger set, so without it a pull request
opened as a draft could remain permanently skipped after becoming reviewable.

The guard applies only to the generated `ci.yml`; independent security and docs
preview workflows continue to run on drafts.

## Consequences

- Default projects test every supported OS and interpreter without paying for
  their full cross-product.
- C-extension projects retain the full OS/interpreter build grid.
- Style runs once, while mypy retains static coverage of platform-gated code.
- The installed CLI is exercised on all operating systems with valid arguments.
- Draft pull requests skip the expensive test, coverage, packaging, and worker
  fan-out. Leaving draft starts a fresh authoritative run.
- A defect requiring one particular non-Linux OS and one non-representative
  interpreter may move past CI; this is the accepted cost trade-off.
