# Package distribution

## Homebrew and Scoop are opt-in dispatches; the tap or bucket owns the manifest logic

**Id:** 462ac46c-c9db-4a4a-b8ae-bbe5c14af09f
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-017 ([`docs/adr/017-opt-in-homebrew-scoop-distribution.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/017-opt-in-homebrew-scoop-distribution.md)); the live reference is the keycast tap and bucket repositories
**Revisit when:** the release build matrix becomes per-architecture, or an ecosystem's own bump tooling changes shape
**See:** external-integrations.md#a-freshly-generated-project-is-green-on-first-push-with-zero-external-accounts — 392b6dcf-6e9d-441d-bf7b-64ba362578d7 — as of 2026-10-11
**See:** package-distribution.md#optional-pypi-publishing — 20be7463-ca95-4d01-82c9-71f632d1b4be — as of 2026-10-11

`include_homebrew` and `include_scoop` are independent toggles, off by default
and asked only when the project can distribute natively. When enabled,
`release.yml` gains `bump-homebrew`/`bump-scoop` jobs that fire a
`repository_dispatch` at the owner's `homebrew-tap`/`scoop-bucket` repository
with only the package name and version. A listener workflow living in the tap
or bucket does the manifest work with each ecosystem's own tooling; the
generated project ships a reference listener and setup guide under
`docs/packaging/` as a copy-into-your-tap bundle, not code it runs. The jobs
are gated on a fine-grained PAT with Contents-write on the target repository
only, skip with a visible warning when the secret is unset, run with no
workflow permissions of their own, and never join the `check` gate.

**Reason:** generating a formula, cask or manifest in every producing project
duplicates sha256 computation, PyPI resource resolution, per-OS asset matching
and each ecosystem's audit rules — and their bugs — once per generated project.
Dispatching keeps that logic in one downstream place, written with the tools
the ecosystems maintain for exactly this job. The jobs live in `release.yml`
because a release event fired by the workflow token cannot trigger another
workflow. The listener opens its own PR with its own token, so the PAT needs no
pull-request scope.

**Rejected alternative:** render and push the formula/manifest from the
generated project — the original design of this record, replaced for the
duplication above.

**Rejected alternative:** one shared enum or parent toggle — an owner may want
one ecosystem only.

**Consequence:** binaries are single-architecture per OS; the Scoop PyPI
fallback is best-effort because Scoop's tooling assumes binary downloads; the
listener is not validated by this template's tests; payload validation is the
listener's job.

## `primary_executable` is the single source for the distribution payload

**Id:** 40888b40-730c-4575-b68c-401b4eeccc06
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-017 ([`docs/adr/017-opt-in-homebrew-scoop-distribution.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/017-opt-in-homebrew-scoop-distribution.md))
**Revisit when:** a fourth executable architecture is added, or the launcher stops needing network access on first run
**See:** standalone-executables.md#three-architecture-named-executable-toggles-instead-of-one-brand-toggle — d5aed1a0-0b7c-4ac3-9d75-fb9568d9e34d — as of 2026-10-11

A hidden computed variable picks `freezer` over `compiler` over `launcher`, or
is empty when no executable toggle is on. Non-empty means a Homebrew cask and a
Scoop binary manifest fed from the GitHub release; empty means a Homebrew
formula built from the PyPI sdist and a Scoop pipx manifest.

**Reason:** PyInstaller and Nuitka produce fully self-contained binaries; the
PyCrucible launcher still needs the network on first run, so it is the fallback
of last resort. One computed variable mirrors the role `primary_component`
plays for console-script precedence: no template re-spells the ordering
inline.

**Rejected alternative:** re-derive the ordering per template — the drift
`primary_component` already exists to prevent.

## Optional PyPI publishing

**Id:** 20be7463-ca95-4d01-82c9-71f632d1b4be
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [issue #382](https://github.com/hasansezertasan/copier-pyproject/issues/382); maintainer decisions while implementing it, 2026-10-11; ADR-039 ([`docs/adr/039-optional-pypi-publishing.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/039-optional-pypi-publishing.md))
**Revisit when:** the PyPI project name becomes its own question, or Homebrew / Scoop gain a non-PyPI source for a pure-Python package
**See:** release-automation.md#the-workflow_dispatch-trigger-on-releaseyml-stays-the-publish-environment-is-the-containment — 0d93a35d-46a3-4ac6-b072-fc07da789842 — as of 2026-10-11

`include_pypi_publish` is a boolean toggle, seeded **on** by every preset, so
existing projects and `copier update` keep publishing. When it is off:

- `release.yml` does not render `pypi-publish`, and drops it from the `needs`
  of `attach-github-release` and `finalize-release`. `build` still produces and
  attests the wheel and sdist, and `attach-github-release` still uploads them,
  so every release keeps its distributions.
- `build` keeps the `publish` environment. It mints build-provenance
  attestations there, and the environment's main-only deployment-branch policy
  is what stops a `workflow_dispatch` run from another branch. So the setup
  guide drops only the PyPI publisher registration. The "Restrict the `publish`
  environment to `main`" step stays.
- The README and `installation.rst` install from
  `git+https://github.com/<user>/<repo>` (`uv tool install`, `uvx --from`,
  `uv add`, `pip install`) and say the release assets carry the wheel and sdist.
  The README PyPI badges and its PyPI-based Analysis links are dropped. The
  PyPI publication-attestation text in `installation.rst` is dropped too, along
  with PyPI mentions in `CONTRIBUTING.md`, the `repo-setup` skill and the
  after-copy message.

**Homebrew and Scoop.** A Homebrew formula is built from the PyPI sdist, and
the Scoop pipx manifest polls PyPI. Only a prebuilt executable (a cask or binary
manifest) is fetched from the GitHub Release. A hidden `can_distribute_natively`
(`is_app` and either PyPI publishing or a `primary_executable`) therefore gates
`include_homebrew` and `include_scoop`. Without it they are not asked, and their
`default` repeats the guard, so a preset cannot turn on a tap or bucket that
could never update.

**Rejected alternative:** leave Homebrew/Scoop ungated and document the caveat.
Rejected: it renders a tap/bucket dispatch whose formula or manifest can never
resolve, which is a failure on first release that the template can prevent at
question time.

**Rejected alternative:** point the install docs at a GitHub Release wheel
download. Rejected in favor of Git URL installs, which work with every installer
the docs already show, can be pinned with `@<tag>`, and work over SSH for
private repositories.

**Rejected alternative:** make the PyPI project name its own question in this
change. Deferred as a separate concern: it decouples the distribution name from
the package name, which touches far more than the publish job.

**Consequence:** a project can release without PyPI, and that choice survives
`copier update`. An explicit `--data include_homebrew=true` still renders the
tap even when the question is gated off — Copier applies passed data to an
unasked question, the existing contract of the `is_app` gate too. The
template-ci `litestar-kafka` scenario renders with PyPI off so actionlint checks
the web variant of `finalize-release`'s `needs` without `pypi-publish`.
