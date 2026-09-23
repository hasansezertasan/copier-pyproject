# ADR-027: Sphinx API-reference rendering strategy (Typer / pydantic / OpenAPI / AsyncAPI)

## Status

Accepted (2026-08). Extends [ADR-006](006-sphinx-shibuya-for-documentation.md),
which chose Sphinx + Shibuya and weighed the *CLI* generator only, to cover all
four auto-generated reference pages and to record why the third-party Sphinx
API-doc extensions surveyed below are (mostly) **not** adopted.

## Context

The docs subsystem ([ADR-025](025-optional-docs-subsystem.md)) auto-generates
four reference pages, all following one deliberate pattern: when `include_docs`
is set, `docs/conf.py` shells the **live app object** at build time into a
gitignored `docs/_generated/` directory (each subprocess runs `check=True`, so a
failure breaks the build), and the reference page pulls the artifact in. No
schema files are hand-maintained or committed.

The four generators are **not** at the same rendering quality, which is the crux
of this decision:

| Reference | Toggle | Mechanism | Output rendered as |
| --- | --- | --- | --- |
| CLI (Typer) | `include_cli` + `cli_framework == typer` | `python -m typer … utils docs` → `cli.md` | Structured Markdown (MyST `{include}`) |
| Config (pydantic) | `include_pydantic_settings` | `autodoc-pydantic` `.. autopydantic_settings::` on the live model | Structured autodoc directive |
| OpenAPI (web) | `include_web` | Litestar `… schema openapi` / FastAPI `app.openapi()` dump → `openapi.yaml` | **Raw YAML** (`.. literalinclude::`) |
| AsyncAPI (worker) | `include_worker` | `faststream docs gen --yaml` → `asyncapi.yaml` | **Raw YAML** (`.. literalinclude::`) |

The CLI and config references are genuinely *rendered* documentation. The
OpenAPI and AsyncAPI references are, today, a syntax-highlighted spec file pasted
into a page via `literalinclude` — a reader gets no navigable endpoint/channel
docs, only the raw schema. That gap is what prompted surveying the Sphinx
API-doc ecosystem.

### Packages surveyed

