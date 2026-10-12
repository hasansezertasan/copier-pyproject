# Presets

## Archetype presets name project shapes; library is the default

**Id:** a14ee38b-12ed-49c8-b452-12b330cf9d10
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-016 (`docs/adr/016-archetype-based-presets.md`); the preset mechanism it reshapes came from [PR #141](https://github.com/hasansezertasan/copier-pyproject/pull/141); ADR-025 and ADR-039 for the two toggles every preset seeds
**Revisit when:** a distinct service/worker archetype (worker + broker + database) proves common enough to be a fifth choice
**See:** standalone-executables.md#three-architecture-named-executable-toggles-instead-of-one-brand-toggle — d5aed1a0-0b7c-4ac3-9d75-fb9568d9e34d — as of 2026-10-11

The `preset` question offers `library` (default; seeds `examples`), `tool`
(`cli`, `tui`, `pydantic_settings`), `web` (`web` with FastAPI,
`pydantic_settings`, `postgres`, `redis`) and `full` (everything). Every preset
also seeds `docs` and `pypi_publish` on (ADR-025, ADR-039). A preset only
seeds toggle defaults through the hidden `preset_map`; every toggle is still
asked and stored. `tool` seeds none of the standalone-executable toggles, and
`web` seeds neither worker, MCP nor the database UIs.

**Reason:** the earlier `minimal`/`standard`/`full`/`custom` ladder answered
"how much tooling" while adopters think in shapes — a library, a PyPI-shipped
CLI/TUI tool, a web app. `standard` was CLI-lite under a size name, nothing
named the library shape, and `custom` existed only to keep `--defaults` output
byte-identical when presets were introduced — meaningless once every preset is
tunable. `library` is the default because an unattended run should produce the
smallest, most conservative surface. `tool` is PyPI-first because the
maintainer ships tools mostly via PyPI and freezes them only occasionally; one
deliberate flip beats a default most tools would turn back off.

**Rejected alternative:** keep `custom` as a migration cushion — presets had
shipped only days earlier, so the cushion protected almost nobody.

**Consequence:** bare `--defaults` output changed from the `custom` set to the
`library` set, intentionally. Stored `include_*` answers drive rendering, so
`copier update` on existing projects is unaffected apart from a one-time
re-prompt of the `preset` question when its stored value is no longer a valid
choice. The template-ci `minimal` scenario adds `include_examples=false` to
stay a true core-only render.

## The example input file holds identity answers and a preset only

**Id:** ef5a9b93-2be9-4b18-a354-4a6c174207fe
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-016 (`docs/adr/016-archetype-based-presets.md`)
**Revisit when:** the identity questions gain defaults, or non-interactive generation gets another data source

`.example-input.yml` carries only the no-default identity answers, the free-form
keywords and `preset: library`; the per-toggle `include_*: false` lines were
removed. The file is kept, not deleted.

**Reason:** removing the toggle list deletes the recurring maintenance step
"update the example input when a toggle is added", so the file becomes stable.
It stays because the identity fields have no defaults and giving them defaults
would be a footgun — a bare `--defaults` run would emit a project literally
named `example` owned by `octocat` — while non-interactive generation (the
example task, the CI render job) still needs a data source. The render harness
is unaffected; it supplies its own identity dictionary through Copier's API.

**Rejected alternative:** remove the file and give the identity questions
defaults — the footgun above.
