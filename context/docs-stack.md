# Documentation stack

## Sphinx with the bare Shibuya theme replaces MkDocs

**Id:** 5133caa8-3231-4d4d-877b-041b315cb87a
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-006 ([`docs/adr/006-sphinx-shibuya-for-documentation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/006-sphinx-shibuya-for-documentation.md))
**Revisit when:** Shibuya stops being published on PyPI, or the Litestar-org reference sites change stack

Generated projects document with Sphinx, the `shibuya` theme from PyPI,
reStructuredText sources (MyST enabled for Markdown pages), autodoc plus
napoleon for the API reference, and a set of extensions matching the Litestar
organization's sites. Docs builds install the package, not only the docs group.
Publishing still goes through the `gh-pages` branch, so no Pages setting
changed.

**Reason:** the MkDocs 2.0 line was unstable and pinning 1.x indefinitely was a
dead end; the shipped MkDocs setup installed `mkdocs-material` without
configuring it and hand-maintained an API page that did not track the code.
The visual target (Litestar, Advanced Alchemy, Polyfactory) turned out to be
Sphinx plus Shibuya, so adopting that stack is the direct path. Autodoc must
import the package and the modules' dependencies, hence the package install.

**Rejected alternative:** `litestar-sphinx-theme` — Shibuya plus Litestar
branding, distributed as a git dependency; wrong for a generic template.

**Rejected alternative:** `sphinxcontrib-typer` for the CLI reference — works,
but generating the page from the live app at build time keeps the CLI uniform
with the worker and web generators and adds no extension; `sphinx-click` is
unusable because Typer vendors its own Click.

**Consequence:** the `--unsafe` YAML-check flag that existed only for
`mkdocs.yml` was dropped; `conf.py` gets a ruff per-file ignore; a duplicate
docstring autodoc surfaced and was removed.

## PR docs previews deploy to a subfolder of the project's own `gh-pages`, same-repo only

**Id:** 55a74975-a6e0-4f18-8254-fa27f047e829
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-010 §1 ([`docs/adr/010-pr-docs-previews-and-released-issue-notifications.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/010-pr-docs-previews-and-released-issue-notifications.md))
**Revisit when:** the preview action ships fork support, or previews need to block merges
**See:** external-integrations.md#a-freshly-generated-project-is-green-on-first-push-with-zero-external-accounts — 392b6dcf-6e9d-441d-bf7b-64ba362578d7 — as of 2026-10-11
**See:** docs-versioning.md#docs-publish-only-the-current-version-and-carry-older-built-versions-forward-from-gh-pages — 858025c1-19a6-46f6-a237-01ba6477262a — as of 2026-10-11

A single-job `docs-preview.yml` on `pull_request` builds the Sphinx HTML and
hands deploy, removal on close and a sticky comment to a purpose-built action,
publishing under `pr-preview/pr-<N>/` on the project's own `gh-pages`. It runs
only when the head repository is the repository itself; fork PRs skip cleanly.
It renders only when `include_docs` is on (ADR-025) and is not in the `check`
gate.

**Reason:** the upstream pattern deployed to a separate repository with a
GitHub App token — a second repo and App to provision. Same-repo `pull_request`
carries a write token and needs no dangerous-triggers ignore because untrusted
fork code never runs with write access; for a solo-maintainer template,
same-repo branches are the common case. Removing a subfolder on close and
maintaining a comment would otherwise mean hand-rolled git on `gh-pages`,
exactly the surface the released-docs deploy moved away from. A bare artifact
has no live URL, which is the whole value.

**Rejected alternative:** a `workflow_run`/`pull_request_target` split for fork
coverage — deferred until the action supports forks.

**Consequence:** the released-docs deploys exclude `pr-preview/**` from
cleaning and merge rather than force-push, so previews survive a release and a
racing deploy cannot overwrite them.

## sphinx-lint and the case-conflict hook are always-on; link checking is weekly

