# Always-on pylint gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pylint as an always-on quality gate to the copier-pyproject template, wired into the `style` tox env and prek, with a curated generalized config.

**Architecture:** Edit the Jinja-rendered template files (`template/pyproject.toml.jinja`, `template/prek.toml.jinja`, `template/README.md.jinja`) so every generated project ships pylint in its `style` dependency group, a `[tool.pylint]` config, a `["pylint", "src"]` step in the tox `style` env, and a `local` prek hook. Verify by rendering a scratch project and running its `style` gate.

**Tech Stack:** Copier (Jinja templates), tox + tox-uv, prek, pylint 4.0.6, uv.

## Global Constraints

- Repo pins dependencies **exact** (`[tool.uv] add-bounds = "exact"`) — use `pylint==4.0.6`.
- These are **Jinja templates** under `template/`: edits are literal TOML except where existing `{% ... %}` conditionals appear. The pylint additions are **unconditional** (always-on — no `include_pylint` question).
- pylint's canonical invocation is `pylint src` (never tests; ruff owns tests).
- prek tools that need the installed package use a **`local`** hook via `uv run --locked --group style <tool>` (see the existing basedpyright/editorconfig-checker/sphinx-lint hooks) — do NOT add an upstream `rev`-pinned pylint repo.
- Branch: `feature/always-on-pylint`. Conventional Commits for messages.

---

### Task 1: Wire pylint into `template/pyproject.toml.jinja` (dep + config + tox step)

**Files:**
- Modify: `template/pyproject.toml.jinja` (three edits: `style` dep group; new `[tool.pylint]` block; tox `style` command list)

**Interfaces:**
- Produces: a rendered project whose `pyproject.toml` has `pylint==4.0.6` in `[dependency-groups].style`, a `[tool.pylint]` config, and a `["pylint", "src"]` entry in `[tool.tox.env.style].commands`.

- [ ] **Step 1: Add pylint to the `style` dependency group.** In `[dependency-groups]`, the `style = [` list, insert alphabetically between `mypy` and `pyrefly` (order: `mypy`, `pylint`, `pyrefly`, `ruff`):

```toml
  "mypy==2.1.0",
  "pylint==4.0.6",
  "pyrefly==1.1.1",
  "ruff==0.15.19",
```

- [ ] **Step 2: Add the `[tool.pylint]` config block.** Insert it immediately after the `[tool.pyrefly]` block (before `[tool.tox]` / the `{% if include_freezer %}` typos block if present):

```toml
[tool.pylint.main]
# pylint runs as an always-on gate that deliberately overlaps ruff's PL* rules.
# Its canonical invocation is `pylint src`, so it never descends into tests; this
# ignore-paths is a defensive scope guard for broader invocations (`pylint .`,
# filename-passing hooks). Tests are linted by ruff, not pylint.
ignore-paths = ["^tests/.*$"]

[tool.pylint."messages control"]
# Only formatter-owned checks, the docstring family, and too-few-public-methods
# are disabled so pylint is usable out of the box; everything else stays on.
disable = [
  "line-too-long",              # C0301 — ruff-format owns line length
  "missing-module-docstring",   # C0114
  "missing-class-docstring",    # C0115
  "missing-function-docstring", # C0116
  "too-few-public-methods",     # R0903 — trips dataclasses / config / Protocol classes
]

[tool.pylint.design]
max-args = 10
max-positional-arguments = 10
max-branches = 20
```

- [ ] **Step 3: Add the tox `style` command.** In `[tool.tox.env.style]`, the `commands = [` list, insert `["pylint", "src"]` immediately after the `["zuban", "check", "src"]` entry and before `["vulture"]`:

```toml
  ["zuban", "check", "src"],
  ["pylint", "src"],
  ["vulture"],
```
(The rendered form may be multi-line arrays; match the surrounding style — one array element either way.)

- [ ] **Step 4: Render a scratch project and verify the three additions.**

Run:
```bash
cd /tmp && rm -rf pylint-check && \
uvx copier@latest copy --trust --overwrite --defaults \
  --data github_user=tester --data github_repo_name=demo \
  --data "author_full_name=Test User" --data author_email=t@example.com \
  --data include_cli=true --data include_tui=true --data include_web=false \
  --data include_gui=false --data include_pydantic_settings=false \
  <ABS_PATH_TO>/copier-pyproject/ /tmp/pylint-check
grep -nE 'pylint==4.0.6|\[tool.pylint|"pylint", "src"' /tmp/pylint-check/pyproject.toml
```
Expected: all three present (dep line, `[tool.pylint.main]`, and the tox command).

- [ ] **Step 5: Commit.**

```bash
git add template/pyproject.toml.jinja
git commit -m "feat: add always-on pylint to the style gate (pyproject)"
```

---

### Task 2: Add the pylint prek hook to `template/prek.toml.jinja`

**Files:**
- Modify: `template/prek.toml.jinja` (the `[[repos]] repo = "local"` block that holds basedpyright/editorconfig-checker/sphinx-lint)

**Interfaces:**
- Consumes: the `pylint==4.0.6` entry in the `style` group (Task 1) — the hook resolves pylint from that group.
- Produces: a rendered `prek.toml` with a `pylint` local hook.

- [ ] **Step 1: Add the hook.** In the existing `[[repos]] repo = "local"` block that contains the `basedpyright` hook (`entry = "uv run --locked --group style basedpyright"`), add a sibling `pylint` hook:

```toml
  { id = "pylint", name = "Pylint", entry = "uv run --locked --group style pylint src", language = "system", pass_filenames = false, always_run = true },
```
Place it adjacent to the `basedpyright` entry (both are `uv run --group style` local hooks). `pass_filenames = false` keeps the invocation to the canonical `pylint src`; `always_run = true` runs it even when no `.py` files are in the change set (parity with the `basedpyright`/`pytest` local hooks).

