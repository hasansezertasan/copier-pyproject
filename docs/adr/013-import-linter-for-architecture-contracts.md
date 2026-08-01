# ADR-013: import-linter for architecture contracts

## Status

Accepted (2026-08).

## Context

The generated package is `core/` + `utils/` (foundational) plus a set of
optional, toggleable components (`cli`, `web`, `gui`, `tui`, `mcp`, `worker`).
Each component is gated on an `include_*` toggle and is meant to be independent:
a project may render `web` without `gui`, so a `web -> gui` import is a latent
bug — an import of a sibling that may not even be installed. The one intentional
exception is `cli`: its `web`/`gui`/`tui` subcommands lazy-import those components
to launch them, so `cli` is an *orchestrator* that legitimately sits above the
other components. None of the existing tools (the five type checkers, ruff,
vulture, slotscheck, …) enforce *which module may import which*. `core` currently
does not import `utils`, and `utils` imports nothing internal, so `utils` is a
true leaf.

## Decision

Adopt [import-linter](https://import-linter.readthedocs.io/) (`lint-imports`) as
an always-on style tool — no `copier.yml` toggle, like ruff/mypy.

### 1. One `layers` contract expresses both guarantees

A single `type = "layers"` contract stacks, high→low: `cli` (orchestrator layer,
present only when `include_cli`), the enabled non-`cli` components as
pipe-separated independent siblings (`web | gui | tui | mcp | worker`), then
`core`, then `utils`. import-linter's sibling semantics give the *independence*
guarantee (siblings may not import each other), the layer ordering gives the
*layering* guarantee (lower layers never import upward), and putting `cli` on its
own higher layer captures its legitimate orchestration imports without any
`ignore_imports`. Two separate `independence` + `layers` contracts would be
redundant. It also degrades gracefully: with 0–1 components a dedicated
`independence` contract is degenerate, whereas this becomes a valid `core > utils`
contract. `__metadata__` is left outside the contract as an unconstrained
foundation. The only guarantee deliberately not enforced is `cli -> mcp`/`cli ->
worker` (harmless — `cli` is the top-level entry point).

### 2. `utils` below `core`

Matches current reality (`core` does not import `utils`; `utils` is a
dependency-free leaf) and encodes the conventional "utils = leaf helpers" model.

### 3. Style env only, not prek

import-linter needs the installed package and a whole-import-graph build (via
`grimp`). The tox `style` env installs the project, so `lint-imports` resolves
the package; prek's isolated hook envs do not install it. This preserves the
existing boundary — prek is the fast local gate, tox `style` is the deep-analysis
gate (the same reason the five type checkers, vulture, and slotscheck are
style-env-only). Renovate tracks the pin as an ordinary `style`-group dependency.

## Consequences

- Cross-component imports and upward imports into `core`/`utils` now fail CI's
  `style` job (and local `tox -e style`).
- The contract config is Jinja-conditional on the enabled components, so a
  component's contract coverage is only exercised when that component is
  generated — verify by generating with components enabled (per CLAUDE.md's
  testing-template-changes flow), not the everything-off `.example-input.yml`.
- Adds one tool to an already-dense `style` env; justified by filling the sole
  architecture-enforcement gap in the toolchain.