**Id:** 726d9de8-c1d3-4974-9019-76c8bb5ffc5b
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-011 ([`docs/adr/011-docs-linting-and-cross-platform-filename-safety.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/011-docs-linting-and-cross-platform-filename-safety.md))
**Revisit when:** the matrix drops a case-insensitive platform, or linkcheck becomes reliable enough for PR time
**See:** ci-topology.md#network-dependent-checks-run-on-a-weekly-cron-never-in-the-merge-gate — 3e5b9525-9087-4125-b19f-80f6c226c01f — as of 2026-10-11
**See:** architecture-contracts.md#whole-program-analyzers-are-local-system-hooks-backed-by-the-style-group — 41f3397d-1afb-4e57-a0bd-b5ef85089bfc — as of 2026-10-11

`sphinx-lint` runs in the tox `style` env and as a prek local hook from the
same `style` group pin, scoped to `.rst` files. `check-case-conflict` is a prek
builtin, not a style tool. A `docs-linkcheck` tox env runs Sphinx's linkcheck,
driven by a weekly scheduled workflow and manual dispatch, never on pull
requests and never in `check`.

**Reason:** nothing checked the RST sources for markup Sphinx tolerates
silently, nothing caught link rot, and nothing caught two filenames differing
only in case — fine on Linux, a collision on the Windows and macOS matrix
cells. All three are account-free, so always-on fits. Link checking hits the
network and is inherently flaky; a dead external link must never block an
unrelated merge.

## Sphinx warnings use an exact, reviewable allowlist

**Id:** 2a555902-38e7-47d4-a231-445a8e6caa0f
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [issue #187](https://github.com/hasansezertasan/copier-pyproject/issues/187), [PR #242](https://github.com/hasansezertasan/copier-pyproject/pull/242); commit [ab6a857](https://github.com/hasansezertasan/copier-pyproject/commit/ab6a8575d401f41fb35ab98a1bf50a2a1ff29fe7); `docs/template-architecture.md`, Sphinx warning gate
**Verification:** corroborated — the rendered warning checker compares normalized sets in both directions, and the docs-build environment invokes it
**Revisit when:** Sphinx changes warning formatting or a previously unavoidable warning disappears
**See:** docs-versioning.md#the-sphinx-warning-gate-runs-in-a-job-the-required-check-context-aggregates — bc382803-5aa9-4582-9bad-1c9efef8fc49 — as of 2026-10-11

The docs-build gate captures Sphinx warnings and compares them with a committed
allowlist. It rejects both new unexpected warnings and expected warnings that
are no longer emitted. The default allowlist is empty. Normalization removes
machine-specific path prefixes and folds Windows separators, while preserving
line numbers. Sphinx's `nitpicky` mode remains off.

**Reason:** an individually justified upstream warning should not force a choice
between permanently red documentation builds and broad warning suppression.
Exact entries make exceptions reviewable; the reverse comparison prevents
obsolete exceptions from accumulating silently.

**Rejected alternative:** make every warning fatal directly through Sphinx's
warning-as-error mode. It was superseded by the allowlist so unavoidable
exceptions can coexist with a regression gate.

**Alternative deferred:** enable `nitpicky` immediately. The issue anticipated
a noisy initial cross-reference cleanup and left this for a separate pass.
Removing line numbers was also considered but not selected; no further reason
for that choice was established in the reviewed sources.

## The Sphinx subsystem is toggleable (`include_docs`, default on); the maintainer guide is not

**Id:** e983d1e7-421f-4926-9415-a3da4626f220
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-025 ([`docs/adr/025-optional-docs-subsystem.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/025-optional-docs-subsystem.md)); issue #252
**Revisit when:** the six files that hard-reference `docs/maintaining/setup.rst` move, or a preset wants docs off by default
**See:** repo-setup.md#maintainer-repository-setup-has-one-actor-tagged-home-in-the-docs-tree — 4e0fcdab-d3b9-4f96-b61d-8e34927af98d — as of 2026-10-11

One boolean gates the whole Sphinx site: the `docs/` pages, the `docs`
dependency group, the `docs-*` tox envs, sphinx-lint in style and prek, the
docs workflows, the `deploy-docs` release job and the related README, support
and contributing links. It defaults on in every preset. `docs/maintaining/`
ships regardless; only its GitHub Pages step is conditional.

**Reason:** docs was the only substantial subsystem with no toggle, and a small
library or internal tool often wants a README and nothing more. Default-on keeps
`copier update` non-breaking and the published-site baseline. The maintainer
setup guide is read as plain text by the `repo-setup` skill and hard-referenced
from six other files, so relocating it would break all of them; a `docs/`
directory holding just the guide is preferable.

