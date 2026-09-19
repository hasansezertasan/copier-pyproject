# ADR-032: Headless testing and injected driver seams for interactive components

## Status

Accepted (2026-09). Resolves issue #176. Builds on
[ADR-008](008-worker-broker-testing-strategy.md) (worker testing strategy),
[ADR-014](014-import-linter-for-architecture-contracts.md) (layering contracts),
and [ADR-019](019-components-as-cli-subcommands.md) (secondary components as CLI
subcommands).

## Context

A generated project can enable multiple interactive components:

- **TUI**: Textual-based terminal UI (`tui/app.py`)
- **GUI**: Tkinter-based dialog interface (`gui/app.py`)
- **Web**: FastAPI or Litestar ASGI application (`web/app.py`)
- **MCP**: Model Context Protocol stdio server (`mcp/app.py`)
- **Worker**: FastStream message consumer (`worker/app.py`)
- **CLI Subcommands**: Subcommand dispatchers in `cli/app.py` that invoke the above

Previously, running these components in standard headless CI (such as GitHub
Actions Linux runners without display servers, interactive TTYs, or persistent
stdio streams) was impossible because their entry points invoked blocking event
loops: `App.run()`, `tkinter.messagebox.showinfo()`, `uvicorn.run()`,
`mcp.server.stdio.stdio_server()`, and FastStream server runners.

To satisfy the `fail_under = 99` coverage requirement, these components relied
on `# pragma: no cover` placed broadly over their `main()` entrypoints,
`_display_*` helpers, worker lifecycle hooks, and CLI subcommand dispatchers.
This had significant drawbacks:

- Business setup, widget tree composition, bind resolution, error handling, and
  dispatcher routing were unmeasured and untested.
- A regression in subcommand argument parsing or dispatch glue could slip
  through without detection.
- The boundary between genuinely irreducible blocking calls and testable
  orchestration code was blurred.

## Decision

Introduce injected adapter/driver seams across all interactive components,
allowing headless CI test suites to drive setup, widget hierarchy, lifecycle,
and error handling deterministically, while shrinking `# pragma: no cover`
strictly to irreducible blocking leaves.

### 1. Injected Adapter/Driver Seams

Each component isolates its blocking execution call into a dedicated private
helper — tagged with `# pragma: no cover` where the call is genuinely
unreachable under headless CI. The public orchestration function accepts a
keyword-only parameter defaulting to that helper:

- **TUI (`tui/app.py`)**:
  - `InfoApp(App[None])` is extracted to module level with distinct widget IDs
    (`#title`, `#info-text`, `#footer`).
  - `_run_app(app: InfoApp) -> None: # pragma: no cover` executes `app.run()`.
  - `_display_tui` and `main` accept `driver: Callable[[InfoApp], None] = _run_app`.
- **GUI (`gui/app.py`)**:
  - `_default_dialog_driver(title: str, message: str) -> None` owns the Tk root
    lifecycle and the `messagebox.showinfo` call. It carries **no** pragma: the
    tests stub `sys.modules["tkinter"]`, so the whole function — including the
    `finally: root.destroy()` teardown — is measured.
  - `_display_message` and `main` accept `dialog_driver: Callable[[str, str], None] = _default_dialog_driver`.
  - `_display_message` keeps a dedicated `except ImportError` arm: Tkinter ships
    separately from CPython on most Linux distributions, so "not installed" is a
    real failure that deserves its own message rather than the generic one.
- **Web (`web/app.py`)**:
  - `_run_server(host: str, port: int) -> None: # pragma: no cover` runs `uvicorn.run`.
  - `main` accepts `runner: Callable[[str, int], None] = _run_server`.
- **MCP (`mcp/app.py`)**:
  - `_stdio_transport() -> None: # pragma: no cover` and `_run_server_loop() -> None: # pragma: no cover`
    manage stdio streams and event loop execution.
  - `run_server` accepts `transport: Callable[[], Awaitable[None]] = _stdio_transport`.
  - `main` accepts `runner: Callable[[], None] = _run_server_loop`.
- **Worker (`worker/app.py`)**:
  - `_run_app(app_: FastStream) -> None: # pragma: no cover` runs the worker loop.
  - `main` accepts `runner: Callable[[FastStream], None] = _run_app`.
  - Lifecycle hooks `@app.after_startup` and `@app.after_shutdown` are exposed
    as `on_startup` and `on_shutdown` and tested without pragmas.

