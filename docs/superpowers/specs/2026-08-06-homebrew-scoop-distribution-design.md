# Design: opt-in Homebrew tap + Scoop bucket distribution

- **Issue:** [#146](https://github.com/hasansezertasan/copier-pyproject/issues/146)
- **Branch:** `feat-opt-in-homebrew-tap-scoop-bucket-distributi`
- **Date:** 2026-08-06
- **Status:** Approved — ready for implementation planning
- **ADR:** ADR-017 (to be authored in Pass 1)

## Problem

PR #145 shipped `uv tool install` / `pipx` / `uvx` install docs for application
configs — these work the instant a project reaches PyPI, which the template
already scaffolds. Homebrew (`brew install <user>/tap/<pkg>`) and Scoop
(`scoop install <pkg>`) are a different class: they need publishing
infrastructure the template does **not** ship. Documenting them today would
point users at taps/buckets that do not exist (rejected in #145 for exactly this
reason). This feature adds the full capability — automation + docs — behind
opt-in toggles, preserving the self-contained "green on first push, zero
external accounts" default.

## Locked decisions

| Decision | Choice |
| --- | --- |
| Toggles | Two **independent** booleans `include_homebrew`, `include_scoop`, `default: false`, ADR-009 opt-in posture |
| Payload | **Binary when an executable toggle is enabled; PyPI/virtualenv fallback otherwise** |
| Publish mechanism | Render formula/manifest + `peter-evans/create-pull-request` to the cross-repo tap/bucket (mirrors `all-contributors.yml`) |
| Workflow location | Jobs **inside `release.yml`**, `needs: finalize-release` — NOT a `release: published` workflow |
| Cross-repo auth | A documented PAT secret; gated-on-secret, non-blocking (SonarCloud/Codecov pattern) |
| Tap/bucket bootstrap | Documented **one-time manual** repo creation + PAT secret |
| Sequencing | Document-Driven: Pass 1 = docs/ADR/toggles; Pass 2 = automation |

### Why the publish jobs live inside `release.yml`

`finalize-release` un-drafts the GitHub Release using `GITHUB_TOKEN`. An event
fired by `GITHUB_TOKEN` cannot trigger another workflow (GitHub's loop-prevention
rule) — the same constraint that forces `deploy-docs` and
`notify-released-issues` to live inside `release.yml` rather than react to
`release: published`. The brew/scoop publish jobs therefore must be jobs in
`release.yml` that `needs: finalize-release` (so the release is published and its
assets attached before we read their sha256s).

### Why a cross-repo PAT (not `GITHUB_TOKEN`)

`all-contributors.yml` pushes to the **same** repo, so `GITHUB_TOKEN` suffices.
Here the PR targets a **separate** `homebrew-<name>` / `scoop-<name>` repo, which
`GITHUB_TOKEN` cannot write. A fine-grained PAT (contents + pull-requests write
on the tap/bucket repos) is required, supplied as a repository secret. Because
the `secrets` context is unavailable in `if:`, gating uses a job-env presence
flag: `HOMEBREW_TAP_TOKEN_SET: ${{ secrets.HOMEBREW_TAP_TOKEN != '' }}`, and the
publish step `if:`s on that flag, emitting a visible `::notice::` skip when unset
so a missing secret never fails the release.

## `copier.yml` changes

### New toggles

```yaml
include_homebrew:
  type: bool
  default: "{{ 'include_homebrew' in preset_map[preset] }}"
  when: "{{ is_app }}"
  help: >-
    Include a Homebrew tap formula published on each release? Requires a
    homebrew-<name> repo and a HOMEBREW_TAP_TOKEN secret (one-time setup,
    documented in CONTRIBUTING.md).

include_scoop:
  type: bool
  default: "{{ 'include_scoop' in preset_map[preset] }}"
  when: "{{ is_app }}"
  help: >-
    Include a Scoop bucket manifest published on each release? Requires a
    scoop-<name> repo and a SCOOP_BUCKET_TOKEN secret (one-time setup,
    documented in CONTRIBUTING.md).
```

- **`when: "{{ is_app }}"`** — a formula/manifest is meaningless for a library,
  so the questions only surface for runnable configs (same `when:`-gating idiom
  as `worker_broker`/`web_framework`). When `is_app` is false the toggle is not
  asked and defaults false.
- Both added to the `full` entry of `preset_map`.

### New computed variable `primary_executable`

```yaml
primary_executable:
  type: str
  when: false
  default: "{% if include_freezer %}freezer{% elif include_compiler %}compiler{% elif include_launcher %}launcher{% endif %}"
```

- Single source of truth for **which** prebuilt binary the formula/manifest
  reference when several executable toggles are enabled.
- Precedence **`freezer` > `compiler` > `launcher`**: freezer and compiler are
  fully self-contained; launcher downloads Python + deps on first run (needs
  network), so it is last.
- Empty string ⇒ no executable toggle enabled ⇒ the formula/manifest render the
  **PyPI/virtualenv fallback** path.
- Follows the naming convention learned earlier: hidden `when: false` question
  names must **not** start with `_`, or Copier renders them empty.

## Formula / manifest templates

Committed to the generated repo under `template/.github/packaging/`, each file
Jinja-conditional on its toggle. They carry **runtime placeholders** the release
job substitutes (distinct from Jinja `{{ }}` so the two templating layers never
collide): `@@VERSION@@`, `@@URL_MACOS@@`, `@@SHA256_MACOS@@`, `@@URL_LINUX@@`,
`@@SHA256_LINUX@@`, `@@URL_WIN@@`, `@@SHA256_WIN@@`, `@@SDIST_URL@@`,
`@@SDIST_SHA256@@`.

### `homebrew-formula.rb.tmpl`

- **Binary path** (`primary_executable` non-empty): `on_macos` / `on_linux`
  blocks referencing the release asset URLs for the primary executable
  (`<pkg>-<primary_executable>-macos` / `-linux`) + their sha256, then
  `bin.install ... => "<pkg>"`.
- **PyPI path** (`primary_executable` empty): `depends_on "python@3.x"`, create a
  virtualenv under `libexec`, `pip install <pkg>==@@VERSION@@` from PyPI. No
  pinned `resource` blocks — auto-generating resource hashes has no maintained
  tooling (`homebrew-pypi-poet` is dead). Personal-tap style, not
  homebrew-core-acceptable (documented as such in the ADR).

### `scoop-manifest.json.tmpl`

- **Binary path**: `architecture.64bit.url` → the windows `.exe`
  (`<pkg>-<primary_executable>-windows.exe`) + hash, `bin` entry naming the
  executable `<pkg>`.
- **PyPI fallback**: `depends_on: "python"` + a pip-install install script.
  Best-effort — Scoop is fundamentally a binary package manager; this corner is
  documented as a known limitation, not hidden.

## `release.yml` publish jobs (Pass 2)

`publish-homebrew` and `publish-scoop`, each:

- `if:` Jinja-gated on `include_homebrew` / `include_scoop`.
- `needs: [release-please, finalize-release]` (release published + assets
  attached first).
- `permissions: contents: read`; `timeout-minutes` set; checkout with
  `persist-credentials: false`; all actions SHA-pinned with `# vX` comments and
  `{% raw %}`-wrapped `${{ }}`.
- Job-env presence flag `HOMEBREW_TAP_TOKEN_SET` / `SCOOP_BUCKET_TOKEN_SET`; the
  render+PR step `if:`s on it and emits a `::notice::` skip when unset.
- Steps: resolve the tag/version, download or read the release assets, compute
  sha256 (binary path) or fetch the PyPI sdist sha256 (fallback), substitute the
  `@@...@@` placeholders into the committed `.tmpl`, then
  `peter-evans/create-pull-request` to `<user>/homebrew-<name>` (resp.
  `scoop-<name>`) with `token: ${{ secrets.HOMEBREW_TAP_TOKEN }}`,
  `base: <default branch>`, `branch: chore/<pkg>-<version>`, `delete-branch:
  true`.
- GitHub context (`TAG_NAME`, `REPO`, tokens) passed via `env:` and read as
  `"$VAR"` in `run:` blocks — no untrusted interpolation (zizmor
  template-injection rule).

### ghalint exception

These jobs expose the token/presence flag at job-env (required because `if:`
cannot read the `secrets` context). ghalint's `job_secrets` policy flags that, so
the web-only `.github/ghalint.yaml` `job_secrets` exclusion is extended to
`publish-homebrew` / `publish-scoop`, Jinja-gated on the toggles — the same
exception already granted to `docker-publish`.

## Docs (Pass 1)

- **`docs/adr/017-opt-in-homebrew-scoop-distribution.md`** — new ADR framed off
  ADR-009. Records: the binary-vs-PyPI payload decision; cross-repo-PAT +
  gated-on-secret posture; why the jobs live in `release.yml`; and the two known
  limitations (single-arch binaries, best-effort Scoop PyPI fallback).
- **`template/README.md.jinja`** — `brew install <user>/tap/<pkg>` and
  `scoop install <pkg>` lines, each behind its toggle, inside the existing
  `{% if is_app %}` app-install block.
- **`template/docs/installation.rst.jinja`** — matching `brew`/`scoop`
  `.. code-block:: sh` sections, toggle-gated, alongside the `uv tool install` /
  `pipx` / `uvx` blocks.
- **`template/.../CONTRIBUTING.md.jinja`** — "Repository setup" gains the
  one-time steps: `gh repo create <user>/homebrew-<name> --public` (resp.
  `scoop-<name>`) and adding the `HOMEBREW_TAP_TOKEN` / `SCOOP_BUCKET_TOKEN`
  fine-grained PAT secret — mirroring the existing PyPI trusted-publishing and
  release-please setup steps.
- **root `CLAUDE.md`** — add `include_homebrew` / `include_scoop` to the
  "Optional components" list and note the `primary_executable` precedence.
- `.example-input.yml` unchanged (library preset; both toggles default false and
  are `when: is_app`-gated anyway).

## Known limitations (documented in ADR-017)

1. **Single-arch binaries.** The release matrix builds one binary per OS
   (ubuntu/windows/macos runners), not per-arch (arm64 + x64). The formula is
   therefore single-arch per platform — it matches exactly what the template
   builds. Multi-arch is a future enhancement gated on the release matrix
   growing arch dimensions.
2. **Scoop PyPI fallback is best-effort.** Scoop is a binary package manager;
   installing a pure-Python package via a pip shim works but is non-idiomatic.
   The recommended Scoop configuration pairs `include_scoop` with an executable
   toggle. The fallback is kept (not a hard requirement) with a documented
   caveat.

## Verification plan

Regenerate representative combinations and confirm each renders + lints clean:

- `preset=full` (both toggles + all executable toggles on) — binary path, primary
  executable = freezer.
- `include_cli=true include_homebrew=true` with **no** executable toggle — PyPI
  fallback path.
- `include_cli=true include_scoop=true include_compiler=true` — Scoop binary
  path.
- `preset=library` (default) — neither toggle asked/rendered (`when: is_app`
  false); confirm zero brew/scoop artifacts.

For each app combination: `git init` the generated project, then
`uv run --locked tox run -e style`, `prek run zizmor --all-files`, and a render
sanity check that the formula (`ruby -c` if available), the manifest (`jq .`),
and the `release.yml` publish jobs are syntactically valid and ghalint-green.

## Out of scope

- Multi-arch (arm64 + x64) binary formulae — future, gated on the release matrix.
- Publishing to `homebrew-core` / the official Scoop `main` bucket (personal
  tap/bucket only).
- Auto-creating the tap/bucket repo (explicitly chose documented manual
  creation).
