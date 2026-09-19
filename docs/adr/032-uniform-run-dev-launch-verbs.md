# ADR-032: `run` / `dev` launch verbs for the web component

## Status

Accepted (2026-09). Extends the console-script wiring in
[ADR-019](019-components-as-cli-subcommands.md) and reuses the dependency guard
from [ADR-028](028-actionable-component-dependency-guard.md).

## Context

ADR-019 gives the highest-precedence enabled component the bare `<pkg>` command
and every other component a `<pkg> <name>` subcommand. That is a clean, uniform
*selection* scheme, but it bakes two things into the entry point that a
server-like component's user routinely wants to vary at launch: **which app
object** to run, and **prod vs. reload**. Running the generated web app with
autoreload, or pointing it at a different ASGI app, meant dropping to the
framework's own CLI — `fastapi dev <pkg>.web.app:app`,
`litestar --app=<pkg>.web.app:app run -r` — a different verb per framework,
neither of which the project's own `--help` mentions.

See issue #177.

## Decision

Add two commands to the console root:

- `<pkg> run [module:attribute]` — start the web application on the configured
  bind.
- `<pkg> dev [module:attribute]` — the same, with autoreload, bound to
  loopback.

They share one private `_run_web(app_path, *, dev_mode)` that differs only in
that flag, and both route through the ADR-028 dependency guard exactly as the
component subcommands do.

### Only the web component gets them

The issue proposed `run`/`dev` for both server-like components. Only web
ships them.

- **web** — `uvicorn` is already a runtime dependency (via `fastapi[all]` /
  `litestar[standard]`) and takes an import string plus `reload=` natively. The
  verbs cost nothing but the code that calls it.
- **worker** — FastStream's reload lives in its *CLI* extra (`faststream[cli]`
  → typer + watchfiles), which this template deliberately keeps in the `docs`
  group, not in `dependencies`. Promoting it to a runtime dependency of every
  worker project to power one ergonomic verb is a bad trade;
  `faststream run <pkg>.worker.app:app --reload` stays the documented dev path,
  and `<pkg> worker` stays the production one.
- **gui / tui / mcp** — no meaningful prod/dev distinction, and nothing to point
  a target at.

Because only one component owns the verbs, `run` is never ambiguous, and no
`run --component` selector is needed.

### A web project always has a console root

`include_console_root` now includes `include_web`. Previously a web-only
project — the `web` preset, and precisely the shape that wants `<pkg> dev` most
— had no console root at all: `__main__` bound `web.app:main` directly and
there was nowhere to hang a subcommand.

The alternative, standalone `<pkg>-run` / `<pkg>-dev` console scripts, is the
second entry scheme ADR-019 exists to prevent. Hosting them on the minimal
launcher keeps one scheme: bare `<pkg>` still launches the primary component
through the launcher's default callback, so the ADR-019 precedence and every
documented invocation are unchanged. The cost is that a web-only project now
pulls in `typer` (plus `shellingham`) for the launcher; `fastapi[all]` already
ships typer, so this is only new for Litestar projects, and it is a small pure-
Python dependency against a launch surface every such project uses.

A consequence worth naming: `sole_component` can no longer be `web`, so the
standalone-executable entrypoint of a web project is the console root rather
than the component. That is the same shape every multi-component project
already had.

### `<pkg> web` stays, as an alias

Where web is *not* the primary component, ADR-019's `<pkg> web` subcommand
remains — removing it would break the one naming rule ADR-019 makes. It is now
literally `_run_web(None, dev_mode=False)`, so there is no second code path:
`<pkg> web` is `<pkg> run` with no target.

### Target discovery stays minimal

`resolve_app_path` accepts a `module:attribute` string, validates that shape,
and otherwise defaults to `DEFAULT_APP_PATH` — this project's own
`<pkg>.web.app:app`. There is no search for candidate modules, no default-attr
guessing, no framework sniffing. An unrecognized target fails with
`SystemExit` naming the bad value and the expected shape, the same way
`resolve_bind` already handles a bad `{PROJECT}_PORT`, rather than surfacing
uvicorn's own wording.

The target is handed to uvicorn as the **import string**, not as the imported
object. Autoreload re-imports the app in a child process, so the string form is
the only one that can reload; using it for both modes keeps one code path.

### Dev mode forces a loopback bind

`dev` binds `127.0.0.1` whatever `{PROJECT}_HOST` says, matching `fastapi dev`.
A reloading server executes unreviewed code on every save; that belongs on the
developer's own machine. `run` honours the environment as before.

## Consequences

- A uniform verb pair that the project's own `--help` advertises, identical
  across FastAPI and Litestar projects.
- One new runtime dependency (`typer`) for web-only Litestar projects, and a
  `cli/` package plus a `test-cli`/`coverage-cli` CI job pair in the `web`
  preset's rendered tree.
- `run`/`dev`/`_run_web` are unit-tested (the launch itself is stubbed), so none
  of them carries a coverage pragma; only `run_server`, which blocks on
  uvicorn, does.
- Worker projects keep exactly the launch surface they had.

## Alternatives considered

- **`run`/`dev` for the worker too**, dispatching on the resolved object's type.
  Rejected: it needs `faststream[cli]` at runtime for reload, and type-sniffing
  the target to pick between `uvicorn.run` and FastStream's runner is the kind
  of framework detection this ADR deliberately avoids.
- **Standalone `<pkg>-run` / `<pkg>-dev` console scripts** when no CLI is
  enabled, as issue #177 suggested. Rejected — see above.
- **Replacing `<pkg> web` with `<pkg> run`.** Rejected: ADR-019's naming rule is
  worth more than removing a one-line alias.
- **Letting uvicorn parse the target.** Rejected: the failure arrives from
  uvicorn's own argument handling with no reference to this project's command,
  and a cheap shape check is testable where uvicorn's is not.
