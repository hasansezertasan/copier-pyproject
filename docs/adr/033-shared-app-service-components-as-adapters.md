# ADR-033: One application payload, components as adapters over it

## Status

Accepted (2026-09). Extends the layering in
[ADR-014](014-import-linter-for-architecture-contracts.md) and the component
model in [ADR-019](019-components-as-cli-subcommands.md).

## Context

Every interface component answers the same two questions — what version is
this, and what is it running on — and every one of them answered it separately.
Before this change a generated `full` project carried **eight** copies of

```python
try:
    distribution = Distribution.from_name(PROJECT_NAME)
except PackageNotFoundError:
    ...
```

and **six** copies of the `platform.python_version()` /
`python_implementation()` / `system()` payload, spread across `cli/app.py`
(twice, in each of two framework variants), `web/app.py` (twice, in each of two
framework variants), `gui/app.py`, `tui/app.py`, `mcp/app.py` and
`worker/app.py`. The test suite carried six copies of the same
`_MissingDistribution` stub to poke at them.

Nothing enforced that they agreed. A component could — and the GUI and TUI
nearly did — drift on the payload's field names, on whether a missing
distribution is fatal, or on how it is logged. The import-linter contract
already says components may not import each other, so there was no path to
sharing short of putting the payload somewhere below them.

See issue #178.

## Decision

`core/app.py` — until now an empty placeholder module — holds the payload:

```python
def version() -> str: ...              # raises MetadataUnavailableError
def info() -> dict[str, str]: ...      # version + runtime environment
def info_or_unknown() -> dict[str, str]  # degrades the version, logs, never raises
```

plus `MetadataUnavailableError` and `UNKNOWN_VERSION`. Each component imports it
as `from <pkg>.core import app as service` and becomes an *adapter*: it decides
how to transport and present the payload, and how to report the single failure
mode in its own terms. The CLI exits 1, the web app answers 503, the MCP tool
returns error text, the GUI and TUI show `unknown`, the worker falls back to
`0.0.0`. Adding a component now means writing an adapter, not another copy of
the metadata lookup.

### It lives in `core`, not a new `base/` layer

Issue #178 proposed a new `base/` package "alongside or just above `core`".
`core` *is* the layer directly beneath the independent component group in the
import-linter contract, so a `base/` layer would add a name without adding a
boundary — and `core/app.py` already existed as the empty stub for exactly this.
The `layers` contract is unchanged; `exhaustive` stays satisfied. The module
renders only when a runnable component is enabled, so a library project keeps
the placeholder rather than gaining code nothing calls.

### Functions, not an `AppService` class

The issue proposed a class with a module-level instance. It would hold no
state, and the generated project's `ruff` config is `select = ["ALL"]` with
preview on, so `PLR6301` (no-self-use) flags exactly that shape; making every
method `@staticmethod` turns the class into a namespace, which is what a module
already is. Importing it as `service` keeps the issue's reading at the call
site — `service.info()` — with nothing to instantiate.

### No `VersionProvider` protocol

The issue's `@runtime_checkable` Protocol would have exactly one
implementation, no second one in prospect, and no caller that type-checks
against it. The issue's own guardrail — "a shared layer must *reduce* net
complexity, not add a framework" — rules it out. The contract is the module's
public functions, which the five type checkers already enforce at every call
site.

### Three functions, because there are three real behaviours

`version()` and `info()` raise; the transports that must fail (CLI, web, MCP)
map the error. `info_or_unknown()` degrades and logs a warning instead, because
a GUI dialog or TUI panel reporting "unknown" is more useful than one that
fails to open — and that was duplicated in both of them. There is no fourth
variant, and no configuration knob: each has more than one caller and no caller
needs anything else.

### What stays in the components

Logging stays with the adapter, because it genuinely differs: the CLI logs an
error without a traceback, the web app logs `.exception()`, the GUI degrades
with a warning. Only `info_or_unknown()` logs, since its two callers log
identically.

The worker's `VersionResponse` also keeps its own `platform` calls. It is a
*wire* model with its own field shape, published to a broker and pinned by the
AsyncAPI schema; routing two fields through a dict lookup would add indirection
for no sharing. What the worker does share is the metadata lookup behind
`__version__`.

### One test fixture instead of six stubs

`tests/conftest.py` gains a `missing_metadata` fixture that patches
`core.app.Distribution`. Because every component reads metadata through that
one module, the fixture reaches the CLI's exit-1 path, the web 503s, the MCP
error text and the GUI/TUI degradation alike — replacing the per-module
`_MissingDistribution` stubs.

## Consequences

- One place to change what an interface reports, and one place to test it.
  `tests/core/test_app.py` pins the payload's shape and both failure
  behaviours; each component test now asserts only its own transport.
- External behaviour is unchanged: the same field names, the same rendered
  strings, the same status codes and exit codes.
- Components gain a dependency on `core.app`. That is the direction the
  import-linter contract already mandates, so the contract needed no edit.
- A library project (no runnable component) renders `core/app.py` as the
  placeholder it was, so it gains nothing to maintain.

## Alternatives considered

- **A `base/` package with `AppService` and `VersionProvider`**, as the issue
  proposed. Rejected on all three counts above: the layer, the class and the
  protocol each add a name without adding a constraint.
- **Formalizing a transport/presentation split** — a separate presenter object
  per component. The issue raises it as optional; rejected here. Each adapter's
  presentation is three f-strings, and its transport is the framework's own
  decorator. Splitting them would produce more files than the code they hold.
- **Letting components keep their own lookups and adding a test that they
  agree.** Rejected: a conformance test tells you the copies have drifted after
  someone writes the sixth one. Removing the copies means they cannot.
