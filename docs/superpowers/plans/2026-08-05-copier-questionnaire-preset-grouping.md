# Copier Questionnaire Preset + Grouping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `preset` question and logical grouping to `copier.yml` so scaffolding is faster and clearer, without changing any generated file or breaking existing projects.

**Architecture:** A new stored `preset` question (minimal/standard/full/custom) plus one hidden `preset_map` computed variable seed every `include_*` toggle's *default*. Every toggle is still asked and stored, so the stored answer schema and `--defaults` output are unchanged. Questions are reordered into logical groups and `redis_backend`'s `when:` is widened. Before/after messages are added.

**Tech Stack:** Copier 9.11.3 (`type: yaml`/`bool` questions, `when:` gating, `_message_before_copy`/`_message_after_copy`), Jinja2 defaults, `uv`, `tox`.

## Global Constraints

- Copier 9.11.3 is the floor (`type: yaml` computed vars, dict `choices` all required).
- **Byte-identical `--defaults` output:** rendering `.example-input.yml --defaults` must produce output identical to the pre-change template. This is the backward-compat gate for every downstream project.
- **`template/` files stay unchanged, with ONE approved exception:** the
  `redis_backend` fix also requires `template/.devcontainer/docker-compose.yml.jinja:3-4`
  to gate `redis_image`/`redis_cli` on `redis_enabled` instead of `include_redis`
  (surfaced by Task 3's acceptance test; user-adjudicated during execution).
  Otherwise only `copier.yml`, `.example-input.yml`, `README.md`, `CLAUDE.md`.
- **Do not add `_tasks`** (ADR-015) — the after-copy message is text only, not a task.
- Stored answer *names* must not change (`include_*` bools stay). `preset` is added; `preset_map` is `when: false` and must NOT be stored.
- `custom` preset's enabled set must equal today's defaults exactly: `include_cli`, `include_web`, `include_gui`, `include_tui`, `include_pydantic_settings` on; everything else off.
- Spec: `docs/superpowers/specs/2026-08-05-copier-questionnaire-preset-grouping-design.md`.

---

### Task 1: Capture the backward-compatibility baseline

Render the current template to a reference directory *before* touching `copier.yml`. Task 2 diffs against this; if it's captured after the edit it proves nothing.

**Files:**
- Create (scratch, not committed): `/tmp/copier-baseline/`

- [ ] **Step 1: Render the current template as the baseline**

Run from the repo root:
```bash
rm -rf /tmp/copier-baseline && \
uv run copier copy --data-file .example-input.yml --defaults --force . /tmp/copier-baseline
```
Expected: renders successfully (exit 0), `/tmp/copier-baseline/pyproject.toml` exists.

- [ ] **Step 2: Freeze a checksum manifest of the baseline**

Run:
```bash
cd /tmp/copier-baseline && find . -type f -not -path './.git/*' | sort | xargs shasum > /tmp/copier-baseline.sha && cd - && wc -l /tmp/copier-baseline.sha
```
Expected: a non-empty `/tmp/copier-baseline.sha` (one line per rendered file). No commit in this task.

---

### Task 2: Rewrite `copier.yml` (preset, preset_map, grouping, `redis_backend`, messages) + `.example-input.yml`

The whole design lands in one file rewrite because `copier.yml` is a single cohesive questionnaire. The equivalence check against Task 1's baseline is the test.

**Files:**
- Modify (full replace): `copier.yml`
- Modify: `.example-input.yml` (add `preset: custom`)

**Interfaces:**
- Produces: a stored `preset` answer (values `minimal|standard|full|custom`) and a hidden `preset_map` (`when: false`, not stored). Every `include_*` bool now has `default: "{{ '<name>' in preset_map[preset] }}"`.

- [ ] **Step 1: Replace `copier.yml` with the target content**

Write `copier.yml` exactly as:

```yaml
---
_subdirectory: template
# No `_tasks`: defining any task marks the template "unsafe", which forces
# `copier ... --trust`. The hosted Mend Renovate App runs `copier update` with
# scripts disabled (no `--trust`), so a task-bearing template would break
# Renovate's copier manager — the mechanism that opens template-update PRs in
# generated projects (ADR-015). Keeping `_tasks` empty lets Renovate update
# untrusted, at the cost of not auto-`git init`-ing on the initial copy (the
# after-copy message tells the user to run `git init`).

_message_before_copy: >-
  Pick a preset, then press Enter through the toggles to accept its defaults, or
  tune any of them. Every toggle is still shown and saved regardless of preset.

_message_after_copy: >-
  Project {{ github_repo_name }} scaffolded. Next steps:
  (1) git init && git add -A && git commit -m "chore: initial commit"
  (2) uv sync
  (3) complete the one-time repository setup documented in CONTRIBUTING.md
  (squash-merge policy, workflow permissions, PyPI trusted publishing).

# ── ① Identity ──────────────────────────────────────────────────────────────
github_user:
  type: str
  help: The GitHub username
github_repo_name:
  type: str  # Used verbatim as the importable Python package name.
  help: An awesome project needs an awesome name. Tell me yours.
  validator: >-
    {% if not (github_repo_name | regex_search('^[a-z][a-z0-9_]*$')) %} github_repo_name must be a valid Python package name: lowercase, start with a letter, and contain only letters, digits, and underscores. It is used verbatim as the package/import name (src/<name>/, `from <name> import ...`) and the project name, so dashes are not allowed. {% elif github_repo_name in ["and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"] %} github_repo_name cannot be the Python reserved keyword "{{ github_repo_name }}" — it is used verbatim as the import package name, so `from {{ github_repo_name }} import ...` would be a SyntaxError. Choose a different name. {% endif %}
author_full_name:
  type: str
  help: The full name of the author
author_given_names:
  type: str
  default: "{{ author_full_name.split(' ')[:-1] | join(' ') }}"
  help: >-
    The author's given (first) names, used in CITATION.cff. Defaults to a best-effort split of the full name — correct it here for compound surnames or "Last, First" ordering.
author_family_names:
  type: str
  default: "{{ author_full_name.split(' ')[-1] }}"
  help: The author's family (last) name, used in CITATION.cff.
author_email:
  type: str
  help: The email of the author
short_description:
  type: str
  default: A Python project template.
  help: A short description of the project
package_keywords:
  type: str
  default: ""
  help: >-
    Extra PyPI keywords specific to your project (comma-separated, e.g. "data, async, etl"). Tooling and component keywords are added automatically.

# ── ② Preset ────────────────────────────────────────────────────────────────
preset:
  type: str
  default: custom
  choices:
    "Minimal — core only (library)": minimal
    "Standard — CLI + config (recommended)": standard
    "Full — every component & integration": full
    "Custom — choose each toggle": custom
  help: >-
    Pick a starting point. Every toggle below is still shown and saved; the preset just chooses smart defaults you can accept by pressing Enter.
preset_map:
  type: yaml
  when: false
  default:
    minimal: []
    standard:
      - include_cli
      - include_pydantic_settings
    full:
      - include_cli
      - include_web
      - include_gui
      - include_tui
      - include_mcp
      - include_worker
      - include_c_extensions
      - include_profiling
      - include_examples
      - include_launcher
      - include_compiler
      - include_freezer
      - include_pydantic_settings
      - include_sourcery
      - include_sonarcloud
      - include_all_contributors
      - include_megalinter
      - include_postgres
      - include_pgadmin
      - include_adminer
      - include_redis
      - include_dbeaver
      - include_vpn
    custom:
      - include_cli
      - include_web
      - include_gui
      - include_tui
      - include_pydantic_settings

# ── ③ Interfaces ────────────────────────────────────────────────────────────
include_cli:
  type: bool
  default: "{{ 'include_cli' in preset_map[preset] }}"
  help: "Include CLI (Command Line Interface) using Typer?"
include_web:
  type: bool
  default: "{{ 'include_web' in preset_map[preset] }}"
  help: "Include Web API?"
web_framework:
  type: str
  default: fastapi
  choices:
    - fastapi
    - litestar
  when: "{{ include_web }}"
  help: "Choose the web framework to use"
include_gui:
  type: bool
  default: "{{ 'include_gui' in preset_map[preset] }}"
  help: "Include GUI (Graphical User Interface) using Tkinter?"
include_tui:
  type: bool
  default: "{{ 'include_tui' in preset_map[preset] }}"
  help: "Include TUI (Terminal User Interface) using Textual?"
include_mcp:
  type: bool
  default: "{{ 'include_mcp' in preset_map[preset] }}"
  help: "Include MCP (Model Context Protocol) server support?"
include_worker:
  type: bool
  default: "{{ 'include_worker' in preset_map[preset] }}"
  help: "Include message queue worker using FastStream?"
worker_broker:
  type: str
  default: kafka
  choices:
    - kafka
    - nats
    - rabbitmq
    - redis
  when: "{{ include_worker }}"
  help: "Choose the message broker to use"

# ── ④ Packaging / build ─────────────────────────────────────────────────────
include_c_extensions:
  type: bool
  default: "{{ 'include_c_extensions' in preset_map[preset] }}"
  help: "Include C extensions support using Cython?"
include_profiling:
  type: bool
  default: "{{ 'include_profiling' in preset_map[preset] }}"
  help: "Include profiling and performance tools (py-spy, scalene, cProfile)?"
include_launcher:
  type: bool
  default: "{{ 'include_launcher' in preset_map[preset] }}"
  help: "Include a uv-bootstrap launcher (PyCrucible) for a small online-first-run executable?"
include_compiler:
  type: bool
  default: "{{ 'include_compiler' in preset_map[preset] }}"
  help: "Include a compiler (Nuitka) to build a compiled native executable?"
include_freezer:
  type: bool
  default: "{{ 'include_freezer' in preset_map[preset] }}"
  help: "Include an offline freezer (PyInstaller) for a self-contained bundled executable?"
include_examples:
  type: bool
  default: "{{ 'include_examples' in preset_map[preset] }}"
  help: "Include an examples/ folder with simple and advanced usage stubs?"

# ── ⑤ Config ────────────────────────────────────────────────────────────────
include_pydantic_settings:
  type: bool
  default: "{{ 'include_pydantic_settings' in preset_map[preset] }}"
  help: "Use pydantic-settings for type-safe configuration management?"

# ── ⑥ Quality add-ons (opt-in, may need external accounts) ──────────────────
include_sourcery:
  type: bool
  default: "{{ 'include_sourcery' in preset_map[preset] }}"
  help: >-
    Include a Sourcery config (.sourcery.yaml) for AI refactoring suggestions? Requires installing the Sourcery GitHub App on the repository.
include_sonarcloud:
  type: bool
  default: "{{ 'include_sonarcloud' in preset_map[preset] }}"
  help: >-
    Include SonarCloud static analysis (sonar-project.properties + a CI job)? Requires a SonarCloud organization and a SONAR_TOKEN repository secret.
include_all_contributors:
  type: bool
  default: "{{ 'include_all_contributors' in preset_map[preset] }}"
  help: >-
    Include an all-contributors config (.all-contributorsrc) and a README section? Requires the all-contributors bot/CLI to maintain the list.
include_megalinter:
  type: bool
  default: "{{ 'include_megalinter' in preset_map[preset] }}"
  help: >-
    Add MegaLinter as an optional extra CI quality layer? It runs only linters that prek/tox do not already cover (shellcheck, hadolint, jsonlint, jscpd clone-detection, and a .md-scoped cspell prose pass) and uploads SARIF findings to the Security tab. Off by default so the fast, self-contained default is preserved (tox/prek remain the canonical runners).

# ── ⑦ Devcontainer services ─────────────────────────────────────────────────
include_postgres:
  type: bool
  default: "{{ 'include_postgres' in preset_map[preset] }}"
  help: "Include PostgreSQL database service in devcontainer?"
include_pgadmin:
  type: bool
  default: "{{ 'include_pgadmin' in preset_map[preset] }}"
  when: "{{ include_postgres }}"
  help: "Include pgAdmin for PostgreSQL management (gated behind 'tools' compose profile)?"
include_adminer:
  type: bool
  default: "{{ 'include_adminer' in preset_map[preset] }}"
  when: "{{ include_postgres }}"
  help: "Include Adminer for database management (gated behind 'tools' compose profile)?"
include_redis:
  type: bool
  default: "{{ 'include_redis' in preset_map[preset] }}"
  help: "Include Redis/Valkey cache service in devcontainer?"
redis_backend:
  type: str
  default: redis
  choices:
    - redis
    - valkey
  when: "{{ include_redis or (include_worker and worker_broker == 'redis') }}"
  help: "Choose the Redis-compatible backend image (redis or valkey)"
include_dbeaver:
  type: bool
  default: "{{ 'include_dbeaver' in preset_map[preset] }}"
  help: "Include DBeaver CloudBeaver for database management (gated behind 'tools' compose profile)?"
include_vpn:
  type: bool
  default: "{{ 'include_vpn' in preset_map[preset] }}"
  help: "Include OpenVPN client in devcontainer?"
```

- [ ] **Step 2: Add `preset: custom` to `.example-input.yml`**

Insert a `preset: custom` line after the `package_keywords:` line in `.example-input.yml` (all existing toggle lines stay; they override the preset defaults explicitly). Do not remove any existing key.

- [ ] **Step 3: Verify Copier still parses the questionnaire**

Run:
```bash
uv run copier copy --data-file .example-input.yml --defaults --force . /tmp/copier-after
```
Expected: renders successfully (exit 0), no Jinja/YAML error. If it errors on `preset_map[preset]` or the bool defaults, the `type: yaml` computed-var or the `{{ ... in ... }}` default expression is wrong — fix before continuing.

- [ ] **Step 4: Assert byte-identical output vs the baseline (the equivalence test)**

Run:
```bash
cd /tmp/copier-after && find . -type f -not -path './.git/*' | sort | xargs shasum > /tmp/copier-after.sha && cd -
diff /tmp/copier-baseline.sha /tmp/copier-after.sha && echo "IDENTICAL"
```
Expected: `diff` prints nothing and `IDENTICAL` is echoed. Any difference means the `custom` default-set diverged from today's defaults — reconcile the `custom:` list in `preset_map` until identical.

- [ ] **Step 5: Assert `preset` is stored and `preset_map` is NOT**

Run:
```bash
grep -E '^preset:' /tmp/copier-after/.copier-answers.yml && echo "preset stored OK"
! grep -q 'preset_map' /tmp/copier-after/.copier-answers.yml && echo "preset_map absent OK"
```
Expected: both `preset stored OK` and `preset_map absent OK` print.

- [ ] **Step 6: Commit**

```bash
git add copier.yml .example-input.yml
git commit -m "feat: add preset question and grouped ordering to copier.yml"
```

---

### Task 3: Verify presets and the `redis_backend` chaining fix produce correct projects

Prove the presets actually toggle the right components and that a redis-broker worker can now choose the valkey image.

**Files:** none modified (verification only; scratch renders under `/tmp`).

- [ ] **Step 1: Render each preset non-interactively**

Render each preset letting it drive the defaults — pass only identity data, NOT the toggle overrides from `.example-input.yml`:
```bash
for p in minimal standard full; do
  rm -rf /tmp/preset-$p
  uv run copier copy --defaults --force \
    --data github_user=hasansezertasan \
    --data github_repo_name=example \
    --data author_full_name="Hasan Sezer" \
    --data author_email=x@example.com \
    --data preset=$p \
    --trust . /tmp/preset-$p
done
```
Expected: three projects render (exit 0 each).

- [ ] **Step 2: Assert the component set per preset**

Run:
```bash
# minimal: no cli
test ! -d /tmp/preset-minimal/src/example/cli && echo "minimal: cli absent OK"
# standard: cli present, web absent
test -d /tmp/preset-standard/src/example/cli && echo "standard: cli present OK"
test ! -d /tmp/preset-standard/src/example/web && echo "standard: web absent OK"
# full: web + worker + mcp present
test -d /tmp/preset-full/src/example/web && \
test -d /tmp/preset-full/src/example/worker && \
test -d /tmp/preset-full/src/example/mcp && echo "full: components present OK"
```
Expected: all four `... OK` lines print.

- [ ] **Step 3: Assert the `redis_backend` chaining fix**

A redis-broker worker with `include_redis=false` must now honor `redis_backend=valkey` in the devcontainer compose (previously the value could not be supplied):
```bash
rm -rf /tmp/redis-broker
uv run copier copy --defaults --force \
  --data github_user=hasansezertasan --data github_repo_name=example \
  --data author_full_name="Hasan Sezer" --data author_email=x@example.com \
  --data preset=custom \
  --data include_worker=true --data worker_broker=redis \
  --data include_redis=false --data redis_backend=valkey \
  --trust . /tmp/redis-broker
grep -q 'valkey' /tmp/redis-broker/.devcontainer/docker-compose.yml && echo "redis_backend=valkey honored OK"
```
Expected: `redis_backend=valkey honored OK` prints. (If the compose file path differs, locate it with `find /tmp/redis-broker/.devcontainer -name 'docker-compose.yml*'`.)

- [ ] **Step 4: Run the generated `standard` project's style + tests**

Verify a preset-generated project is actually green:
```bash
cd /tmp/preset-standard && git init -q && git add -A && \
  uv run --locked tox run -e style && uv run --locked tox run -e 3.14 ; cd -
```
Expected: style env and the 3.14 test env both pass (coverage `fail_under=99` gate green). No commit in this task.

---

### Task 4: Document the preset in `README.md` and `CLAUDE.md`

**Files:**
- Modify: `README.md` (template-usage / options section)
- Modify: `CLAUDE.md` (the "Template Variables (copier.yml)" section)

- [ ] **Step 1: Locate the options docs**

Run:
```bash
grep -n "include_cli" README.md | head -3
grep -n "Template Variables (copier.yml)" CLAUDE.md
```
Expected: line numbers for where component options are listed in each file.

- [ ] **Step 2: Add a `preset` subsection to `README.md`**

Immediately before where the individual `include_*` options are documented, add:
```markdown
### Preset

The first component question, `preset`, seeds sensible defaults for everything
below it:

- `minimal` — core only (a plain library).
- `standard` — CLI + pydantic-settings (recommended starting point).
- `full` — every component and integration enabled.
- `custom` — the historical defaults (CLI, web, GUI, TUI, pydantic-settings);
  choose each toggle yourself.

Every toggle is still shown and written to `.copier-answers.yml`, so the preset
only changes the *default* you can accept with Enter — it never hides a question
and never changes an existing project on `copier update`.
```

- [ ] **Step 3: Add a `preset` bullet to `CLAUDE.md`**

Under "Template Variables (copier.yml)", above "Optional components (all boolean)", add:
```markdown
Starting point:

- `preset` - `minimal`/`standard`/`full`/`custom`. Seeds the default of every
  `include_*` toggle via the hidden `preset_map` computed variable (`when: false`,
  never stored). `default: custom`, whose set equals the historical defaults, so
  `--defaults` output is byte-identical to before and existing projects are
  unaffected on update. Toggles remain asked and stored — the preset only changes
  defaults.
```

- [ ] **Step 4: Verify the docs render/lint clean**

Run:
```bash
uv run prek run --files README.md CLAUDE.md
```
Expected: markdownlint/typos hooks pass (or auto-fix and re-stage). Re-run until clean.

- [ ] **Step 5: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "docs: document the copier preset question"
```

---

## Self-Review

**Spec coverage:**
- §1 `preset` question → Task 2 Step 1. ✓
- §2 `preset_map` + uniform defaults → Task 2 Step 1. ✓
- §3 grouping/reorder → Task 2 Step 1 (grouped with header comments). ✓
- §4 `redis_backend` `when:` fix → Task 2 Step 1 + Task 3 Step 3; no-new-validators decision → reflected (only the existing `github_repo_name` validator kept). ✓
- §5 before/after messages → Task 2 Step 1. ✓
- Backward-compat verification (§"verification") → Task 1 + Task 2 Steps 4–5. ✓
- `.example-input.yml` `preset: custom` → Task 2 Step 2. ✓
- Docs (README/CLAUDE) → Task 4. ✓

**Placeholder scan:** No TBD/TODO; full `copier.yml` content is inline; all verification commands are concrete. ✓

**Type consistency:** `preset` values `minimal|standard|full|custom` used identically in `preset_map` keys, `choices`, and Task 3 renders. `preset_map[preset]` membership test `'<name>' in preset_map[preset]` uses the exact `include_*` names present as questions. `redis_backend` `when:` guards `worker_broker` behind `include_worker` (which gates the `worker_broker` question), avoiding an undefined reference. ✓
