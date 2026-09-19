# ADR-034: Opt-in performance benchmarking

## Status

Accepted (2026-09).

## Context

Correctness, coverage, and static-analysis gates detect many regressions, but
not an otherwise-valid change that makes a hot path materially slower. Benchmark
timings must not make every generated project's default CI slower or require an
external service account.

## Decision

Provide `include_benchmarks`, disabled by default and enabled by the `full`
preset. It renders a `benchmarks/` starter suite using `pytest-codspeed`, a
registered `benchmark` pytest marker excluded from the ordinary test suite, and
`benchmark` tox/mise entry points for local runs.

The separate `benchmarks.yml` workflow runs CodSpeed simulation on default-branch
pushes and pull requests. It is gated on the `CODSPEED_TOKEN` secret, emits a
notice when not configured, and is intentionally excluded from the `check` merge
gate. This keeps the template self-contained by default and makes service setup
an explicit, reversible project-owner choice.

## Consequences

- Projects that leave the toggle off receive no benchmark dependency, workflow,
  marker, or benchmark directory.
- Enabled projects get a stable CI measurement service and PR performance deltas,
  but must register the repository with CodSpeed and set `CODSPEED_TOKEN`.
- The starter benchmark is deliberately small; maintainers add benchmarks for
  their own meaningful hot paths under `benchmarks/`.
