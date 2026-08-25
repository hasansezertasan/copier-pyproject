# ADR-028: Actionable component-dependency errors at the launcher boundary

## Status

Accepted (2026-08). Builds on the launcher wiring in
[ADR-019](019-components-as-cli-subcommands.md) (the console root and its
lazy-imported component subcommands) and the layering in
[ADR-014](014-import-linter-for-architecture-contracts.md).

## Context

The `<pkg>` console root lazy-imports each non-primary component (`<pkg> web`,
`<pkg> worker`, …), and a minimal launcher lazy-imports the primary one from its
default callback. When one of those imports hit a missing dependency, the user
got a bare `ModuleNotFoundError` traceback with no hint about the fix.

Two facts about this template constrain what the fix can say.

**There are no per-component extras to name.** Every component's runtime
dependency is a core `dependency` under its Jinja toggle;
`[project.optional-dependencies]` carries only an empty `all`, kept so the `dev`
group's `<pkg>[all]` resolves. So `pip install <pkg>[<extra>]` can never be the
right advice — the extra does not exist. A missing dependency module means the
*environment* is out of sync with the installed metadata: a `copier update` that
enabled a component without a re-sync, or a stale venv. The honest remedy is
`uv sync`.

**Guarding the launcher's own import is not enough.** The lazy imports in
`cli/app.py` are all first-party (`from <pkg>.web.app import main`), rendered
under the same toggle that put the third-party dependency in `dependencies`.
After a `copier update` the first-party module *is* present; what fails is the
third-party import one frame deeper, inside the component module. So the guard
has to sit around the import site and classify what comes out of it, rather than
replace the import with a `require()` call.

See issue #172.

## Decision

Wrap each launcher's lazy import in a private `_component_dependencies(component,
*dependencies, hint=...)` context manager that turns a missing **known**
dependency into an exit-1 message naming the component, the missing module, and
the fix. It is emitted only when the root actually lazy-imports something —
derived from `primary_component`, so a CLI-only project renders byte-identical to
before.

### Match dependency names exactly

The guard translates a `ModuleNotFoundError` only when `exc.name` is *exactly*
one of the component's declared dependency modules. A failure below an installed
dependency's namespace — a typo'd `from <dep>.user_plugin import X` in a
customized component — is an application defect, not a stale environment.
Suppressing its traceback to recommend `uv sync` would send the reader down the
wrong path, so it propagates untouched. A nameless `ModuleNotFoundError`
propagates for the same reason: the guard cannot tell whose failure it is.

### Import awkward dependencies eagerly (`_preflight`)

Exact matching only works on failures that (a) happen inside the guarded block
and (b) carry a module name. Two kinds of dependency satisfy neither:

- **Deferred.** `uvicorn` is imported when the web app calls `uvicorn.run()`,
  Tkinter when the GUI draws its window, `textual` when the TUI mounts — all
  *after* the guarded block has closed. Left alone, these degrade to a bare
  traceback or a generic `GuiDisplayError`/`TuiDisplayError` fallback.
- **Guarded re-exports.** `faststream.<broker>` re-exports the broker client
  behind faststream's own import guard, which raises a plain `ImportError`
  carrying **no** module name and advising `pip install "faststream[<broker>]"` —
  advice that bypasses this project's lockfile.

`_preflight(module)` imports such a module inside the guarded block and, when the
interpreter reports no name, re-raises as a `ModuleNotFoundError` naming the
module it was asked for. Because that name is supplied by the caller rather than
read off the exception, the attribution is precise, and the single translation
site in `_component_dependencies` keeps working unchanged.

This is why the worker's allowlist names `faststream.<broker>` and **not** the
broker client (`aiokafka`, `aio_pika`, …): faststream intercepts the client's own
`ModuleNotFoundError`, so a client entry would be dead. MCP needs no preflight —
`mcp/app.py` imports `mcp` at module scope, so the guarded import already reports
it by name.

### Tk gets a different hint

`tkinter` is the one dependency that is not a distribution: it is a
standard-library extension module that ships as a separate *system* package on
many platforms, so no dependency sync can install it. The GUI launcher therefore
passes a `hint=` naming the platform package (`python3-tk`, `python3-tkinter`) and
— because Homebrew's bare `python-tk` aliases the newest Python's formula, which
would install Tk for an interpreter the user may not be running — a
`python-tk@X.Y` built from `sys.version_info`. Its allowlist covers both `tkinter`
and the `_tkinter` C extension that `tkinter/__init__.py` imports unguarded: on
an interpreter built without tk-dev the pure-Python package still ships, and
`_tkinter` is the name that actually fails.

### Guard the console root's own module-scope imports

Some third-party modules are imported at the root's *module* scope, before the
guard inside `cli/app.py` exists: `typer` by the root itself, and — when
`include_pydantic_settings` — `pydantic`/`pydantic_settings` pulled in
transitively via `core.logging_setup` → `core.config`. `__main__.py` loads the
root through `_load_console_root()`, which applies the same translation and
re-raises anything else unchanged. `root_dependencies` is computed from the
enabled toggles, so a pure argparse root with no settings renders without the
guard.

### Derived facts live in `copier.yml`

`launcher_components`, `need_import_guard`, `launched_components`,
`component_label`, `component_preflight`, `preflight_used` and
`root_dependencies` are `when: false` computed variables. `cli/app.py.jinja`,
`__main__.py.jinja` and both test modules read them, so the four files cannot
drift on whether a guard is emitted, what a component's preflight module is, or
how it labels itself in an error message. Earlier revisions kept these as
per-file Jinja headers synchronized only by a `{#- Mirrors … -#}` comment.

## Consequences

- A stale environment produces one actionable line instead of a traceback, and
  the advice matches how the project is actually installed (`uv sync`, never a
  non-existent extra).
- Application import defects keep their diagnostics, which is the property the
  exact-match rule exists to protect. It is deliberately conservative: a genuinely
  ambiguous failure propagates rather than being mislabelled.
- `_preflight` catches `ImportError` broadly for the module it was asked to
  import, so a *broken* installation of that module is also reported as
  unavailable. That is the right summary for the launcher boundary, and the
  distinction does not change what the user must do.
- Coverage: the guard's error paths are unit-tested (no blanket `pragma`), with
  the deferred/nameless cases driven through `sys.meta_path` finders so the
  scenarios reproduce identically on any runner, whatever the host's Tk or
  faststream packaging.

## Alternatives considered

- **A shared `core/_imports.py` with `require(module, *, feature, extra)`**, as
  issue #172 proposed. Rejected on both halves: there is no `extra` to name, and
  a `require()` call replacing the launcher's first-party import would not have
  caught the actual failure, which happens one frame deeper. The eager-import
  need is real, and `_preflight` covers it at the boundary that already
  lazy-imports.
- **Guarding every component's module scope**, so a library consumer doing
  `import <pkg>.web.app` directly also gets the message. Out of scope here: it
  needs a decision about the sole-component `__main__` entrypoints
  ([ADR-007](007-standalone-executable-toggles.md)), which reach the same
  `core.config` chain unguarded. Tracked separately.
- **Letting faststream's own `ImportError` through.** Its message is actionable
  but recommends `pip install "faststream[<broker>]"`, which contradicts the
  lockfile-managed install this template ships.
