# ADR-014: import-linter for architecture contracts

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
foundation. The only import boundary import-linter cannot forbid is `cli -> mcp`
/ `cli -> worker` — but `cli` legitimately sits above them as the top-level
entry point, so this is harmless.

### 2. `utils` below `core`

Matches current reality (`core` does not import `utils`; `utils` is a
dependency-free leaf) and encodes the conventional "utils = leaf helpers" model.

### 3. Both the tox `style` env and prek (via a `local` `system` hook)

import-linter needs the installed package and a whole-import-graph build (via
`grimp`). The tox `style` env installs the project, so `lint-imports` resolves
the package. prek can run it too — but **only** as a `local` `language = "system"`
hook that shells out through `uv run --locked --group style lint-imports`, which
syncs and resolves the installed package. It is *not* eligible as the upstream
**repo hook** import-linter ships, because prek (like pre-commit) runs a repo
hook in its own isolated venv with only the hook's own deps — the project is not
installed there, so `grimp` cannot build the graph. This is exactly how
`basedpyright` — the other whole-program analyzer — is already delivered, so
import-linter follows that precedent: a `style`-group command run from both the
tox `style` env (the canonical full suite, ADR-003) and a prek `local` hook (the
fast local + CI `hooks`-job gate, catching contract violations at commit time).
Renovate tracks the pin as an ordinary `style`-group dependency; the prek hook
needs no separate `rev`. The earlier revision of this ADR kept it style-env-only
on the imprecise premise that "prek cannot install the package" — true of the
isolated **repo-hook** pattern, but not of the `local` `system` hook used here
(verified end-to-end: an injected upward import fails `prek run import-linter`
with a non-zero exit).

**slotscheck** is delivered the same way, and for the same reason. It imports
every module under `src/` to verify `__slots__`, so it also needs the installed
package and cannot be an isolated repo hook. It checks a property no other tool
covers (like import-linter's architecture check), so — unlike the redundant type
checkers `ty`/`pyrefly`/`zuban`, which stay style-env-only to avoid stacking five
type checkers on the fast gate — it is worth running on the prek gate too, as a
`local` `system` hook (`uv run --locked --group style python -m slotscheck src`).

## Consequences

- Cross-component imports and upward imports into `core`/`utils` now fail CI's
  `style` job (and local `tox -e style`).
- The contract config is Jinja-conditional on the enabled components, so a
  component's contract coverage is only exercised when that component is
  generated — verify by generating with components enabled (per CLAUDE.md's
  testing-template-changes flow), not the everything-off `.example-input.yml`.
- Adds one tool to an already-dense `style` env; justified by filling the sole
  architecture-enforcement gap in the toolchain.
