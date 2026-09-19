# ADR-020: CLI framework as a choice (`cli_framework`)

## Status

Proposed (2026-08). Resolves
[#205](https://github.com/hasansezertasan/copier-pyproject/issues/205). Builds on
[ADR-019](019-components-as-cli-subcommands.md) (the `{{project}}` command is a
single console root that hosts component subcommands) and relates to
[ADR-007](007-standalone-executable-toggles.md) (the runnable-component model and
`is_app`) and [ADR-017](017-opt-in-homebrew-scoop-distribution.md)
(Homebrew/Scoop distribution, gated on `is_app`).

## Context

`include_cli` was hardwired to Typer: enabling it rendered a `typer.Typer` root,
added `typer` to `dependencies`, and generated Typer-based tests. There was no
way to expose a command on `PATH` without taking the Typer dependency.

That coupling has a concrete downstream cost. `is_app` — the flag marking a
project as a standalone tool, and the gate on the Homebrew/Scoop toggles
(ADR-017) — is the OR of the six interface-framework toggles. A project that is a
genuine command-line tool but wants neither Typer nor any other framework (e.g. a
library that also ships a single bare command backed by a plain function) had no
supported path to `is_app`, and therefore none to Homebrew/Scoop packaging.
Forcing the toggles via `--data` did not persist, because `is_app` is a
`when: false` computed helper.

The template already models "pick the framework, don't bake one in" one component
over: `include_web` has a `web_framework` sub-question. `include_cli` had no
equivalent.

## Decision

### Add a `cli_framework` sub-question, mirroring `web_framework`

A `str` question with choices `typer` (default) and `argparse`, asked only
`when: include_cli`. The default preserves every existing render; it is a stored
answer, so a chosen value survives `copier update`.

### `argparse` renders a dependency-free, contract-equivalent console root

The `argparse` variant is standard-library only — no `typer` in `dependencies`,
the keyword list, or the mypy hook's `additional_dependencies`. It exposes the
**same** `version` / `info` commands and, per ADR-019, hangs every enabled
non-primary component off the root as a lazily-imported subcommand
(`interactive`/`gui`/`web`/`mcp`/`worker`). Two behaviours are held equal to the
Typer root on purpose:

- **No-argument invocation prints help** (parity with `no_args_is_help=True`).
- **Missing package metadata exits non-zero** — the Typer root raises
  `typer.Exit(code=1)`; the argparse root raises `SystemExit(1)` after logging
  and writing the same message to stderr.

Because `cli_framework` is only asked `when: include_cli`, the choice only ever
switches the root when a CLI is present. A no-CLI launcher — `include_console_root`
true via ≥2 components, or via `include_web` alone
([ADR-032](032-uniform-run-dev-launch-verbs.md)) — keeps the Typer root.

**The Typer dependency is gated on `root_uses_typer`, not on
`cli_framework == "typer"`.** An earlier revision of this ADR claimed the latter
was "correct in every case, because the default makes the guard true whenever
`include_cli` is false". That is wrong, and the counter-example is a supported
update path: Copier *retains* hidden and unasked answers, so a project that once
set `include_cli: true` + `cli_framework: argparse` and then turns the CLI off
while keeping ≥2 components (or the web app) carries the stored `argparse`
answer forward. `cli_framework == "typer"` is then false while the rendered root
*is* the Typer one — a project whose launcher imports `typer` without declaring
it: broken at launch even in a fully synced environment, with the ADR-028 guard
recommending a `uv sync` that cannot help.

`root_uses_typer` (`copier.yml`, `when: false`) is therefore the single source
for all three consumers that must agree — the `cli/app.py` branch, the `typer`
entry in `[project] dependencies`, and the `typer` entry in the isolated
mirrors-mypy prek hook's `additional_dependencies`. The last one is easy to miss
because `tox -e style` runs mypy against the project's real venv, where `typer`
is installed as a runtime dependency; only the isolated hook environment sees the
gap, and only on the adopter's first `prek run --all-files`.

### The `is_app` gate is kept as-is

`is_app` still means "a runnable component is enabled," and Homebrew/Scoop remain
gated on it (ADR-017 unchanged). The fix is not to widen the gate but to make a
framework-free CLI a first-class way to *be* an app: a library that wants a bare
command sets `include_cli: true` + `cli_framework: argparse`, flipping `is_app`
on through the existing stored toggle — no new library-only concept, no `--data`
workaround.

## Consequences

- A library-shaped project can ship a console command and reach Homebrew/Scoop
  packaging without adopting Typer or any interface framework.
- The console-root component now has two rendered variants to maintain (app +
  test module), covered by `tests/test_cli_framework.py` and the render harness.
- `dependencies` may be empty for an `argparse`-only CLI library; that is valid
  (the console entry point needs no runtime dependency).

### Known limitations

- `argparse` reproduces the `version`/`info` command shape and the component
  subcommands for parity; a project wanting a single no-subcommand action still
  deletes what it does not need.
- `click` was considered as a third choice and skipped: it adds a dependency
  without Typer's ergonomics, so it earns its keep only if later demand appears.
