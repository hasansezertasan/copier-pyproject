# ADR-019: Secondary components as CLI subcommands, not separate console scripts

## Status

Accepted (2026-08). Refines the console-script wiring introduced with the
`primary_component` precedence (see [ADR-014](014-import-linter-for-architecture-contracts.md)
for the layering the subcommands lazy-import into).

## Context

A generated project can enable several runnable components — CLI, GUI, TUI, web,
MCP, worker. The highest-precedence enabled one (CLI > GUI > TUI > web > MCP >
worker) is the **primary** and owns the bare `<pkg>` command. Previously every
**other** enabled component was exposed as its own top-level console script:
`<pkg>-tui`, `<pkg>-web`, `<pkg>-mcp`, `<pkg>-worker`, and a windowless
`<pkg>-gui` gui-script.

That had three problems:

- **`PATH` pollution.** A multi-component project installed four or five sibling
  executables (`<pkg>`, `<pkg>-tui`, `<pkg>-mcp`, …).
- **Discoverability.** A separate script is invisible unless you already know its
  exact name; `<pkg> --help` did not enumerate the components.
- **Redundancy.** `cli/app.py` *already* exposed `interactive`/`gui`/`web`
  subcommands (lazy-importing each component per the ADR-014 layering), so a
  CLI-primary project shipped both `<pkg> interactive` **and** `<pkg>-tui` for the
  same thing, while `mcp`/`worker` had no subcommand at all.

See issue #203.

## Decision

Collapse non-primary components into **subcommands of the single `<pkg>` Typer
root**. Every enabled component `X` where `primary_component != "X"` is a
lazily-imported subcommand — `<pkg> interactive` (TUI), `<pkg> gui`, `<pkg> web`,
`<pkg> mcp`, `<pkg> worker` — and **no** `<pkg>-<name>` console script is
emitted. The primary keeps the bare `<pkg>` command (wired to `__main__:main`,
the entry point standalone builds also target). The windowless `<pkg>-gui`
gui-script is dropped; GUI uses `[project.gui-scripts]` only when it is itself
the primary.

### A root exists only where it buys something (`include_console_root`)

The Typer root lives in the `cli/` package. A root is generated whenever — and
only whenever — it is useful, captured by one hidden computed variable in
`copier.yml` (`when: false`):

```
include_console_root = include_cli or (≥2 of gui/tui/web/mcp/worker enabled)
```

- **`include_cli` on** → CLI is always the primary; `cli/` is the full CLI
  (`version`/`info` commands, `no_args_is_help`) plus a subcommand per secondary.
- **`include_cli` off, ≥2 components** → `cli/` is a *minimal launcher*: no
  `version`/`info`; bare `<pkg>` launches the primary via an
  `@app.callback(invoke_without_command=True)` default, secondaries are named
  subcommands.
- **`include_cli` off, exactly one component** → **no root, no `typer`**; bare
  `<pkg>` launches that component directly (`__main__` dispatches to it), exactly
  as before.

`include_console_root` is the single source of truth for the `cli/` package and
test guards, the `typer` core dependency, the import-linter `cli` orchestrator
layer, and the `__main__.py` branch. This keeps `typer` off a single-component
non-CLI app (e.g. a pure web service), and leaves `include_cli`'s meaning — the
`version`/`info` inspection feature — intact. The one accepted cost is that the
package directory is named `cli/` even in a launcher-only project that did not
set `include_cli`.

### Subcommand naming and bodies

Names follow the component modules, except the TUI keeps the friendlier
`interactive` (unchanged from before): `interactive`, `gui`, `web`, `mcp`,
`worker`. Every subcommand body — and the launcher's default callback — is a
lazy `from <pkg>.<name>.app import main; main()`, so the layering contract and
import-time boundaries hold and `typer`/component imports stay deferred. These
launch bodies carry `# pragma: no cover` (they block on a server loop / mainloop
/ stdio); a `--help` smoke test and, under `include_cli`, the `version`/`info`
tests keep the module covered under the `fail_under = 99` gate.

## Consequences

- One `<pkg>` on `PATH`; `<pkg> --help` enumerates every component.
- Alternatives considered: a **universal** root for *every* app (rejected — it
  forces `typer` onto single-component non-CLI apps and dilutes `include_cli`);
  and keeping `<pkg>-<name>` scripts when no CLI is present (rejected — it leaves
  the `PATH`/discoverability problem unsolved for non-CLI multi-component apps).
- Downstream projects adopting this via `copier update` gain the subcommands and
  lose the `<pkg>-<name>` scripts; any wrapper/alias that invoked a suffixed
  script must switch to the subcommand form.
