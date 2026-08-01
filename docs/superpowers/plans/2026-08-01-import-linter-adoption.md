# import-linter Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add import-linter as an always-on style tool that enforces one `layers` contract in every generated project — components (`cli`/`web`/`gui`/`tui`/`mcp`/`worker`) mutually independent and layered above `core` above `utils`.

**Architecture:** A single `[tool.importlinter]` block in `template/pyproject.toml.jinja` declares one `layers`-type contract. The top layer is a Jinja-assembled, pipe-joined list of only the *enabled* component modules (pipe-siblings are mutually independent and may only import downward). `core` sits above `utils`; `__metadata__` is left outside the contract. Delivered through the `style` dependency group + a `lint-imports` command in the tox `style` env — **not** prek (it needs the installed package + whole-graph analysis, which the tox `style` env provides and prek's isolated envs do not).

**Tech Stack:** Copier + Jinja2 templating, import-linter 2.13 (`lint-imports` CLI, `grimp` static graph), uv, tox.

## Global Constraints

- import-linter pin: **`import-linter==2.13`** (requires-python `>=3.10`, matches the template floor). Exact-pin format like every other `style` dep.
- The contract config must **never reference a component module that was not generated** — the top-layer line is Jinja-conditional and omitted entirely when no components are enabled.
- Always-on: **no `copier.yml` toggle** (like ruff/mypy).
- **Not** a prek hook — style env only.
- All new TOML lives in `template/pyproject.toml.jinja` (the generated project's config), not the template repo's own `pyproject.toml`.
- Package module prefix in all module paths is `{{github_repo_name}}` (Jinja variable).
- Follow template conventions: generated comments use `#`, whitespace-control `{%-`/`-%}` to avoid blank lines.

---

### Task 1: Wire import-linter into the generated project

**Files:**
- Modify: `template/pyproject.toml.jinja` — `style` dep group (after line 176), new `[tool.importlinter]` block (after the `[tool.slotscheck]` block, ~line 427), tox `style` command list (after the `slotscheck` command, ~line 674)

**Interfaces:**
- Produces: a generated `pyproject.toml` with `[tool.importlinter]` `root_package = "<pkg>"` and one `[[tool.importlinter.contracts]]` of `type = "layers"`; the tox `style` env runs `lint-imports`. Task 2 (docs) describes this behavior but consumes no symbols.

- [ ] **Step 1: Add the dependency to the `style` group**

In `template/pyproject.toml.jinja`, insert this line between `"editorconfig-checker==3.6.1",` (line 176) and `"mypy==2.1.0",` (line 177), preserving 2-space indentation:

```toml
  "import-linter==2.13",
```

- [ ] **Step 2: Add the `[tool.importlinter]` contract block**

In `template/pyproject.toml.jinja`, immediately after the `[tool.slotscheck]` block (the two lines `[tool.slotscheck]` / `strict-imports = false`, ~line 426-427) and before `[tool.ruff]`, insert:

```jinja
[tool.importlinter]
root_package = "{{github_repo_name}}"


[[tool.importlinter.contracts]]
name = "Layered architecture with independent components"
type = "layers"
# Layers are listed high -> low: a layer may import lower layers but never a
# higher one. Modules joined by ` | ` on one line are independent SIBLINGS that
# may not import each other. `cli` is the orchestrator layer — its subcommands
# launch the other components (web/gui/tui) via lazy imports — so it sits ABOVE
# the independent component group, which sits above `core`, which sits above the
# leaf `utils`. `__metadata__` is left outside the contract as an unconstrained
# foundation.
layers = [
{%- if include_cli %}
  "{{github_repo_name}}.cli",
{%- endif %}
{%- set il_components = [] -%}
{%- if include_web %}{% set _ = il_components.append(github_repo_name ~ ".web") %}{% endif -%}
{%- if include_gui %}{% set _ = il_components.append(github_repo_name ~ ".gui") %}{% endif -%}
{%- if include_tui %}{% set _ = il_components.append(github_repo_name ~ ".tui") %}{% endif -%}
{%- if include_mcp %}{% set _ = il_components.append(github_repo_name ~ ".mcp") %}{% endif -%}
{%- if include_worker %}{% set _ = il_components.append(github_repo_name ~ ".worker") %}{% endif -%}
{%- if il_components %}
  "{{ il_components | join(' | ') }}",
{%- endif %}
  "{{github_repo_name}}.core",
  "{{github_repo_name}}.utils",
]
```

Rationale for `cli` on its own higher layer (not a sibling): the CLI's
`web`/`gui`/`tui` subcommands legitimately lazy-import those components to launch
them (`cli/app.py` imports `web.app`, `gui.app`, `tui.app`). Modelling `cli` as
an orchestrator layer above the independent component group captures this
truthfully and needs **no `ignore_imports`** for any toggle combination. The only
guarantee given up is forbidding `cli -> mcp`/`cli -> worker` (harmless — `cli`
is the top-level entry point). `mcp`/`worker` remain in the independent sibling
group. Notes: `{% set _ = list.append(...) %}` is the standard Jinja2
side-effect append idiom (Copier's Jinja supports it); `cli` is intentionally
NOT added to `il_components` since it is its own layer.

- [ ] **Step 3: Add `lint-imports` to the tox `style` env**

In `template/pyproject.toml.jinja`, in the `[tool.tox.env.style]` `commands` list, insert this command block immediately after the `slotscheck` command block (the `["python", "-m", "slotscheck", "src"]` block ending ~line 674) and before the `taplo` command:

```toml
  [
    "lint-imports",
  ],
```

- [ ] **Step 4: Render a project WITH components + a planted violation (red)**

```bash
cd /Users/hasansezertasan/orca/workspaces/copier-pyproject/nuckelavee
copier copy --data-file .example-input.yml \
  --data include_cli=true --data include_web=true \
  --defaults --trust . /tmp/il-test --force
cd /tmp/il-test && uv sync --group style
```

Then plant a forbidden cross-component import — add this line near the top imports of the web app module (find it with `ls src/*/web/app.py`):

```python
from il_test.cli import app as _forbidden  # noqa
```

(Replace `il_test` with the generated package name if different — it is the `github_repo_name` you rendered with; here `/tmp/il-test` → package `il_test`.)

Run:

```bash
uv run lint-imports
```

Expected: **FAILS**, reporting a broken "Layered architecture with independent components" contract with an illegal import from `web` to `cli`. This proves the guardrail bites.

- [ ] **Step 5: Remove the violation and confirm it passes (green)**

Delete the planted `_forbidden` import line, then:

```bash
uv run lint-imports
```

Expected: **PASSES** — "Contracts: 1 kept, 0 broken."

- [ ] **Step 6: Confirm the everything-off render still passes**

```bash
cd /Users/hasansezertasan/orca/workspaces/copier-pyproject/nuckelavee
copier copy --data-file .example-input.yml --defaults --trust . /tmp/il-test-bare --force
cd /tmp/il-test-bare && uv sync --group style && uv run lint-imports
```

Expected: **PASSES** with the 2-layer `core > utils` contract (the top component-layer line is absent from `pyproject.toml` — verify with `grep -A12 importlinter pyproject.toml`; there must be no `.cli`/`.web`/etc.).

- [ ] **Step 7: Run the full style env on the components render**

```bash
cd /tmp/il-test && uv run --locked tox run -e style
```

Expected: PASS (import-linter integrated alongside the existing checkers; taplo will have already normalized the new TOML during earlier renders).

- [ ] **Step 8: Commit**

```bash
cd /Users/hasansezertasan/orca/workspaces/copier-pyproject/nuckelavee
git add template/pyproject.toml.jinja
git commit -m "feat: enforce architecture contracts with import-linter"
```

---

### Task 2: Document the decision (ADR-013 + CLAUDE.md + READMEs)

**Files:**
- Create: `docs/adr/013-import-linter-for-architecture-contracts.md`
- Modify: `CLAUDE.md` — style-checks parenthetical (line 50) + a note in the tooling prose
- Modify: `README.md` — QA-stack list (line 9)
- Modify: `template/README.md.jinja` — "Code Quality" feature bullet (line 230)

**Interfaces:**
- Consumes: the behavior implemented in Task 1 (single `layers` contract, style-env-only delivery). No code symbols.

- [ ] **Step 1: Write ADR-013**

Create `docs/adr/013-import-linter-for-architecture-contracts.md` mirroring the ADR-012 section format (`## Status`, `## Context`, `## Decision` with `###` subsections, `## Consequences`):

```markdown
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
```

- [ ] **Step 2: Update CLAUDE.md — style-checks parenthetical**

In `CLAUDE.md` line 50, add `import-linter` to the parenthetical tool list. Change:

```
# Run style checks (ruff, mypy, basedpyright, ty, pyrefly, zuban, vulture, slotscheck, taplo, validate-pyproject, typos, actionlint, editorconfig-checker, sphinx-lint)
```

to:

```
# Run style checks (ruff, mypy, basedpyright, ty, pyrefly, zuban, vulture, slotscheck, import-linter, taplo, validate-pyproject, typos, actionlint, editorconfig-checker, sphinx-lint)
```

- [ ] **Step 3: Update CLAUDE.md — tooling prose note**

In `CLAUDE.md`, immediately after the paragraph ending "…there is no Pants or Trunk config to drift against it (both were removed; see [ADR-003](../docs/adr/003-tox-as-canonical-lint-runner.md))." add a new paragraph:

```markdown
**import-linter** enforces the generated package's architecture: one always-on
`layers` contract (in `[tool.importlinter]`) keeps the optional components
(`cli`/`web`/`gui`/`tui`/`mcp`/`worker`) mutually independent and layered above
`core` above `utils`. The top-layer module list is Jinja-conditional on the
enabled components (omitted when none are enabled, leaving a `core > utils`
contract). Delivered via the `style` group + a `lint-imports` command in the tox
`style` env — **not** prek, because it needs the installed package and a
whole-import-graph build. See
[ADR-013](../docs/adr/013-import-linter-for-architecture-contracts.md).
```

(If the ADR relative path differs in your CLAUDE.md's other links, match the
existing `../docs/adr/...` convention already used in that file.)

- [ ] **Step 4: Update README.md — QA-stack list**

In `README.md` line 9, add `import-linter (architecture contracts)` to the QA-stack list. Change the segment `…slotscheck, taplo, validate-pyproject…` to `…slotscheck, import-linter (architecture contracts), taplo, validate-pyproject…`.

- [ ] **Step 5: Update template/README.md.jinja — Code Quality bullet**

In `template/README.md.jinja` line 230, change:

```
- **Code Quality**: Comprehensive linting and formatting with ruff
```

to:

```
- **Code Quality**: Comprehensive linting and formatting with ruff, plus architecture-contract enforcement with import-linter
```

- [ ] **Step 6: Verify the docs render / links**

```bash
cd /Users/hasansezertasan/orca/workspaces/copier-pyproject/nuckelavee
test -f docs/adr/013-import-linter-for-architecture-contracts.md && echo "ADR exists"
grep -q "import-linter" CLAUDE.md README.md template/README.md.jinja && echo "refs present"
```

Expected: both echo lines print.

- [ ] **Step 7: Commit**

```bash
cd /Users/hasansezertasan/orca/workspaces/copier-pyproject/nuckelavee
git add docs/adr/013-import-linter-for-architecture-contracts.md CLAUDE.md README.md template/README.md.jinja
git commit -m "docs: document import-linter adoption (ADR-013)"
```

---

## Self-Review

**Spec coverage:**
- Single `layers` contract, independence + layers, `utils` below `core` → Task 1 Step 2. ✓
- Jinja-conditional top layer / toggle problem → Task 1 Step 2 (`il_components` build) + Step 6 (everything-off verification). ✓
- `root_package` → Task 1 Step 2. ✓
- Delivery: `style` dep + tox command, not prek → Task 1 Steps 1, 3. ✓
- Version pin `import-linter==2.13` → Task 1 Step 1 / Global Constraints. ✓
- Verification incl. negative test → Task 1 Steps 4–7. ✓
- ADR-013, CLAUDE.md, README, generated README → Task 2. ✓
- Renovate/taplo/validate-pyproject tolerance → no action needed (automatic); noted in ADR. ✓
- YAGNI exclusions (no extra contracts, no toggle, no prek, no ignore_imports) → honored. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases" — all edits give exact content. ✓

**Type/name consistency:** Jinja var `il_components` used consistently; contract name "Layered architecture with independent components" identical across Task 1 and ADR text. ✓
