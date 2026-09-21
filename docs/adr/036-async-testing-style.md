# ADR-036: Make async testing an explicit template axis

## Context

Async components and their tests need a pytest runner, but a synchronous
library should not gain one merely because it was created from this template.

## Decision

`async_style` is an independent Copier choice with `none`, `asyncio`, and
`anyio` values. It defaults to `none` for a synchronous project and to
`asyncio` when an async-capable component is selected. The asyncio option adds
`pytest-asyncio` and uses strict mode, so every async test has an explicit
marker. The AnyIO option adds `anyio[trio]`; its generated fixture parametrizes
tests over asyncio and trio. Tests for asyncio-native integrations (currently
FastStream workers and Textual's headless pilot) explicitly select asyncio.

Generated async component tests use the marker selected by this setting. A
project that renders TUI, MCP, or worker tests cannot choose `none`, because
those tests are async. The dependency always remains in the test group.

## Consequences

New synchronous libraries retain a minimal test environment. Async projects
get a runner that works immediately, and adopters can choose broader backend
coverage without copying boilerplate. AnyIO may expose backend assumptions that
an asyncio-only suite would not; component tests that require asyncio document
and constrain that requirement locally.
