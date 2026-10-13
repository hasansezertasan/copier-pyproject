# Testing strategy of generated projects

## The worker exposes an env-injectable broker factory; lazy broker imports were rejected

**Id:** b00a3a49-7fbf-4d87-98fa-73519b994c8e
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-008 §1 and its implementation revision note ([`docs/adr/008-worker-broker-testing-strategy.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/008-worker-broker-testing-strategy.md)); the pattern was proven in litestar-faststream and [litestar-events#9](https://github.com/hasansezertasan/litestar-events/pull/9)
**Revisit when:** a worker gains a second broker, or FastStream changes how a broker is constructed
**See:** components.md#component-dependencies-are-core-dependencies-there-is-no-empty-all-extra — e9b25624-f621-4071-bd99-a7cde620189a — as of 2026-10-11

`worker/app.py` provides `build_broker(url=None)`, which resolves the
connection at call time (argument, broker-specific env var, local default) and
registers the subscriber and publisher on the broker it returns; a module-level
`broker = build_broker()` still serves the entry point. The handler and
publisher are factory-local closures, so the unit test asserts on a response
delivered to a collector subscriber rather than importing internals.

**Reason:** the original draft proposed lazy broker imports. Implementation
showed that buys nothing here: there is one broker, its driver is a core runtime
dependency and so always present, and the broker was constructed at module top,
so the driver loads at import regardless of where the statement sits. The real
blocker to integration testing was *construction at import time* — a
localhost-bound singleton tests cannot retarget. The factory is the seam a real
round-trip test needs: a fresh broker pointed at a throwaway instance, no
import-order games.

**Rejected alternative:** lazy broker imports — the reasoning above.

**Consequence:** the factory returns only the broker; subscriber and publisher
become closures rather than importable module globals, so tests assert on
observable behaviour (a response reaching a collector subscriber), not wiring.

## Real-broker integration tests: testcontainers locally, per-broker CI mechanism

**Id:** 73e209d9-60ad-4492-9807-28192b480480
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-008 §2 and its 2026-08 amendment ([`docs/adr/008-worker-broker-testing-strategy.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/008-worker-broker-testing-strategy.md)); issues #169 and #166
**Revisit when:** GitHub service containers can override the image command, Kafka/RabbitMQ gain a usable readiness probe, or Docker becomes available on non-Linux runners
**See:** testing-strategy.md#the-worker-exposes-an-env-injectable-broker-factory-lazy-broker-imports-were-rejected — b00a3a49-7fbf-4d87-98fa-73519b994c8e — as of 2026-10-11
**See:** ci-topology.md#per-component-markers-path-filtered-jobs-and-one-coverage-gate-per-component — 467b6cc3-775b-4e4c-9a8e-b0d1c3d733ac — as of 2026-10-11

