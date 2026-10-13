# Architecture contracts

## One exhaustive import-linter layers contract: cli above independent components above core above utils

**Id:** 3b7cdbee-7c66-4e52-9d7e-8ab0ffe32e56
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-014 ([`docs/adr/014-import-linter-for-architecture-contracts.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/014-import-linter-for-architecture-contracts.md))
**Revisit when:** `core` starts importing `utils`, a second orchestrator component appears, or a component needs an exception the layers model cannot express
**See:** components.md#secondary-components-are-subcommands-of-one-console-root-not-separate-scripts — 3d60ab14-8ff9-47db-b326-d7e82947a6cf — as of 2026-10-11

import-linter is an always-on style tool. A single `layers` contract stacks
`cli` (present only with `include_cli`), the enabled non-CLI components as
pipe-separated independent siblings, then `core`, then `utils`. The contract
is `exhaustive`, so any subpackage not named in the layers breaks it;
non-layer foundations (`__main__`, `__metadata__`, `_version`, `_c_extension`)
are listed as exhaustive ignores.

**Reason:** components are gated on toggles and meant to be independent — a
`web -> gui` import is a latent bug against a sibling that may not be
installed — and none of the existing tools enforce which module may import
which. Sibling semantics give independence, layer order gives layering, and a
separate `cli` layer captures its legitimate lazy-import orchestration without
ignore rules. Exhaustiveness closes the gap that motivated the tool: coding
agents and hurried humans add a top-level package (`data/`, `marketplace/`)
that an unlisted-is-unconstrained contract ignored; prose in the agent
instructions does not hold, a failing style run does. `utils` below `core`
matches current reality and the conventional leaf-helpers model.

**Rejected alternative:** separate `independence` plus `layers` contracts —
redundant, and `independence` is degenerate with zero or one component, whereas
the single contract degrades to a valid `core > utils`.

**Consequence:** the contract is Jinja-conditional on enabled components, so a
component's coverage is exercised only when it is generated; the one boundary
it cannot forbid (`cli` importing MCP or worker) is harmless because `cli`
legitimately sits on top.

## Whole-program analyzers are local system hooks backed by the `style` group

**Id:** 41f3397d-1afb-4e57-a0bd-b5ef85089bfc
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-014 §4 ([`docs/adr/014-import-linter-for-architecture-contracts.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/014-import-linter-for-architecture-contracts.md)); the same delivery is recorded for basedpyright in ADR-005 and sphinx-lint in ADR-011
**Revisit when:** prek gains a way to run repo hooks with the project installed, or the fast gate becomes too slow
**See:** lint-orchestration.md#the-tox-style-env-is-the-sole-authoritative-lint-suite-prek-is-a-fast-gate-not-a-second-suite — 9b74fc8b-a808-4f2b-bdbd-9e4253c1b35a — as of 2026-10-11

import-linter and slotscheck (like basedpyright, mypy and sphinx-lint) run on
the prek gate as `local` `language = "system"` hooks that shell through
`uv run --locked --group style`, and in the tox `style` env from the same
group. Neither uses the upstream repo hook the tool ships.

**Reason:** both need the installed package and a whole-import-graph build
(grimp) or an import of every module (slotscheck). prek runs a repo hook in its
own isolated venv with only the hook's own deps, so the project is not
installed there and the graph cannot be built. A local system hook sees the
project's real environment, uses the single `style` pin (no second `rev` for
Renovate), and verified end-to-end that an injected upward import fails the
hook. slotscheck is worth the fast gate because it checks a property nothing
else covers; the redundant type checkers `ty`/`pyrefly`/`zuban` stay
style-env-only so five type checkers do not stack on every commit.

**Rejected alternative:** style-env-only for import-linter — an earlier revision
of the record, on the imprecise premise that prek cannot install the package;
true of the isolated repo-hook pattern, not of the local system hook.