**Consequence:** a README-only project is a supported shape; the later
docs-dependent features (tested examples, CLI reference, versioned docs) are
gated by construction.

## Documentation code examples are executed, not pasted

**Id:** 2a95e867-8cca-44e9-9844-a7109e5f6a7b
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-028 ([`docs/adr/028-tested-documentation-examples.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/028-tested-documentation-examples.md))
**Revisit when:** another Markdown file is adopted as a doctest surface, or the per-component CI jobs stop replacing tox's default env list
**See:** docs-stack.md#the-sphinx-subsystem-is-toggleable-include_docs-default-on-the-maintainer-guide-is-not — e983d1e7-421f-4926-9415-a3da4626f220 — as of 2026-10-11

Complete Python examples live in `docs/examples/`, rendered into Sphinx pages
with `literalinclude` and imported or called by the regular pytest suite. The
directory is in scope for ruff, every type checker and pylint, but outside the
package and coverage source set. The Sphinx `doctest` extension runs inline
`>>>` snippets through a `docs-doctest` tox env and a dedicated CI job in the
`check` gate. The top-level `README.md` is a pytest `testpaths` entry collected
with a doctest glob for that basename only; `tests/conftest.py` ignores `*.md`
so no future `tests/**/README.md` is swept in, and the prek pytest hook runs
bare `pytest` so `testpaths` is honoured. README examples leave a blank line
before the closing fence because doctest ends expected output at the first
blank line.

**Reason:** pasted fences drift silently from the API; neither the suite nor the
static gates execute them, which the template's high coverage bar otherwise
makes easy to miss. The dedicated doctest job exists because the per-component
test jobs pass marker arguments that replace tox's default env list, so
doctests would never run otherwise. Examples are documentation, not product
code, hence outside coverage.

**Rejected alternative:** an explicit `pytest tests` target in the hook — would
let a broken README doctest pass locally and surface only in CI.

**Consequence:** the Sphinx builder owns `.rst` prose and pytest owns the one
curated Markdown surface; neither collector overlaps the other.

## The four auto-generated reference pages keep their current generators

**Id:** aa157658-027b-42c3-8a2b-1e6b40b6b739
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-038 ([`docs/adr/038-sphinx-api-reference-rendering-strategy.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/038-sphinx-api-reference-rendering-strategy.md)), refreshed 2026-10-05
**Revisit when:** a `sphinxcontrib-openapi` pilot confirms OpenAPI 3.1 rendering, an AsyncAPI Sphinx renderer appears, or argparse CLIs are judged to need a reference page
**See:** docs-stack.md#sphinx-with-the-bare-shibuya-theme-replaces-mkdocs — 5133caa8-3231-4d4d-877b-041b315cb87a — as of 2026-10-11

The CLI (Typer), config (autodoc-pydantic), OpenAPI and AsyncAPI references are
all derived from the live app at build time, nothing committed. The OpenAPI and
AsyncAPI pages are raw spec dumps via `literalinclude`; none of the surveyed
extensions is adopted now. `sphinxcontrib-openapi` is the designated future
upgrade for OpenAPI; `sphinx-argparse-cli` the candidate if argparse CLIs get a
page; an AsyncAPI renderer does not exist and would be an upstream
contribution.

**Reason:** every extension is another docs dependency to pin, so the bar is a
rendering upgrade large enough to justify it — met only for OpenAPI/AsyncAPI,
where today's output is a dump. Native-rST rendering is the only style
consistent with the offline, self-contained docs posture; ReDoc, Swagger-UI
(CDN by default), RapiDoc and the embeddable bundles ship a JS app into the
docs. `sphinxcontrib-typer` covers only Typer, so argparse would still need
separate handling. `asyncapi-sphinx-ext` is early-stage, stale, and wants
channels authored in docstrings rather than consuming a generated spec.

**Rejected alternative:** `sphinx-pydantic` — abandoned. `pydantic-kitbash` and
`sphinx-jsonschema` — no advantage for a settings reference.

**Consequence:** `sphinxcontrib-openapi`'s OpenAPI 3.1 support has lagged and
both frameworks emit 3.1, so a pilot must precede adoption.
