# Runnable components and the console root

## Secondary components are subcommands of one console root, not separate scripts

**Id:** 3d60ab14-8ff9-47db-b326-d7e82947a6cf
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-019 ([`docs/adr/019-components-as-cli-subcommands.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/019-components-as-cli-subcommands.md)), including its 2026-09 amendment; issue #203
**Revisit when:** a new kind of runnable component is added, or `typer` becomes unacceptable on the minimal launcher
**See:** architecture-contracts.md#one-exhaustive-import-linter-layers-contract-cli-above-independent-components-above-core-above-utils — 3b7cdbee-7c66-4e52-9d7e-8ab0ffe32e56 — as of 2026-10-11
**See:** components.md#the-web-component-gets-run-and-dev-launch-verbs-and-therefore-always-a-console-root — 3daefc4a-ee36-44cb-b137-bc9224f2a262 — as of 2026-10-11

The highest-precedence enabled component (CLI > GUI > TUI > web > MCP > worker,
spelled once as `primary_component` in `copier.yml`) owns the bare `<pkg>`
command. Every other enabled component is a lazily imported subcommand
(`interactive`, `gui`, `web`, `mcp`, `worker`); no `<pkg>-<name>` console
script is emitted. A root exists only where it buys something, captured by the
hidden `include_console_root`: with `include_cli`, with web, or with two or more
components. With no root, bare `<pkg>` dispatches to the sole component from
`__main__`. GUI uses `[project.gui-scripts]` only as the sole runnable
component; a GUI primary sharing a root gets a normal console script.

**Reason:** a multi-component project installed four or five sibling
executables, a separate script is invisible until you know its name, and the
CLI already exposed `interactive`/`gui`/`web` subcommands beside their suffixed
scripts while MCP and worker had none. A windowless launcher as the shared root
would swallow console I/O and `--help` of the subcommands on Windows. One
computed variable is the single source for the `cli/` package, the `typer`
dependency, the import-linter orchestrator layer and the `__main__` branch, so
`typer` stays off a single-component non-CLI app.

**Rejected alternative:** a universal root for every app — forces `typer` onto
single-component non-CLI apps and dilutes what `include_cli` means.

**Rejected alternative:** keep suffixed scripts when no CLI is present — leaves
the PATH and discoverability problem for non-CLI multi-component apps.

**Consequence:** the package directory is named `cli/` even in a launcher-only
project; adopters updating lose the suffixed scripts and switch wrappers to the
subcommand form.

## `cli_framework` offers argparse beside Typer; the Typer dependency is gated on `root_uses_typer`

**Id:** de9f8183-4328-4678-8611-5e715cffd70d
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-020 ([`docs/adr/020-cli-framework-choice.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/020-cli-framework-choice.md)); [issue #205](https://github.com/hasansezertasan/copier-pyproject/issues/205)
**Revisit when:** demand appears for click as a third choice, or a no-CLI launcher needs to be framework-free
**See:** components.md#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts — 3d60ab14-8ff9-47db-b326-d7e82947a6cf — as of 2026-10-11
**See:** package-distribution.md#homebrew-and-scoop-are-opt-in-dispatches-the-tap-or-bucket-owns-the-manifest-logic — 462ac46c-c9db-4a4a-b8ae-bbe5c14af09f — as of 2026-10-11

A `cli_framework` sub-question (`typer` default, `argparse`), asked only with
`include_cli`, mirrors `web_framework`. The argparse root is standard-library
only and contract-equivalent: same `version`/`info` commands, same lazily
imported component subcommands, help on no arguments, non-zero exit on missing
metadata. A no-CLI launcher keeps the Typer root. The `typer` entry in
`dependencies` and the `cli/app.py` branch both read one hidden
`root_uses_typer` variable.

**Reason:** `include_cli` was hardwired to Typer, so a genuine command-line
tool that wanted no framework had no supported path to `is_app` and therefore
none to Homebrew/Scoop packaging; forcing toggles via `--data` did not persist.
The dependency is gated on `root_uses_typer` rather than on the framework
answer because Copier retains unasked answers: a project that set
`argparse`, then turned the CLI off while keeping two components, carries the
stored answer forward while rendering the Typer root — a launcher importing
`typer` without declaring it, broken even in a synced environment. An earlier
revision of the record claimed the simpler guard was correct in every case; it
was not.

**Rejected alternative:** widen the `is_app` gate for libraries — a framework-free
CLI is made a first-class way to *be* an app instead.

**Rejected alternative:** click as a third choice — a dependency without Typer's
ergonomics; earns its keep only on later demand.

## Launcher imports are guarded with exact-match, preflighted dependency errors

**Id:** 70e54068-d43c-40a2-9097-95e7cc14c668
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-028 ([`docs/adr/028-actionable-component-dependency-guard.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/028-actionable-component-dependency-guard.md)); issues #172 and #268
**Revisit when:** generated projects gain per-component extras, or a dependency stops importing lazily after the guarded block
**See:** components.md#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts — 3d60ab14-8ff9-47db-b326-d7e82947a6cf — as of 2026-10-11
**See:** components.md#component-dependencies-are-core-dependencies-there-is-no-empty-all-extra — e9b25624-f621-4071-bd99-a7cde620189a — as of 2026-10-11

Each launcher's lazy import is wrapped in a context manager that turns a
`ModuleNotFoundError` whose name is *exactly* one of the component's declared
dependency modules into an exit-1 message naming the component, the module and
the fix (`uv sync`). Dependencies that import late (uvicorn, Tkinter, textual)
or re-export behind their own guard with no module name (faststream brokers,
mcp's transitive imports) are imported eagerly inside the block by a preflight
that re-raises with the caller-supplied name. Tkinter gets a system-package
hint (including a version-qualified Homebrew formula) because it is not a
distribution. The root's own module-scope imports (`typer`, pydantic via the
settings stack) and the sole-component entrypoint in `__main__.py` get the same
treatment; all derived facts are `when: false` computed variables in
`copier.yml`.

**Reason:** there are no extras to name — component deps are core dependencies —
so a missing module means the environment is out of sync with the metadata and
`uv sync` is the honest remedy. The first-party import always succeeds after a
`copier update`; the third-party failure happens one frame deeper, so the guard
must classify what comes out of the import rather than replace it. Exact
matching protects application defects (a typo'd import below an installed
dependency) from being mislabelled as a stale environment. The sole-component
entrypoint is what frozen binaries target, whose user has no CLI to fall back
on. Shared computed variables matter most for the two guards rendered into
different files, only one of which exists in any project.

**Rejected alternative:** a shared `require(module, feature, extra)` helper as
the issue proposed — no extra exists, and replacing the first-party import would
not catch the deeper failure.

**Rejected alternative:** guard every component's module scope so direct library
imports also get the message — the reader is already in a traceback in their
own code, the guard would run on every successful import forever, and component
modules are what adopters edit most.

**Rejected alternative:** let faststream's own `ImportError` through — its advice
(`pip install "faststream[<broker>]"`) bypasses the lockfile.

## Component dependencies are core dependencies; there is no empty `all` extra

**Id:** e9b25624-f621-4071-bd99-a7cde620189a
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** ADR-028 ([`docs/adr/028-no-empty-all-extra.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/028-no-empty-all-extra.md))
**Revisit when:** a component gains a genuinely optional dependency

Generated projects declare no `[project.optional-dependencies]` table. A
runnable component's runtime dependency goes into the core `dependencies` list
under its toggle guard. The permanently empty `all = []`, the `<pkg>[all]` dev
self-reference, six `extras = ["all"]` tox settings and four `--extra all`
workflow flags were removed.

**Reason:** a component is chosen at generation time and `__main__` imports it
unconditionally, so a plain install must pull its dependency or the console
script fails at launch. The leftover shell installed nothing yet three
documents cited it as load-bearing — a reader auditing the packaging would have
concluded the wrong thing about what guarantees what.

**Rejected alternative:** keep `all = []` as a pre-wired seam for a future
optional dependency — a one-time edit if ever needed is cheaper than a
permanent misleading declaration.

**Consequence:** adopters applying this update must re-lock, because the
metadata recorded in `uv.lock` changes and every `uv run --locked` hard-fails
until they do; a hand-added `uv run --extra all` breaks.

## The web component gets `run` and `dev` launch verbs, and therefore always a console root

**Id:** 3daefc4a-ee36-44cb-b137-bc9224f2a262
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-032 ([`docs/adr/032-uniform-run-dev-launch-verbs.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/032-uniform-run-dev-launch-verbs.md)); issue #177
**Revisit when:** FastStream's reload stops requiring its CLI extra, or a second component acquires a prod/dev distinction
**See:** components.md#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts — 3d60ab14-8ff9-47db-b326-d7e82947a6cf — as of 2026-10-11
**See:** components.md#launcher-imports-are-guarded-with-exact-match-preflighted-dependency-errors — 70e54068-d43c-40a2-9097-95e7cc14c668 — as of 2026-10-11

`<pkg> run [module:attribute]` starts the web app on the configured bind;
`<pkg> dev` adds autoreload and forces a loopback bind. Both share one private
runner and the dependency guard; `<pkg> web` stays as an alias where web is not
primary. The target is passed to uvicorn as an import string, validated for
shape only — no module search, no framework sniffing. `include_console_root`
now includes `include_web`, so a web-only project reaches its component through
the minimal launcher.

**Reason:** varying the app object or reload meant dropping to a different
framework CLI per framework that the project's own help never mentioned.
uvicorn is already a web runtime dependency and takes an import string with
reload natively; the string form is the only one that can reload in a child
process, so one code path serves both modes. A reloading server executes
unreviewed code on every save and belongs on loopback. A web-only project had
no root to hang a verb on, and standalone `<pkg>-run`/`<pkg>-dev` scripts are
the second entry scheme the subcommand decision exists to prevent.

**Rejected alternative:** verbs for the worker too — reload needs
`faststream[cli]` at runtime, which the template deliberately keeps out of
`dependencies`, and type-sniffing the target is the framework detection avoided
here.

**Rejected alternative:** replace `<pkg> web` with `<pkg> run` — breaks the one
naming rule the subcommand decision makes.

**Rejected alternative:** let uvicorn parse the target — its error names no
project command and is not testable the way a cheap shape check is.

**Consequence:** web-only Litestar projects gain `typer` (FastAPI already ships
it); `sole_component` can never be `web`, so a web project's executable
entrypoint is the console root.

## One application payload in `core/app.py`; components are adapters over it

**Id:** 8bb1e55e-f468-44fc-80a5-d3b3719e5ddc
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-033 ([`docs/adr/033-shared-app-service-components-as-adapters.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/033-shared-app-service-components-as-adapters.md)); issues #178 and #321
**Revisit when:** a component needs a fourth failure behaviour, or a second provider of the payload appears
**See:** architecture-contracts.md#one-exhaustive-import-linter-layers-contract-cli-above-independent-components-above-core-above-utils — 3b7cdbee-7c66-4e52-9d7e-8ab0ffe32e56 — as of 2026-10-11
**See:** template-updates.md#retired-template-modules-become-adopter-owned — 4dd6729a-697e-4588-a7a7-d37152018b6b — as of 2026-10-11

`core/app.py` exposes three functions — `version()` and `info()`, which raise
`MetadataUnavailableError`, and `info_or_unknown()`, which degrades, logs and
never raises — plus the error type and an unknown-version constant. Each
component imports the module as `service` and adapts: the CLI exits 1, the web
app answers 503, the MCP tool returns error text, GUI and TUI show "unknown",
the worker falls back to `0.0.0`. The module renders only when a runnable
component is enabled. One `missing_metadata` fixture patching
`core.app.Distribution` replaces six per-module stubs.

**Reason:** a `full` project carried eight copies of the distribution lookup
and six of the platform payload, with nothing enforcing agreement — GUI and TUI
nearly drifted on field names and fatality. The import contract forbids
components importing each other, so sharing had to live below them, and `core`
is already that layer. Functions rather than a class because it would hold no
state and ruff's no-self-use rule flags exactly that shape; no Protocol because
it would have one implementation and no type-checking caller. Three functions
because there are three real behaviours, each with more than one caller.
Logging stays in the adapters because it genuinely differs; the worker's wire
model keeps its own platform fields because routing them through a dict adds
indirection for no sharing.

**Rejected alternative:** a new `base/` package with an `AppService` class and
a `VersionProvider` protocol, as proposed — each adds a name without adding a
constraint.

**Rejected alternative:** a transport/presentation split per component — more
files than the three f-strings they would hold.

**Rejected alternative:** keep the copies and add a conformance test — tells you
they drifted after the sixth copy is written; removing them means they cannot.
