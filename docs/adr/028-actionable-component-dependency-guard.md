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
dependency is a core `dependency` under its Jinja toggle; generated projects
declare no `[project.optional-dependencies]` at all (see
[the no-empty-`all` decision](028-no-empty-all-extra.md)). So
`pip install <pkg>[<extra>]` can never be the right advice — the extra does not exist. A missing dependency module means the
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

`_preflight(module)` imports such a module inside the guarded block and re-raises
import failures as a `ModuleNotFoundError` naming the module it was asked for.
This includes nested failures from partially installed dependencies (for
example, `uvicorn` naming a missing `click` or the web framework naming a
missing `starlette`): the component owns the direct dependency, and `uv sync`
remains the appropriate repair. Because the name is supplied by the caller rather
than read off the exception, the attribution is precise, and the single
translation site in `_component_dependencies` keeps working unchanged. The sole
exception is `tkinter` naming its `_tkinter` C extension, whose precise name is
preserved for the system-level Tk hint.

This is why the worker's allowlist names `faststream.<broker>` and **not** the
broker client (`aiokafka`, `aio_pika`, …): faststream intercepts the client's own
`ModuleNotFoundError`, so a client entry would be dead. MCP does need a preflight
— `mcp` has transitive dependencies (e.g. `anyio`) whose import errors surface as
nested failures with unhelpful names; the preflight normalizes them to `mcp`.

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
root through `_load_console_root()`, which preflights each declared root
dependency to normalize transitive failures (e.g. `typer` missing `click`),
applies the same translation, and re-raises anything else unchanged.
`root_dependencies` is computed from the enabled toggles, so a pure argparse
root with no settings renders without the guard.

### Guard the sole-component entrypoint too

A project that enables exactly *one* runnable component has no console root
(`include_console_root` is false, so no `cli/` package is rendered) and
`__main__.py` binds that component directly. This is the ADR-007
standalone-executable entrypoint — what PyCrucible, PyInstaller and Nuitka all
target — and it was the one boundary the guard did not cover: the direct
`from <pkg>.<component>.app import main` reaches the component's own third-party
imports *and*, through `core.logging_setup` → `core.config`, the settings stack,
all before any guard existed. A stale environment therefore failed with a bare
traceback at exactly the boundary whose user is least equipped to read one — a
frozen binary's user has no CLI to fall back on. A GUI-only project, the shape
where a Tk-less interpreter is most likely, additionally got none of the Tk hint
machinery.

`_load_console_root()` could not be reused: it exists to import the *shared
launcher*, and these projects have none. `__main__.py` now renders a sibling
`_load_component()` for them, applying the same preflight, the same exact-match
rule and the same hints. Because the merged allowlist mixes real distributions
with `tkinter`, the hint is chosen per *module* rather than per component:
`_TK_HINT` for `tkinter`/`_tkinter`, `_SYNC_HINT` for everything else.

The five near-identical `elif include_<component>` branches collapsed into one
block parameterized by `sole_component`; the summary line and whether `main()`
returns an exit code are the only per-component differences left. See issue #268.

### Direct library imports stay unguarded

`import <pkg>.web.app` in a consumer's own code still raises a bare
`ModuleNotFoundError`, and that is deliberate — the first motivating case of
issue #172, resolved here as out of scope rather than left open.

Guarding it would mean wrapping every component's *module scope*, which buys
little and costs real things:

- The reader is already in a traceback in their own code, with the failing
  import and the frame that triggered it both visible. That is a better
  diagnostic than a one-line message, not a worse one, and `uv sync` is not
  necessarily the fix for *their* environment — they installed this package as a
  dependency of something else.
- A module-scope guard runs on the success path of every import, for every
  consumer, forever.
- Component modules are the part of a generated project an adopter edits most.
  A `try:`/`except ImportError:` wrapper around each one's imports is exactly
  the kind of scaffolding that gets in the way.

The guard therefore covers *entrypoints* — the two places where this package
chose to launch something and owns the error surface — and nothing else.

### Derived facts live in `copier.yml`

`launcher_components`, `need_import_guard`, `launched_components`,
`component_label`, `component_dependencies`, `component_preflight`,
`preflight_used`, `root_dependencies`, `sole_component`,
`sole_component_dependencies` and `sole_component_preflight` are `when: false`
computed variables. `cli/app.py.jinja`, `__main__.py.jinja` and both test
modules read them, so the four files cannot drift on whether a guard is emitted,
what a component's dependencies and preflight modules are, or how it labels
itself in an error message. `component_dependencies` matters most: the launcher
guard and the sole-component guard are rendered into *different files* and only
one of them ever exists in a given project, so nothing but a shared source would
catch them disagreeing. Earlier revisions kept these as
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
  `import <pkg>.web.app` directly also gets the message. Rejected — see
  "Direct library imports stay unguarded" above.
- **Letting faststream's own `ImportError` through.** Its message is actionable
  but recommends `pip install "faststream[<broker>]"`, which contradicts the
  lockfile-managed install this template ships.
