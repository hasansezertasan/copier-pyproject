# ADR-008: Worker broker testing strategy (lazy imports + testcontainers integration)

## Status

Accepted (2026-06). Implemented.

> **Revision (during implementation).** The original draft proposed *lazy broker
> imports* as item 1. Implementation showed that this buys nothing for this
> worker: it has exactly one broker, `faststream[<broker>]` is a hard dependency
> of the `worker` extra and every test/tox environment installs
> `extras = ["all"]` (so the driver is always present wherever the worker is
> exercised), and the broker is constructed at module top — so the driver is
> imported at module load regardless of where the `import` statement sits, and
> the top-level package never imports `worker.app` anyway. The real blocker to
> integration testing was *construction at import time* (a localhost-bound
> broker singleton that tests can't retarget). Item 1 is therefore an
> **env-injectable broker factory**, which is what actually enables a real
> round-trip integration test. The lazy-import idea is rejected.

## Context

The `include_worker` component generates a [FastStream](https://faststream.ag2.ai/)
worker (`src/<pkg>/worker/app.py`) bound to one broker chosen by `worker_broker`
(kafka / nats / rabbitmq / redis). Two observations about its current testing
story motivated this ADR. Both patterns were proven in
[`litestar-faststream`](https://github.com/hasansezertasan/litestar-faststream)
and the CI/lint sweep in
[`litestar-events#9`](https://github.com/hasansezertasan/litestar-events/pull/9),
and are candidates to fold back into this template.

**1. Broker drivers are imported at module load.** `worker/app.py` does its
broker import at the top of the file (e.g. `from faststream.kafka import
KafkaBroker`), so importing the package — or any submodule that transitively
reaches the worker — pulls in the broker's third-party driver
(`aiokafka`, `nats-py`, `aio-pika`, `redis`). That couples *importability* to a
heavy, often C-backed dependency being installed and loadable on the current
platform.

**2. There is no integration test against a real broker.** The generated worker
tests (`tests/worker/test_app.py`) already use FastStream's in-memory
`Test<Broker>` context manager — a genuinely good unit pattern that needs no
running broker, so that half of the litestar-events PR is already present and is
**retained** (though the assertions were reworked from `.mock` introspection to
observable-behavior checks as a consequence of the factory in item 1 — see
Consequences). What is missing is any test that
exercises the worker against a *real* broker. The CI `ci` job runs `tox run`
across the OS matrix but never starts a broker; the `.devcontainer` compose file
defines broker services, but CI does not use the devcontainer. So a regression in
real serialization, connection handling, or driver compatibility (the exact
things the in-memory broker stubs out) ships undetected.

litestar-events solved (2) with [testcontainers](https://testcontainers.com/):
spin the real broker up in a Docker container per test session, in a CI matrix
job per backend, instead of relying on statically-declared GitHub `services:`
blocks.

## Decision

Adopt both patterns for the generated worker, scoped to `include_worker`.

### 1. Env-injectable broker factory

Replace the module-level `broker = <Broker>(os.getenv(...))` singleton (which
froze the connection at import time and bound the response publisher and
subscriber to it) with a `build_broker(url: str | None = None)` factory that:

- resolves the connection at *call* time (`url` arg → broker-specific env var →
  local default), and
- registers the `version-requests` subscriber and `version-responses` publisher
  on the broker it builds, returning that broker fully wired.

A module-level `broker = build_broker()` is still created for the entry point
(`main()` / `FastStream(broker)`), so nothing about running the worker changes.

```python
def build_broker(url: str | None = None) -> KafkaBroker:
    default_url = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    broker = KafkaBroker(url if url is not None else default_url)
    publisher = broker.publisher("version-responses", ...)

    @broker.subscriber("version-requests", ...)
    async def handle_version_request(msg: VersionRequest, logger: Logger) -> None:
        ...
        await publisher.publish(response)

    return broker


broker = build_broker()
```

This is the seam the integration test needs: it calls `build_broker(container_url)`
to get a fresh, self-contained broker pointed at a throwaway instance — no
import-order or module-cache games. The factory returns only the broker (one
clean type annotation); the subscriber/publisher become closures rather than
importable module globals, so tests assert on *observable behavior* (a response
delivered to a collector subscriber) instead of internal wiring. The handler and
publisher are no longer importable from the module — the unit test was updated
accordingly.

### 2. Testcontainers integration test + dedicated CI job

Add an integration test (marked `@pytest.mark.integration`) that starts the real
broker via testcontainers and round-trips a message through the actual driver,
and a CI job that runs only that marker. The job is **Ubuntu-only** (Docker is
reliably available on GitHub's Ubuntu runners but not macOS/Windows runners) and
**conditional on `include_worker`**, mirroring how ADR-007's `build-*-check` jobs
are conditional on their toggles. It is a per-backend job keyed off
`worker_broker`, not a fan-out over all four brokers, because a generated project
has exactly one broker.

The default `tox run` / `ci` matrix stays broker-free and fast: integration tests
are deselected there (`-m "not integration"`) and only the new job opts in
(`-m integration`). This keeps the cross-OS matrix honest (it never needs Docker)
while still gaining real-broker coverage on Linux.

### Why testcontainers over GitHub `services:`

- `services:` blocks are static YAML, health-checked by the runner, and only
  available on Linux runners anyway — so they buy nothing the container approach
  doesn't, and they can't express per-test lifecycle.
- testcontainers owns the container lifecycle *from the test*, so the same
  integration test runs identically on a developer laptop with Docker as it does
  in CI — no "works in CI only" divergence.
- It composes with the existing `.devcontainer` services rather than duplicating
  their definitions into workflow YAML.

## Consequences

- `worker/app.py` exposes `build_broker(url=None)` and keeps a module-level
  `broker = build_broker()`. The previously-importable `handle_version_request`
  and `version_response_publisher` become factory-local closures; the unit test
  was rewritten to assert on the response delivered to a collector subscriber
  rather than importing those names.
- A new `testcontainers[<broker>]` dependency joins the `test` dependency group
  (conditional on `include_worker`), kept current by Renovate like every other
  pin (ADR-003).
- A new `pytest` marker `integration` is registered in `pyproject.toml`, and the
  default `addopts` deselects it (`-m "not integration"`) so `tox run` stays
  Docker-free. An on-demand `[tool.tox.env.integration]` env (not in `env_list`,
  like the `worker` env) runs `pytest -m integration tests/worker` with
  `extras = ["all"]` + the `test` group.
- `ci.yml` gains one conditional, Ubuntu-only `worker-integration` job (rendered
  only when `include_worker`) that runs `tox run -e integration` against the chosen
  broker and gates the `check` aggregation job, in the same spirit as ADR-007's
  packaging guards.
- More template surface to test: the worker must now be exercised both in the
  default broker-free matrix and in the integration job, across the four
  `worker_broker` values — the same per-broker testing burden already called for
  in [ADR-007](007-standalone-executable-toggles.md)'s closing note.
- The integration test file is added to coverage `omit` (run and report). It is
  imported during default collection but its body is deselected, so without the
  omit its unexecuted lines would depress coverage below the `fail_under` gate.
- Filterwarnings: the testcontainers `@wait_container_is_ready` deprecation is
  ignored (worker-only, scoped to the `testcontainers` module — the ini
  `filterwarnings` module field is a regex, so the prefix matches), and the
  `integration` tox env runs with a broad `-W default::DeprecationWarning` so
  third-party deprecations surfaced by a *real* connection don't abort the run
  while the default suite stays strict. Module-scoping that `-W` demotion was
  attempted and **rejected**: CLI `-W` module matching is exact (not a regex),
  and drivers attribute warnings via `stacklevel` to arbitrary caller modules
  (the redis driver's `lib_name` deprecation surfaces through
  `redis.asyncio.connection`/faststream frames), so scoped filters miss them
  and the run aborts. The env also passes `--timeout` (pytest-timeout) so a
  wedged container or broker connection fails with a traceback instead of
  hanging until the CI job timeout.
- **Systemic coverage fix (done here).** Testing the worker surfaced a
  pre-existing, systemic gap: *no* optional-component project reached
  `fail_under = 99` out of the box (web ~96%, worker ~95%, gui/tui/mcp lower),
  because each component's process/UI entrypoints and defensive fallbacks were
  unexercised and `.example-input.yml` disables every component so that path was
  never CI-validated. Rather than fix the worker alone, the gap is closed
  uniformly (see the coverage exclusion note in `CLAUDE.md`), in two ways:

  - **Reachable error handling is tested, not excluded.** The missing-metadata
    paths that carry real behavior now have unit tests: the web `/version` and
    `/info` 503 responses, the CLI `version`/`info` exit-code-1 contract, the
    GUI/TUI "Version: unknown" degradation, and the MCP error-text response.
  - **Genuinely untestable code carries a per-site `# pragma: no cover`**: the
    blocking process entrypoints (`main()` in the web/MCP/worker apps and the
    `__main__` dispatchers, the MCP `run_server`), the raw display/launch
    functions (`_display_message`, `_display_tui`, the CLI
    `interactive`/`gui`/`web` subcommands), the worker lifecycle hooks, the
    c-extension `except ImportError` fallback, and the worker's module-level
    metadata fallback (unreachable wherever tests run — the package is always
    installed there).

  An earlier iteration excluded these via blanket `[tool.coverage.report]
  exclude_lines` regexes (`def main(`, `async def run_server`,
  `except PackageNotFoundError`). That was **rejected**: a regex matching a
  `def` line excludes the entire function body, so the patterns silently
  un-measured the *tested* GUI/TUI `main()` entrypoints and the web 503
  handlers, making the `fail_under` gate structurally blind to exactly the
  error handling it exists to protect. Per-site pragmas keep each exclusion
  decision visible and reviewable next to the code it affects.

  The same audit uncovered a subtler, universal defect: the `_version.py` omit
  glob was anchored on `src/**`, but tox/CI installs the built wheel/sdist into
  `.../site-packages/`, so the pattern missed the installed copy and reported
  `_version.py` at 0% — dragging *even the all-disabled base project* to ~92%
  under the real `tox` path (editable `pytest` hid it because there the file
  really is under `src/`). The omit globs are now anchored to match both
  layouts (`*/_version.py`, and `*/worker/test_integration.py` —
  directory-anchored so a future `test_integration.py` in another component,
  which *would* run in the default suite, stays measured).

  A related cross-environment defect surfaced only under the *full* multi-env
  `tox run`: `[tool.coverage.paths]` mapped `*/{pkg}/src/{pkg}`, which never
  matches tox's per-env `.tox/<env>/.../site-packages/{pkg}` install path, so
  `coverage combine` kept a separate copy per interpreter and version-gated lines
  covered in one but not another counted as missed (base fell to ~92% across five
  envs). The mapping is now `["src/{pkg}", "*/site-packages/{pkg}"]`, unifying all
  interpreters onto the canonical `src/` tree. Verified via the real multi-env
  `tox run` install path: every component, every combination, and the base project
  now report **100%**.
- **Explicitly out of scope:** the larger litestar-faststream *runtime*
  integration (running the FastStream broker inside the Litestar app via a shared
  lifespan + DI + AsyncAPI). That is a separate feature touching the
  `include_web` × `include_worker` intersection and is not part of this ADR.
