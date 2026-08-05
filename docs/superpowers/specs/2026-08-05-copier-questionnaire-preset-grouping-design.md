# Design: Preset-driven, grouped Copier questionnaire

**Date:** 2026-08-05
**Status:** Approved (pending spec review)
**Scope:** `copier.yml` questionnaire UX only. No change to `template/` file
contents, stored answer *names*, or the generated project's behavior.

## Problem

The current `copier.yml` presents ~25 questions as a flat, unordered list. The
reported pain (all four confirmed by the maintainer):

1. **Too many / poorly ordered questions** — related questions (e.g. all
   devcontainer services) are not adjacent; the flow feels random.
2. **Missing conditional chaining** — some dependent sub-questions are asked or
   defaulted in ways that don't track their parent (see `redis_backend`).
3. **Bad defaults / invalid combos possible** — `include_cli/web/gui/tui` all
   default `true`, producing a heavy project by default.
4. **Confusing prompts / validation** — the meaning of a toggle and its
   downstream cost isn't clear at prompt time.

## Non-goals / constraints (decided during brainstorming)

- **Keep the `include_*` boolean schema.** No `multiselect` that would rename or
  restructure stored answers — that would break every `{% if include_x %}` in
  `template/` and every existing `.copier-answers.yml`.
- **Presets seed defaults only; every toggle stays asked and stored.** Copier
  does not persist skipped (`when:false`) questions, so gating toggles behind a
  preset would recompute them on every `copier update` and could silently change
  a downstream project's shape. Rejected. Therefore **the raw interactive prompt
  count is unchanged** — the improvement is faster Enter-through + logical order,
  not fewer prompts.
