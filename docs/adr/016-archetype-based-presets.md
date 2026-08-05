# ADR-016: Archetype-based presets

## Status

Proposed (2026-08). Supersedes the preset design introduced in
[#141](https://github.com/hasansezertasan/copier-pyproject/pull/141) (which
shipped without an ADR). That change added a `preset` question with the choices
`minimal` / `standard` / `full` / `custom`; this ADR reshapes those choices.

## Context

[#141] added a `preset` question to `copier.yml` that seeds the defaults of every
`include_*` toggle via a hidden `preset_map` (`when: false`) computed variable.
The mechanism is sound and is kept: the preset **only changes defaults** — every
toggle is still asked and stored, and dependency-gated sub-questions
(`web_framework`, `worker_broker`, the DB UIs, `redis_backend`) still appear only
when their parent toggle is enabled. Nothing is hidden.

The **choice set**, however, was a "how much tooling" ladder:

| Preset | Seeds |
| --- | --- |
| `minimal` | (nothing) |
| `standard` | `cli`, `pydantic_settings` |
| `full` | everything |
| `custom` (default) | `cli`, `web`, `gui`, `tui`, `pydantic_settings` |

That ladder answers *"how much do I want?"* — but that is not how projects are
actually conceived. A template user thinks in **shapes**: "this is a library,"
"this is a CLI/TUI tool I'll ship on PyPI," "this is a web app." The old choices
mapped poorly onto those shapes:

- `standard` was really "CLI-lite" wearing a size-ladder name.
- Nothing corresponded to a **library** as a first-class starting point (only the
  unnamed, easily-overlooked `minimal`).
- `custom` existed *only* to preserve a byte-identical `--defaults` output when
  presets were first introduced — it was not a shape anyone chooses. In an
  archetype model it is doubly redundant: **every** preset already lets you tune
  every toggle, so a preset literally named "choose each toggle" carries no
  meaning.

The template's own maintainer builds three recurring shapes — **libraries**,
**CLI/TUI tools** (distributed via PyPI, occasionally frozen with
PyInstaller/Nuitka), and **web apps** — which sometimes overlap. Because presets
set defaults rather than lock choices, overlap is a non-issue: pick the nearest
shape, then flip the one or two toggles that differ.

## Decision

Replace the size ladder with **archetype presets** that name project shapes.

### New choice set

| Preset | Seeds ON | Shape |
| --- | --- | --- |
| **`library`** *(default)* | `examples` | Pure importable package. Examples stubs help consumers; no interface and no config framework imposed on downstream users. |
| **`tool`** | `cli`, `tui`, `pydantic_settings` | A PyPI-distributed CLI/TUI tool — the maintainer's most common shape. |
| **`web`** | `web` (→ `fastapi`), `pydantic_settings`, `postgres`, `redis` | A web app with a database + cache in the devcontainer. |
| **`full`** | everything | Unchanged — the kitchen-sink smoke test. |

`minimal` → folded into `library` (+`examples`). `standard` → sharpened into
`tool`. `custom` → **removed** (redundant, see Context).

### `tool` is PyPI-first — no standalone-executable seed

The maintainer ships tools *mostly* via PyPI and only *sometimes* freezes them.
So `tool` seeds **none** of the standalone-executable toggles (`launcher` /
`compiler` / `freezer`, per [ADR-007](007-standalone-executable-toggles.md)). The
occasional frozen build is one deliberate toggle flip, not a default the majority
of tools would have to turn back off. `profiling`, `examples`, `mcp`, and
`worker` are likewise left off for `tool` to keep it lean.

### `web` is lean — no worker/mcp/DB-UI seed

`web` seeds only `postgres` + `redis` (a realistic dev stack) plus the web app and
config. It does **not** seed `worker`, `mcp`, or the DB UIs (`pgadmin` /
`adminer` / `dbeaver`) — those remain asked (like all toggles) and off by
default. `web_framework` is asked as usual once `include_web` is on
(default `fastapi`).

### Default preset is `library`

With `custom` gone, a new default is required (it drives bare `--defaults` and
non-interactive runs). `library` is chosen as the **smallest, most conservative
surface** — a pure package — so an unattended run produces the least, not the
most. This is a deliberate change from the previous `custom` default.

## Consequences

- **`copier.yml`**: rewrite the `preset` question `choices` (new labels + values,
  `default: library`) and the `preset_map` computed variable to the four-entry
  map above. No change to the per-toggle
  `default: "{{ '<toggle>' in preset_map[preset] }}"` wiring.
- **`--defaults` output changes.** It was the `custom` set
  (`cli`+`web`+`gui`+`tui`+`pydantic_settings`); it is now the `library` set
  (`examples` only). This **intentionally breaks** the byte-identical-`--defaults`
  guarantee that motivated `custom` in [#141]. That guarantee was only ever a
  migration cushion for presets' introduction; reshaping the presets is a
  deliberate, breaking-by-design change to the *defaults*, not to any generated
  file's contents.
- **`copier update` on existing projects is safe.** A project's
  `.copier-answers.yml` stores every `include_*` value **explicitly**, and those
  stored answers — not the preset — drive rendering. A project that stored
  `preset: minimal` / `standard` / `custom` will re-prompt the `preset` question
  once on its next update (the stored value is no longer a valid choice), but
  selecting any preset leaves the rendered output unchanged. Cosmetic, one-time,
  low-blast-radius (presets shipped only days earlier in [#141], so few or no
  downstream projects have adopted them yet).
- **`.example-input.yml` is shrunk to identity + preset.** The per-toggle
  `include_*: false` lines are removed; the file now carries only the five
  no-default identity answers (`github_user`, `github_repo_name`,
  `author_full_name`, `author_email`, `short_description`) plus `preset: library`.
  This deletes the recurring maintenance step "update `.example-input.yml` when a
  new toggle is added" (previously CLAUDE.md's Adding-New-Optional-Components step
  6) — the file becomes stable and no longer tracks the toggle list. The file is
  **kept**, not removed: the five identity fields have no defaults, so
  non-interactive generation (`mise run example`, the `template-ci.yml` render
  job) needs a data source, and giving identity defaults would be a footgun
  (bare `--defaults` would otherwise emit a project literally named `example`
  owned by `octocat`). The automated render harness (`tests/conftest.py`) is
  unaffected — it already supplies its own `IDENTITY` dict via Copier's Python
  API and never read `.example-input.yml`.
- **`example/` (via `mise run example`)** now renders the `library` preset
  (`examples/` present) instead of the former everything-off tree — a more
  representative manual smoke-test example.
- **`.github/workflows/template-ci.yml`**: the render job's additive matrix
  (base data-file + per-scenario `--data include_X=true`) assumed an
  everything-off baseline. With the base now seeding the `library` floor,
  `examples/` is present in every scenario — inert (it only adds usage-stub
  files, which lint/build cleanly) and each scenario still isolates its target
  toggle. To preserve the **`minimal` scenario's** documented "bare, core/utils
  only" purpose, add `--data include_examples=false` to that one scenario so it
  stays a true core-only render. No other scenario changes.
- **`README.md`**: the line "`.example-input.yml` provides default values for all
  template options" is no longer accurate — update it to describe the file as
  identity answers + a starting preset.
- **Docs**: update the preset documentation added in [#141] — the `copier.yml`
  `preset` `help`, `_message_before_copy`, `CLAUDE.md` (the "Starting point"
  section), and the `README` preset table — to describe the archetype set and the
  new default.
- **Render test harness**: update the preset assertions in the `test_presets`
  harness added in [#141] to the new choice set and per-archetype toggle
  expectations.
- No `pyproject.toml`, component, or generated-source change: this ADR only
  reshapes which defaults a preset seeds.

## Notes / follow-up

- The archetype set is intentionally small (three shapes + `full`). If a distinct
  **service/worker** archetype (`worker` + broker + DB) proves common later, it
  can be added as a fifth choice without disturbing this design — the mechanism
  scales to any number of `preset_map` entries.