An `integration`-marked test round-trips a message through the real driver. It
is deselected from the default suite and run by an on-demand tox env and a
conditional, Ubuntu-only `worker-integration` CI job keyed to the one chosen
broker. Container startup lives in a plain context manager: when the broker's
URL env var is already set it connects directly; otherwise it starts a
testcontainer. In CI, redis and nats use runner-provided `services:`
containers (the split lives once, as the `ci_service` field on
`worker_broker_spec` in `copier.yml`, with `health_cmd: null` marking "no
usable in-container probe"); kafka and rabbitmq keep testcontainers. The env
runs with a broad deprecation-warning demotion and a pytest timeout.

**Reason:** the in-memory test broker stubs out exactly the things that regress
— serialization, connection handling, driver compatibility — and CI never
started a broker. Docker is reliably available only on Ubuntu runners, so the
cross-OS matrix must stay Docker-free. testcontainers owns the lifecycle from
the test, so a laptop run matches CI. The original reasoning over-generalized
against `services:`: for fast-starting brokers the runner starts, health-gates
and injects the connection before the job, which is lighter than in-test
orchestration; Kafka's advertised listeners and RabbitMQ's readiness are not
worth that path. NATS runs without a health check because its monitoring
endpoint needs a container command that service containers cannot set, and
the test's own connect-retry covers readiness. A context manager rather than a
fixture because a fixture consumed only by a deselected test reads as unused to
the dead-fixtures check in `style`. Module-scoping the warning demotion was
tried and rejected: CLI `-W` module matching is exact, and drivers attribute
warnings via `stacklevel` to arbitrary caller frames.

**Rejected alternative:** `services:` for every broker — static YAML without
per-test lifecycle, and Kafka/RabbitMQ readiness is not worth it.

**Rejected alternative:** a fan-out over all four brokers — a generated project
has exactly one.

**Consequence:** the integration test file is in coverage `omit`, since it is
collected but deselected in the default suite. The larger runtime integration of
FastStream inside the Litestar app is explicitly out of scope.

**Shared image variables.** The Redis-compatible image and CLI come from the
`redis_image` / `redis_cli` computed vars, which the devcontainer compose
service reads as well as the CI `services:` container, so a redis-to-valkey or
version bump cannot leave CI and the devcontainer disagreeing.

## Coverage exclusions are per-site pragmas, and the globs must match the installed layout

**Id:** 68366ce3-cc8e-4720-aa91-5eb83aaf2e2d
**Type:** decision
**Type:** incident
**Status:** active
**Evidence:** confirmed
**Source:** ADR-008, Consequences — systemic coverage fix ([`docs/adr/008-worker-broker-testing-strategy.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/008-worker-broker-testing-strategy.md))
**Revisit when:** tox stops installing the built wheel/sdist, or coverage changes how `paths` remapping works
**See:** testing-strategy.md#interactive-components-expose-injected-driver-seams-so-headless-ci-measures-everything-but-the-blocking-call — ffcf90f2-34c7-4673-bbe2-5619c6b23128 — as of 2026-10-11

Reachable error handling (web 503s, CLI exit codes, GUI/TUI "unknown"
degradation, MCP error text) is unit-tested. Only irreducible blocking calls,
the `__main__` dispatchers, the c-extension `except ImportError` fallback and
the worker's module-level metadata fallback carry a per-site
`# pragma: no cover`. The
`omit` globs are `*/`-anchored (`*/_version.py`, `*/worker/test_integration.py`,
the latter directory-anchored), and `[tool.coverage.paths]` maps
`*/site-packages/<pkg>` back onto `src/<pkg>`.

**Reason:** testing the worker exposed that *no* optional-component project
reached the 99% gate out of the box, because entrypoints and fallbacks were
unexercised and the example input disabled every component. An earlier
iteration excluded them with blanket `exclude_lines` regexes (`def main(`,
`except PackageNotFoundError`); a regex matching a `def` line excludes the
whole function body, which silently un-measured the *tested* GUI/TUI
entrypoints and web handlers — the gate became blind to what it protects. Two
further defects were universal: a `src/**`-anchored omit missed the installed
copy and reported `_version.py` at 0%, and a paths mapping that never matched
tox's per-env `site-packages` kept a separate copy per interpreter so a
version-gated line covered in one counted as missed. Both are invisible under
editable `pytest` and appear only under a real multi-env `tox run`.

**Rejected alternative:** blanket `exclude_lines` regexes — the blindness above.

**Consequence:** coverage is verified only via the installed-package `tox run`
path; after the fix every component and the base project report 100%.

## Interactive components expose injected driver seams so headless CI measures everything but the blocking call

**Id:** ffcf90f2-34c7-4673-bbe2-5619c6b23128
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-035 ([`docs/adr/035-headless-testing-for-interactive-components.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/035-headless-testing-for-interactive-components.md)); issue #176
**Revisit when:** a component's blocking call becomes swappable at the module level, or a new interactive component is added
**See:** testing-strategy.md#coverage-exclusions-are-per-site-pragmas-and-the-globs-must-match-the-installed-layout — 68366ce3-cc8e-4720-aa91-5eb83aaf2e2d — as of 2026-10-11
**See:** components.md#one-application-payload-in-coreapppy-components-are-adapters-over-it — 8bb1e55e-f468-44fc-80a5-d3b3719e5ddc — as of 2026-10-11

Each component isolates its blocking call (Textual `App.run`, the Tk dialog,
`uvicorn.run`, the MCP stdio transport and loop, the FastStream loop) in a
private helper, and the public orchestration function takes a keyword-only
driver or runner defaulting to it. Tests drive the TUI with Textual's headless
pilot, the GUI with a tracking driver and a stubbed `tkinter` module (so its
default driver carries no pragma at all), the web runner with a stub asserting
the dev-mode loopback override, the MCP transport and runner, and the worker's
lifecycle hooks by their log records. CLI subcommand bodies are tested by
monkeypatching the target component's `main`, importing the submodule
explicitly because package `__init__` re-exports shadow it. The web seam is a
`Protocol` because `reload` is keyword-only and ruff's boolean-trap rules are
on.

**Reason:** the entrypoints previously carried broad `# pragma: no cover` over
setup, widget composition, bind resolution, error handling and dispatch glue,
so a regression there slipped through and the line between irreducible and
testable was blurred. A seam is one default argument and one call — no
registry, no runtime cost — and does not cross component boundaries.

**Rejected alternative:** monkeypatching the private default helper — Python
binds a default argument at definition time, so patching the module attribute
silently no-ops; the driver must be passed. Monkeypatching stays correct for
the CLI dispatchers, which look their target up at call time.

**Consequence:** two deliberate behaviour changes: the TUI imports `textual` at
module scope, so a missing Textual raises on import instead of degrading to
stdout (a hard dependency being absent is a broken install), and the GUI
catches `Exception` around an injected driver while keeping its specific
"Tkinter not available" arm first.

**Test-side details.** The TUI `q` binding is asserted inside the pilot
context, because `run_test().__aexit__` stops the app unconditionally and
asserting after exit proves nothing. The worker's `_run_app` keeps its uvloop
probe inside the pragma'd helper, since choosing a loop only means anything next
to the `run` call it chooses it for.

## Async testing is an explicit template axis (`async_style`)

**Id:** e3dc1ec0-0579-4fc9-ac79-413d64550b9a
**Type:** decision
**Status:** active
**Evidence:** inferred
**Source:** ADR-036 ([`docs/adr/036-async-testing-style.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/036-async-testing-style.md))
**Revisit when:** an async-capable component gains trio support, or pytest ships a built-in async runner

`async_style` offers `none`, `asyncio` and `anyio`; it defaults to `none` for a
synchronous project and to `asyncio` when an async-capable component is
selected. `asyncio` adds pytest-asyncio in strict mode (every async test
explicitly marked); `anyio` adds `anyio[trio]` with a fixture parametrized over
both backends. A project rendering TUI, MCP or worker tests cannot pick `none`.
Tests for asyncio-native integrations (FastStream workers, Textual's pilot)
select asyncio explicitly.

**Reason:** a synchronous library should not gain an async runner merely because
it came from this template, while async projects need one that works
immediately; AnyIO may expose backend assumptions an asyncio-only suite would
not, so component tests that require asyncio constrain that locally.

**Alternatives:** unknown — ADR-036 records the decision and its reasons, no
alternative that was in contention.