- **Byte-identical `--defaults` output.** Existing generated projects (updated
  non-interactively by Renovate's copier manager, ADR-015) must be unaffected.
- **No `_tasks`** (ADR-015) — must not reintroduce one.

## Design

### 1. `preset` question

Inserted immediately after the identity/author fields, before the component
toggles:

```yaml
preset:
  type: str
  default: custom
  choices:
    "Minimal — core only (library)":         minimal
    "Standard — CLI + config (recommended)":  standard
    "Full — every component & integration":   full
    "Custom — choose each toggle":            custom
  help: >-
    Pick a starting point. Every toggle below is still shown and saved; the
    preset just chooses smart defaults you can accept by pressing Enter.
```

- `default: custom`, and `custom`'s default-set (below) equals today's defaults,
  so a `copier copy --defaults` (no `preset` supplied) reproduces **byte-identical
  output to the current template**. This is the backward-compatibility guarantee.
- Existing projects have every `include_*` stored; Copier only applies a default
  when an answer is *absent*, so the `preset` default never overrides a stored
  toggle on `copier update`. `preset` is written into their answers file on the
  first update (harmless).
- `preset` is a normal stored question, so it lands in `.copier-answers.yml`.

### 2. `preset_map` helper (single source of preset logic)

```yaml
preset_map:
  type: json
  when: false            # hidden: never asked, never stored
  default:
    minimal:  []
    standard: [include_cli, include_pydantic_settings]
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
    custom:              # == current template defaults
      - include_cli
      - include_web
      - include_gui
      - include_tui
      - include_pydantic_settings
```

Every component toggle then uses one uniform default expression:

```yaml
include_web:
  type: bool
  default: "{{ 'include_web' in preset_map[preset] }}"
  help: "..."
```

- `preset_map` is `when: false`, so it is **not** written to `.copier-answers.yml`
  and is recomputed each run. That is correct here — it only *seeds defaults* of
  stored questions; it is never itself a stored answer, so recomputation cannot
  change a project's persisted shape.
- Choice sub-questions keep their own literal defaults unchanged
  (`web_framework: fastapi`, `worker_broker: kafka`, `redis_backend: redis`).
- Child toggles that are also `when:`-gated (`include_pgadmin`,
  `include_adminer`) still compute their default from `preset_map` but are only
  *asked* when their parent is on — e.g. under `full`, `postgres` is on so
  `pgadmin` is asked with default `true`.

### 3. Grouping / reordering

Copier has no native section UI; grouping = deliberate order (each dependent
question adjacent to its parent) plus short header phrases in `help`. Target
order:

```
① Identity        github_user → github_repo_name → author_full_name →
                  author_given_names → author_family_names → author_email →
                  short_description → package_keywords
② Preset          preset  (+ hidden preset_map)
③ Interfaces      include_cli → include_web →⟜web_framework → include_gui →
                  include_tui → include_mcp → include_worker →⟜worker_broker
④ Packaging/build include_c_extensions → include_profiling → include_launcher →
                  include_compiler → include_freezer → include_examples
⑤ Config          include_pydantic_settings
⑥ Quality add-ons include_sourcery → include_sonarcloud →
                  include_all_contributors → include_megalinter
⑦ Devcontainer    include_postgres →⟜include_pgadmin →⟜include_adminer →
                  include_redis →⟜redis_backend → include_dbeaver → include_vpn
```

`⟜` = child shown only when its parent is on. No stored answer *names* change, so
this reorder is backward-compatible.

### 4. Chaining fixes + validators

- **`redis_backend` chaining fix.** Today `when: "{{ include_redis }}"`, so a
  redis-broker worker (`include_worker` + `worker_broker == 'redis'`) with
  `include_redis == false` silently forces the default redis image and can't pick
  valkey. Widen to:

  ```yaml
  when: "{{ include_redis or (include_worker and worker_broker == 'redis') }}"
  ```

- **No new hard-blocking validators (deliberate).** Copier's `when:`-gating
  already prevents the only genuine dependency violations (`pgadmin`/`adminer`
  cannot be selected without `postgres`). The remaining "unusual" combos are all
  *valid*:
  - **Zero interfaces** = a pure library (exactly what `minimal` produces) — must
    stay allowed.
  - **`dbeaver` without a DB service** — CloudBeaver connects to arbitrary/external
    databases, so this is legitimate, not nonsense.

  Existing validators are unchanged (the `github_repo_name` package-name /
  reserved-keyword validator stays).

### 5. Guidance messages

- **`_message_before_copy`** — "Pick a preset, then press Enter through the
  toggles to accept its defaults, or tune any of them."
- **`_message_after_copy`** — post-scaffold checklist currently buried in docs:
  most importantly the **`git init`** reminder (ADR-015 removed `_tasks: git
  init`), then `uv sync`, then a pointer to the `CONTRIBUTING.md` repository-setup
  section. Rendered with Jinja so it can reference `{{ github_repo_name }}`.

## Backward-compatibility verification (part of the implementation plan)

1. Regenerate `example/` with `.example-input.yml --defaults --force` and `git
   diff` the result against the pre-change render — **must be empty** (identical),
   because `.example-input.yml` sets toggles explicitly and `preset` defaults to
   `custom` whose map equals today's defaults.
2. Add `preset: custom` to `.example-input.yml` for explicitness (no output
   change).
3. Render each preset (`--data preset=minimal|standard|full`) to a scratch dir and
   confirm the expected component set and that `tox -e style` + tests pass for at
   least `standard` and `full`.
4. Confirm `preset` appears and `preset_map` does **not** appear in a generated
   `.copier-answers.yml`.

## Files touched

- `copier.yml` — the entire change (new questions, reorder, default expressions,
  `redis_backend` `when:`, messages).
- `.example-input.yml` — add explicit `preset: custom`.
- `README.md` / `CLAUDE.md` — document the preset and the reordered flow.
- No files under `template/` change.

## Rejected alternatives

- **`multiselect` component questions** — collapses ~20 bool prompts into ~5, but
  renames the stored schema and breaks every `template/` conditional and every
  existing answers file. Rejected.
- **Skip toggles under non-custom presets (`when: preset == 'custom'`)** — real
  prompt reduction, but Copier doesn't store skipped answers, so updates could
  silently change project shape. Rejected in favor of "seed defaults only."
- **Inline per-toggle preset logic** (no `preset_map` helper) — 25 duplicated
  expressions; harder to keep the preset sets consistent. Rejected for the single
  helper var.