- [ ] **Step 2: Render and verify the hook is present.**

Run (re-render as in Task 1 Step 4, then):
```bash
grep -n 'id = "pylint"' /tmp/pylint-check/prek.toml
```
Expected: the pylint hook line is present.

- [ ] **Step 3: Commit.**

```bash
git add template/prek.toml.jinja
git commit -m "feat: add pylint prek hook (local, style group)"
```

---

### Task 3: Add pylint to the README tooling description

**Files:**
- Modify: `template/README.md.jinja` (the "Code Quality" feature bullet, ~line 232)

**Interfaces:**
- Produces: rendered README mentions pylint in the quality-tooling list.

- [ ] **Step 1: Update the Code Quality bullet.** Change the line that reads:

```markdown
- **Code Quality**: Comprehensive linting and formatting with ruff, plus architecture-contract enforcement with import-linter
```
to include pylint:
```markdown
- **Code Quality**: Comprehensive linting and formatting with ruff and pylint, plus architecture-contract enforcement with import-linter
```

- [ ] **Step 2: Render and verify.**

Run (re-render, then):
```bash
grep -n 'ruff and pylint' /tmp/pylint-check/README.md
```
Expected: the updated bullet is present.

- [ ] **Step 3: Commit.**

```bash
git add template/README.md.jinja
git commit -m "docs: mention pylint in the README quality-tooling list"
```

---

### Task 4: End-to-end gate verification and tuning

**Files:**
- Possibly modify: `template/pyproject.toml.jinja` (add `extras = ["all"]` to `[tool.tox.env.style]` and/or extend the pylint `disable` list — only if verification requires it)

**Interfaces:**
- Consumes: the fully wired template (Tasks 1–3).
- Produces: a generated project whose `tox -e style` and `prek run pylint` pass green.

- [ ] **Step 1: Generate a representative scratch project and install it.**

```bash
cd /tmp && rm -rf pylint-e2e && \
uvx copier@latest copy --trust --overwrite --defaults \
  --data github_user=tester --data github_repo_name=demo \
  --data "author_full_name=Test User" --data author_email=t@example.com \
  --data include_cli=true --data include_tui=true --data include_web=false \
  --data include_gui=false --data include_pydantic_settings=false \
  <ABS_PATH_TO>/copier-pyproject/ /tmp/pylint-e2e
cd /tmp/pylint-e2e && git init -q && git add -A && uv sync
```

- [ ] **Step 2: Run pylint directly on the generated skeleton first.**

Run: `cd /tmp/pylint-e2e && uv run --group style pylint src`
Expected: exit 0. **If `import-error` (E0401) fires** on an optional component (e.g. `textual`): the `style` env lacks the extras. Fix by adding `extras = ["all"]` to `[tool.tox.env.style]` in `template/pyproject.toml.jinja`, re-render, `uv sync`, re-run. **If a legitimate pylint finding fires on the generated code** (not import-error): add the specific message id to the `disable` list in the `[tool.pylint."messages control"]` block with a one-line rationale, re-render, re-run. Iterate until exit 0.

- [ ] **Step 3: Run the full style gate through tox.**

Run: `cd /tmp/pylint-e2e && uv run --locked tox run -e style`
Expected: `style: OK` (pylint runs as one of the commands and passes).

- [ ] **Step 4: Run the prek hook.**

Run: `cd /tmp/pylint-e2e && uv run --locked --group prek prek run pylint --all-files`
Expected: `Pylint ... Passed`.

- [ ] **Step 5: Convergence check.** Confirm the change does not create update churn for already-adopted projects:

Run: from an existing generated project checkout, `uvx copier@latest update --pretend --trust --defaults --vcs-ref=<its _commit>` still reports up-to-date (this is a sanity check that the template renders cleanly; a genuine new pylint block is expected to appear only on a real update to a newer ref).

- [ ] **Step 6: Commit any tuning made in this task.**

```bash
git add template/pyproject.toml.jinja
git commit -m "fix: ensure the generated style gate runs pylint green"
```
(Skip if Steps 2–5 required no edits.)

---

### Task 5: Open the PR

**Files:** none (git/gh only)

- [ ] **Step 1: Push the branch.**

```bash
cd <ABS_PATH_TO>/copier-pyproject && git push -u origin feature/always-on-pylint
```

- [ ] **Step 2: Open the PR** with `gh pr create`, title `feat: add always-on pylint quality gate`, body summarizing: the decision (always-on, full pylint, curated baseline), the files changed, and the verification performed (generated a cli+tui project → `tox -e style` + `prek run pylint` green). Link the design spec `docs/superpowers/specs/2026-08-04-always-on-pylint-design.md`.

- [ ] **Step 3: Report** the PR URL and note the olink rollout is a separate follow-up (via `copier update` once this ships a new template version).

---

## Self-Review

- **Spec coverage:** dep + `[tool.pylint]` config + tox step (Task 1), prek hook (Task 2), README/docs (Task 3), verification incl. extras/baseline tuning + convergence (Task 4), PR (Task 5) — all spec sections mapped.
- **Placeholders:** `<ABS_PATH_TO>` and `<its _commit>` are execution-time literals the implementer fills from their environment, not design gaps. pylint version is concrete (`4.0.6`).
- **Type/name consistency:** the hook id (`pylint`), the tox command (`["pylint", "src"]`), the dep (`pylint==4.0.6`), and the config table names (`[tool.pylint.main]`, `[tool.pylint."messages control"]`, `[tool.pylint.design]`) are used consistently across tasks.