Default parameter values keep every production call site unchanged: `main()`
with no arguments still runs the real driver.

Two behavior changes ride along that the defaults do not cover, both
deliberate:

- The TUI imports `textual` at module scope (needed so `InfoApp` can be defined
  there and driven by the pilot), so a missing or broken Textual now raises
  `ImportError` when `tui.app` is imported, rather than being converted to a
  `TuiDisplayError` and degrading to stdout. Textual is a hard runtime
  dependency of the TUI component, so "not installed" is a broken install, not
  a runtime condition worth degrading around. The CLI still imports `tui.app`
  lazily, so `pkg version` and friends never pay the import.
- The GUI's `_display_message` catches `Exception` around the injected driver
  rather than only `TclError`, since a custom driver may fail in its own way.
  The `except ImportError` arm stays ahead of it to keep the specific
  "Tkinter is not available" message.

### 2. Headless Driving in Tests

Test suites in `tests/<component>/test_app.py` take advantage of these seams:

- **TUI**: Uses Textual's headless testing pilot (`async with app.run_test() as pilot`)
  to verify widget titles, content, and key handling. The `q` binding is asserted
  *inside* the pilot context (`assert app.is_running` → `press("q")` → `pause()` →
  `assert not app.is_running`); asserting after the context has exited proves
  nothing, since `run_test().__aexit__` stops the app unconditionally.
  Tests for `main()` verify driver invocation and fallback exception handling.
- **GUI**: Tests for `main()` inject a tracking driver, verifying correct parameter
  delivery, success return codes, fallback logging on display errors, and interrupt
  propagation. A separate group stubs `sys.modules["tkinter"]` to drive
  `_default_dialog_driver` itself, pinning the happy path
  (`withdraw` → `showinfo` → `destroy`) and that the root is destroyed when
  either step raises.
- **Web**: Tests for `main()` verify bind resolution and runner invocation.
- **MCP**: Tests for `run_server()` and `main()` verify transport and runner execution.
- **Worker**: Tests directly await `on_startup()` and `on_shutdown()` and assert
  on the emitted log records (not bare invocation, which would pass through any
  regression in the hook bodies), and verify `main()` invokes the runner with `app`.

### 3. CLI Subcommand Testing without Submodule Shadowing

In `cli/app.py`, `# pragma: no cover` is removed from all subcommand handlers
(`interactive()`, `gui()`, `web()`, `mcp()`, `worker()`) and the launcher's
default callback.

Tests verify dispatching by monkeypatching the target component's `main()` entrypoint.
Because package `__init__.py` files often re-export attributes (e.g. `app = FastAPI(...)`
or `app = FastStream(...)`) which shadow submodules under attribute lookup, the
test harnesses use `importlib.import_module(f"{pkg}.{subcommand}.app")` before
applying monkeypatches.

## Consequences

- **Coverage Accuracy**: Test coverage for all interactive components reaches 100%
  under headless CI while preserving `fail_under = 99`.
- **Minimal Pragmas**: `# pragma: no cover` is confined to irreducible blocking
  calls (`uvicorn.run`, `stdio_server`, `app.run()`, the FastStream loop) plus
  the import or loop selection each one is inseparable from — the worker's
  `_run_app` keeps its uvloop probe, since choosing a loop only means anything
  next to the `run` call it chooses it for. Where the blocking dependency can
  be swapped at the `sys.modules` level — the GUI's Tkinter driver — no pragma
  is used at all.
- **No Layering Violations**: Injected seams do not introduce cross-component
  imports; the import-linter contracts (ADR-014) remain fully satisfied.
- **Zero Runtime Overhead**: A seam is one default argument and one call
  through it — no indirection layer, no registry, no runtime penalty.
- **Inject, do not monkeypatch**: Python binds a default argument at `def`
  time, so the default driver is captured when the module is imported.
  Monkeypatching `_default_dialog_driver`, `_run_app`, `_run_server`, or
  `_run_server_loop` on the module therefore does **not** change what `main()`
  calls — it silently no-ops. Pass the driver as an argument, which is why the
  tests were rewritten away from the `monkeypatch.setattr(mod, "_display_*")`
  pattern they used before. Monkeypatching stays correct for the CLI
  dispatchers, which look their target up at call time via a function-local
  `from <pkg>.<name>.app import main`.