| Package | Scope | Health (2026-08) | Fit |
| --- | --- | --- | --- |
| [`sphinxcontrib-typer`](https://github.com/sphinx-contrib/typer) | `.. typer::` renders a Typer app (html/svg/text) | Healthy, MIT | Redundant — see below |
| [`sphinxcontrib-openapi`](https://github.com/sphinx-contrib/openapi) | `.. openapi::` renders a spec to native rST via httpdomain (2.0/3.0/3.1) | Mature (~126★), active | **Best fit for a future OpenAPI upgrade** |
| [`sphinxcontrib-redoc`](https://github.com/sphinx-contrib/redoc) | Embeds ReDoc JS for OpenAPI | Older, moderate | JS/offline/CSP concern |
| [`SAP/swagger-plugin-for-sphinx`](https://github.com/SAP/swagger-plugin-for-sphinx) | Swagger-UI embed | Active | **CDN by default** — wrong posture |
| [`Unidocs1/sphinx_openapi`](https://github.com/Unidocs1/sphinx_openapi) | *Downloads* remote specs for ReDoc | 0★, niche | Irrelevant — specs are generated locally |
| [`mortbauer/asyncapi-sphinx-ext`](https://github.com/mortbauer/asyncapi-sphinx-ext) | `asyncapi_channels`/`asyncapi_overview` directives | 3★, "early stage", stale | Not adoptable |
| [`git-pull/gp-sphinx`](https://github.com/git-pull/gp-sphinx) | Whole-`conf.py` bundle (themes + autodoc collection) | 1★, personal monorepo | Out of scope — a config framework, not a renderer |

### Additional candidates surveyed (second pass)

**CLI**
| Package | Scope | Health | Fit |
| --- | --- | --- | --- |
| [`sphinx-argparse-cli`](https://github.com/tox-dev/sphinx-argparse-cli) | `sphinx_argparse_cli` directive, sub-command-friendly | Active, tox-dev org | **Best candidate to fill the `argparse` gap** (see below) |
| [`sphinx-argparse`](https://github.com/alex-rudakov/sphinx-argparse) | `argparse` directive | Maintained | argparse baseline; less clean for nested CLIs |
| [`sphinxcontrib-autoprogram`](https://github.com/sphinx-contrib/autoprogram) | Expands an `ArgumentParser` into `program`/`option` | Mature, low activity | argparse only |
| [`sphinxcontrib-programoutput`](https://pypi.org/project/sphinxcontrib-programoutput/) | Embeds any command's `--help` stdout | Mature, low activity | Framework-agnostic but unstructured |

**OpenAPI**
| Package | Scope | Health | Fit |
| --- | --- | --- | --- |
| [`sphinx-rapidoc`](https://pypi.org/project/sphinx-rapidoc/) | RapiDoc web-component renderer | Young (2025), low adoption | JS embed — same offline/CSP concern as ReDoc/Swagger |
| [`sphinxcontrib-swaggerui`](https://pypi.org/project/sphinxcontrib-swaggerui/) | `swaggerui` directive, vendors swagger-ui assets | Stale (single release, 2023) | Vendored (no CDN) but low-maintenance risk |

**AsyncAPI** (no Sphinx directive exists — these are the build path for a port)
| Package | Scope | Health | Fit |
| --- | --- | --- | --- |
| [`@asyncapi/html-template`](https://github.com/asyncapi/html-template) + [`@asyncapi/generator`](https://github.com/asyncapi/generator) | Official spec → static HTML / Markdown | Active, official org | Canonical `asyncapi.yaml` → browsable docs; Markdown output could feed MyST |
| `@asyncapi/react-component` | Embeddable renderer both templates use | Active, official org | The swagger-ui-dist analog to wrap in a Sphinx directive |

**pydantic**
| Package | Scope | Health | Fit |
| --- | --- | --- | --- |
| [`pydantic-kitbash`](https://github.com/canonical/pydantic-kitbash) | Canonical's model → config-reference directive | New/niche, active (Canonical) | Closest live alternative to autodoc-pydantic |
| [`sphinx-jsonschema`](https://github.com/lnoor/sphinx-jsonschema) | Renders any JSON Schema (`model_json_schema()`) as tables | Mature, maintained | Low-dep fallback route |
| [`sphinx-pydantic`](https://github.com/Zsailer/sphinx-pydantic) | `pydantic` directive via sphinx-jsonschema | **Abandoned** (no release since ~2020) | Do not adopt |

**Embeddable API-UI bundles** (portable to a Sphinx directive, incl. the `openapipages` idea)
| Package | Scope | Health |
| --- | --- | --- |
| [`@scalar/api-reference`](https://github.com/scalar/scalar) | Single-file, no-build OpenAPI UI | Very active |
| [`@stoplight/elements`](https://github.com/stoplightio/elements) | `<elements-api>` web component (no Sphinx wrapper yet) | Active |
| [`redoc` standalone](https://github.com/Redocly/redoc) / [`swagger-ui-dist`](https://www.npmjs.com/package/swagger-ui-dist) / `rapidoc` | Raw embeddable bundles behind the wrappers above | Active |
| [`openapipages` (fork)](https://github.com/eltoder/openapipages) | Alternate maintained line of the original `openapipages` | — |

## Decision

**Keep all four current generators unchanged for now.** Do not adopt any of the
surveyed extensions in this iteration. Record the OpenAPI upgrade and the
AsyncAPI ecosystem gap as tracked follow-ups rather than acting on them here.

Per reference:

- **CLI (Typer): keep `typer … utils docs`.** `sphinxcontrib-typer` renders more
  richly but was already weighed and rejected in ADR-006: it adds an extension,
  and it covers only Typer — `cli_framework == argparse` would still need
  separate handling, breaking the uniform "shell the live app into
  `_generated/`" pattern. No change. **Noted gap:** the CLI reference page is
  produced *only* for `cli_framework == typer`; an `argparse` CLI currently gets
  no generated reference. [`sphinx-argparse-cli`](https://github.com/tox-dev/sphinx-argparse-cli)
  (tox-dev, sub-command-aware) is the cleanest candidate to close that gap if we
  decide argparse CLIs warrant a reference page — a separate follow-up, not
  resolved here.
- **Config (pydantic): keep `autodoc-pydantic`.** It is the best-in-class option
  and is already the mechanism. The only live alternatives —
  `pydantic-kitbash` (new/niche) and `sphinx-jsonschema` (JSON-Schema tables) —
  offer no advantage for our settings-reference use; `sphinx-pydantic` is
  abandoned. No change.
- **OpenAPI (web): keep the `literalinclude` dump for now; `sphinxcontrib-openapi`
  is the designated future upgrade.** It renders to native rST (no JS, no CDN, no
  CSP concern), which suits the template's self-contained/offline posture, unlike
  the ReDoc and Swagger-UI embedders. The Swagger plugin's CDN-by-default is an
  outright poor fit for a template that ships strict workflow/CSP hygiene.
  `Unidocs1/sphinx_openapi` is irrelevant (download-only). The JS-embed
  alternatives — `sphinx-rapidoc`, `sphinxcontrib-swaggerui`, and hand-wrapping a
  standalone bundle (Scalar, Stoplight Elements, RapiDoc, redoc/swagger-ui-dist,
  or an `openapipages`-style port) — are all ruled out by the same offline/CSP
  posture. **Open risk to verify
  before adopting:** `sphinxcontrib-openapi`'s OpenAPI 3.1 support has
  historically lagged, and both Litestar and FastAPI emit 3.1 — a pilot must
  confirm the generated specs render correctly.
- **AsyncAPI (worker): keep the `literalinclude` dump; there is no adoptable
  renderer.** `asyncapi-sphinx-ext` is self-described "early stage", stale, and
  wants channels authored in docstrings rather than consuming a generated
  `asyncapi.yaml` — the opposite of our generate-from-live-app model. This is a
  genuine, unfilled ecosystem gap; a purpose-built directive that renders a
  generated `asyncapi.yaml`/`.json` (e.g. an `openapipages`-style static
  renderer) would be novel and is the strongest candidate for an upstream
  contribution, but is out of scope here. The realistic build path for such a
  port is the official AsyncAPI stack — `@asyncapi/react-component` (the
  embeddable renderer) or `@asyncapi/generator` + `@asyncapi/html-template`
  (spec → static HTML/Markdown, the latter feedable into MyST).

## Rationale

- **The current pattern's value is uniformity.** All four generators shell the
  live app into `_generated/`; a per-reference extension erodes that. The bar for
  adopting one is a rendering upgrade large enough to justify the divergence.
- **That bar is only met for OpenAPI/AsyncAPI**, where today's output is a raw
  spec dump — not for CLI/config, which already render properly.
- **Posture rules out the JS/CDN OpenAPI options.** Native-rST rendering is the
  only style consistent with the template's offline/self-contained defaults.
- **The AsyncAPI gap is real, not an oversight** — no production-grade Sphinx
  renderer for an AsyncAPI spec file exists, which is why the dump stands.

## Consequences

- No template changes in this ADR — it records evaluation and direction.
- Follow-up (not committed here): pilot `sphinxcontrib-openapi` against a
  generated web project for both `web_framework` values, checking OpenAPI 3.1
  rendering; if it clears, a later ADR would swap the web `literalinclude` for the
  directive and add the extension to the `docs` group under the `include_web`
  guard.
- Follow-up (not committed here): prototype an AsyncAPI-spec → Sphinx renderer as
  a potential upstream contribution; if it matures, a later ADR would wire it into
  the worker reference page.
- Follow-up (not committed here): decide whether an `argparse` CLI warrants a
  generated reference page (currently none); if so, `sphinx-argparse-cli` is the
  designated candidate.
- ADR-006's CLI-generator rationale is unchanged and now cross-referenced here as
  the precedent for keeping the Typer generator over `sphinxcontrib-typer`.
