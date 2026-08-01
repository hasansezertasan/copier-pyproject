# Design: Adopt import-linter for architecture contracts

- **Date:** 2026-08-01
- **Status:** Approved (design), pending implementation
- **Related:** ADR-013 (to be created), [ADR-003](../../adr/003-tox-as-canonical-lint-runner.md) (tox as canonical lint runner), [ADR-005](../../adr/005-five-type-checkers-basedpyright-strict.md) (deep-analysis tools live in the style env)

## Problem

The generated package is `core/` + `utils/` (foundational) plus a set of **independent,
toggleable components** — `cli/`, `web/`, `gui/`, `tui/`, `mcp/`, `worker/`. Each component
is optional (gated on an `include_*` toggle) and is *meant* to be independent: a user can
generate a project with `web` but not `cli`. If `web/` imported `cli/`, that is a latent
bug — an import of a sibling that may not be installed. Nothing in the current toolchain
catches architectural import violations:

- The 5 type checkers (mypy, basedpyright, ty, pyrefly, zuban), ruff, vulture, slotscheck,
  etc. check types/style/dead-code — none enforce *which module may import which*.

[import-linter](https://import-linter.readthedocs.io/) (`lint-imports`) fills exactly this
gap: it builds the static import graph (via `grimp`, AST-based — it does **not** execute
module code) and enforces declared contracts.

## Decision summary

Adopt import-linter as an **always-on** style tool (no copier toggle, like ruff/mypy),
delivered through the `style` dependency group and the tox `style` env, enforcing a
**single `layers` contract** that captures both component independence and core/utils
layering.

## The contract — one `layers` contract does both

Rendered into the generated `pyproject.toml`:

```toml
[tool.importlinter]
root_package = "{{github_repo_name}}"

[[tool.importlinter.contracts]]
name = "Layered architecture with independent components"
type = "layers"
# Modules on one line separated by ` | ` are SIBLINGS: they may not import each
# other (independence), and may only import lower layers. Lower layers may never
# import a higher layer. `__metadata__` is intentionally outside the contract.
layers = [
    "{{github_repo_name}}.cli",                            # orchestrator, only if include_cli
    "{{github_repo_name}}.web | ...other enabled components...",
    "{{github_repo_name}}.core",
    "{{github_repo_name}}.utils",
]
```

> **Revised during implementation:** `cli` is on its own higher layer, not a
> sibling. The CLI's `web`/`gui`/`tui` subcommands lazy-import those components to
> launch them (`cli/app.py` → `web.app`, `gui.app`, `tui.app`), so `cli` is a
> legitimate orchestrator above the independent component group. This models
> reality and needs **no `ignore_imports`** for any toggle combination; the only
> guarantee given up is forbidding `cli -> mcp`/`cli -> worker` (harmless — `cli`
> is the top-level entry point). `mcp`/`worker` stay in the sibling group.

- **Independence** — pipe-separated component siblings (`web`/`gui`/`tui`/`mcp`/`worker`)
  cannot import each other.
- **Layers** — `cli` (orchestrator) may import any component; components may import
  `core`/`utils`; `core`/`utils` can never import a component; `utils` sits **below**
  `core`. This matches current reality (`core` does not import `utils`; `utils` imports
  nothing internal) and keeps `utils` a dependency-free leaf. `__metadata__` (imported by
  `core`) is left outside the contract as an unconstrained foundation.

### Why one contract, not literal `independence` + `layers` contracts

- **DRY** — a single module list, one source of truth.
- **Provably equivalent** — layer siblings already give the independence guarantee, and
  the ordering gives the layering guarantee.
- **Graceful degradation** — with 0–1 components (e.g. the everything-off
  `.example-input.yml`), a dedicated `independence` contract would be degenerate/erroring,
  whereas this simply becomes a valid `core > utils` 2-layer contract that still forbids
  `utils -> core`.

A comment in the rendered TOML documents the sibling-independence semantic so a reader who
doesn't know import-linter's pipe syntax isn't surprised.

## The toggle problem — Jinja-conditional top layer

Because components are optional, the top layer line is **Jinja-assembled** from only the
enabled `include_*` toggles, pipe-joined. If no components are enabled, the line is omitted
entirely and the contract is the 2-layer `core > utils`. The rendered config therefore
never references a component the project does not have — consistent with the template's
clean-output ethos.

Rendering approach (in `pyproject.toml.jinja`): build a list of enabled component module
paths, then emit `"{{ comps | join(' | ') }}"` only when the list is non-empty. Component
→ module map: `cli`→`.cli`, `web`→`.web`, `gui`→`.gui`, `tui`→`.tui`, `mcp`→`.mcp`,
`worker`→`.worker`, each prefixed with `{{github_repo_name}}`.

## Delivery — style env only, not prek

- Add `import-linter==2.13` to the `style` dependency group in `pyproject.toml.jinja`
  (alphabetical position: between `editorconfig-checker` and `mypy`). `import-linter 2.13`
  requires Python `>=3.10`, matching the template's floor exactly.
- Add one command `["lint-imports"]` to the tox `style` env (config auto-read from
  `[tool.importlinter]`; no CLI flags needed). Place it near the other whole-project
  analyzers (e.g. after `slotscheck`).
- **Not** a prek hook. Like the 5 type checkers, vulture, and slotscheck, import-linter
  needs the **installed package** and whole-import-graph analysis. The tox `style` env
  installs the project (no `skip_install`/`package="skip"`), so `grimp` can resolve
  `{{github_repo_name}}`; prek's isolated hook envs do not install the project. This keeps
  the existing boundary: prek = fast local gate, tox `style` = deep-analysis gate. The CI
  `hooks` job is unaffected; the CI `style` job gains the check for free.
- **Renovate** tracks `import-linter` automatically as a normal pinned PyPI dependency in
  the `style` group — no custom manager config.
- **taplo** (format) and **validate-pyproject** tolerate the new `[tool.importlinter]` /
  `[[tool.importlinter.contracts]]` tool tables (unknown-tool tables are ignored by
  validate-pyproject; taplo just formats them).

## Documentation changes

- **ADR-013** — `docs/adr/013-import-linter-for-architecture-contracts.md`: the always-on
  decision, the single-`layers`-contract rationale, the `utils`-below-`core` choice, and
  the prek-exclusion rationale. Follow the existing ADR file format (001–012).
- **CLAUDE.md** — add `import-linter` to the style-env tool list in the Development
  Commands section (the "Run style checks (ruff, mypy, …)" parenthetical) and a short note
  in the tooling/`style`-env description.
- **README.md** — add import-linter to the linter/tooling list.

## Verification plan

1. Regenerate `example/` **with components enabled** (not the everything-off default) and
   run `cd example && uv run --locked tox run -e style` — `lint-imports` must pass.
2. Regenerate with the everything-off `.example-input.yml` and confirm `tox -e style` still
   passes (the 2-layer `core > utils` contract).
3. **Negative test** — in a scratch generation with `web` + `cli` enabled, add a
   `{{github_repo_name}}.cli` import inside `web/app.py`, confirm `lint-imports` **fails**,
   then revert. Proves the guardrail actually bites.
4. Run the full template test flow per CLAUDE.md ("Testing Template Changes"): regenerate,
   `tox -e style`, `tox run`.

## Out of scope (YAGNI)

- No additional `forbidden` / `independence` / `acyclic` contracts.
- No `copier.yml` toggle — always-on like ruff/mypy.
- No prek hook.
- No per-component `ignore_imports` unless the negative test surfaces a *legitimate* shared
  import that must be allowed.
