# ADR-039: Optional PyPI publishing

## Status

Accepted (2026-10).

## Context

Every generated project used to publish to PyPI on release: `release.yml`
always rendered a `pypi-publish` job, and `attach-github-release` and
`finalize-release` both listed it in `needs`. A project that must not go to PyPI
had no supported path to a release. Hand-editing the generated workflow was the
only way out, and that edit then conflicted on every `copier update`.

Publishing to PyPI is wrong or impossible for:

- private or internal projects, distributed from Git or a private index;
- a project whose PyPI name (`github_repo_name`) already belongs to someone
  else, where trusted publishing fails on the first release;
- projects that only ship other artifacts, or only want GitHub Releases.

## Decision

### Optional PyPI publishing

**Id:** 20be7463-ca95-4d01-82c9-71f632d1b4be
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [issue #382](https://github.com/hasansezertasan/copier-pyproject/issues/382); maintainer decisions while implementing it, 2026-10-11
**Revisit when:** the PyPI project name becomes its own question, or Homebrew / Scoop gain a non-PyPI source for a pure-Python package

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

**Homebrew and Scoop.** A Homebrew formula is built from the PyPI sdist
(`brew update-python-resources`), and the Scoop pipx manifest polls PyPI. Only
a prebuilt executable (a cask or binary manifest) is fetched from the GitHub
Release. A hidden `can_distribute_natively` (`is_app` and either PyPI publishing
or a `primary_executable`) therefore gates `include_homebrew` and
`include_scoop`. Without it they are not asked, and their `default` repeats the
guard, so a preset cannot turn on a tap or bucket that could never update.

**Rejected alternatives:**

- *Leave Homebrew/Scoop ungated and document the caveat.* Rejected: it renders
  a tap/bucket dispatch whose formula or manifest can never resolve, which is a
  failure on first release that the template can prevent at question time.
- *Point the install docs at a GitHub Release wheel download.* Rejected in
  favor of Git URL installs, which work with every installer the docs already
  show, can be pinned with `@<tag>`, and work over SSH for private repositories.
- *Make the PyPI project name its own question in this change.* Deferred as a
  separate concern: it decouples the distribution name from the package name,
  which touches far more than the publish job.

## Consequences

- A project can release without PyPI, and that choice survives `copier update`.
- An explicit `--data include_homebrew=true` still renders the tap even when
  the question is gated off. Copier applies passed data to an unasked question,
  which is the existing contract of the `is_app` gate too.
- `template-ci`'s `litestar-kafka` scenario renders with PyPI off, so actionlint
  checks the web variant of `finalize-release`'s `needs` without `pypi-publish`.
