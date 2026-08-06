# Opt-in Homebrew tap + Scoop bucket distribution — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two independent opt-in toggles (`include_homebrew`, `include_scoop`) that scaffold release automation + install docs so generated app projects can publish a Homebrew tap formula and a Scoop bucket manifest.

**Architecture:** Two `default: false`, `when: is_app` Copier toggles (ADR-009 posture). On each release, jobs inside `release.yml` (`needs: finalize-release`) render a formula/manifest from a committed `.tmpl` and open a PR to the author's `homebrew-tap` / `scoop-bucket` repo via `peter-evans/create-pull-request`, gated-on-secret and non-blocking. The formula/manifest ship the prebuilt binary from the release when an executable toggle is enabled (`primary_executable` precedence `freezer > compiler > launcher`), else a PyPI/virtualenv fallback.

**Tech Stack:** Copier + Jinja2, GitHub Actions, `peter-evans/create-pull-request`, `gh` CLI, Homebrew Ruby formula, Scoop JSON manifest. Repo-level tests: pytest with the `render(**answers) -> Path` fixture in `tests/conftest.py`.

**Spec:** `docs/superpowers/specs/2026-08-06-homebrew-scoop-distribution-design.md`

## Global Constraints

- Toggles are `type: bool`, `default: "{{ 'include_X' in preset_map[preset] }}"`, `when: "{{ is_app }}"`. Add both to the `full` list in `preset_map` (`copier.yml:74-97`). Do NOT add to `library`/`tool`/`web`.
- `.example-input.yml` stays unchanged (library preset; toggles are `when: is_app`-gated).
- Conventional target repos: **`homebrew-tap`** and **`scoop-bucket`** (so `brew install <user>/tap/<pkg>` and `scoop bucket add <user> …/scoop-bucket` resolve). The spec's `homebrew-<name>` was a placeholder; use the conventional names.
- Secret names: **`HOMEBREW_TAP_TOKEN`** and **`SCOOP_BUCKET_TOKEN`** (separate per distribution). Gate with a job-env presence flag (`… != ''`) because `secrets` is unreadable in `if:`; skip with a visible `::notice::` when unset — never fail the release.
- `primary_executable` precedence is **`freezer` > `compiler` > `launcher`**. Empty string ⇒ PyPI fallback path.
- Runtime placeholders in `.tmpl` files use `@@NAME@@` (NEVER Jinja `{{ }}`) so the copier-render and release-render layers never collide. Values known at render time (class name, package name, exe filename) use Jinja; values known only at release time (version, url, sha256) use `@@…@@`.
- Hidden computed question names must NOT start with `_` (Copier renders them empty otherwise) — `primary_executable`, like `primary_component`/`is_app`.
- **Workflow hardening (must stay zizmor + ghalint green):** `permissions: {}` top-level already exists in `release.yml`; new jobs get least-privilege `permissions:` (checkout-only jobs `contents: read`), `timeout-minutes`, `persist-credentials: false` on every checkout, all `uses:` SHA-pinned. **Reuse the exact `uses: …@<sha>  # vX` lines already in the repo** — copy `actions/checkout` and `peter-evans/create-pull-request` pins verbatim from `template/.github/workflows/{% raw %}{% if include_all_contributors %}all-contributors.yml{% endif %}{% endraw %}.jinja`; do not invent SHAs (Renovate maintains them).
- **No untrusted `${{ }}` in `run:`** — pass `github.*`/`needs.*` via `env:` and read as `"$VAR"`.
- Every `${{ … }}` inside a `.jinja` workflow must be wrapped in `{% raw %}…{% endraw %}`.
- Markdown guarded sections keep exactly one blank line around `{% if %}` (copier `trim_blocks` is OFF; markdownlint `MD012` gates) — see the `jinja-markdown-whitespace` memory.

---

## File Structure

**Pass 1 (docs/contract):**
- `copier.yml` — modify: add `primary_executable` computed var, `include_homebrew`/`include_scoop` toggles, `full` preset entries.
- `tests/test_distribution.py` — create: render-assert tests for the whole feature.
- `template/README.md.jinja` — modify: brew/scoop install lines in the `is_app` block.
- `template/docs/installation.rst.jinja` — modify: brew/scoop `code-block`s.
- `template/.github/CONTRIBUTING.md.jinja` — modify: one-time repo-setup steps.
- `docs/adr/017-opt-in-homebrew-scoop-distribution.md` — create: the ADR.
- `CLAUDE.md` (root) — modify: Optional-components list + `primary_executable` note.

**Pass 2 (automation):**
- `template/.github/packaging/{% if include_homebrew %}homebrew-formula.rb.tmpl{% endif %}.jinja` — create.
- `template/.github/packaging/{% if include_scoop %}scoop-manifest.json.tmpl{% endif %}.jinja` — create.
- `template/.github/workflows/release.yml.jinja` — modify: `publish-homebrew` + `publish-scoop` jobs.
- `template/.github/{% if include_web %}ghalint.yaml{% endif %}.jinja` — modify: widen filename condition + add job_secrets exclusions.
- `_typos.toml` — modify (if needed): allow Ruby/JSON tokens in `.tmpl`.

---

## PASS 1 — Docs / Contract

### Task 1: `copier.yml` toggles + `primary_executable` + preset

**Files:**
- Modify: `copier.yml` (computed-helpers block ~L227-244; `preset_map` full list L74-97; new section at end of file)
- Test: `tests/test_distribution.py`

**Interfaces:**
- Produces: answers `include_homebrew: bool`, `include_scoop: bool` (stored in `.copier-answers.yml` only when `is_app`); computed `primary_executable: str` (`"freezer"|"compiler"|"launcher"|""`).

- [ ] **Step 1: Write the failing test** — create `tests/test_distribution.py`:

```python
"""Opt-in Homebrew tap + Scoop bucket distribution (issue #146)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import yaml

PKG = "example"
USER = "octocat"


def _answers(root: Path) -> dict[str, Any]:
    text = (root / ".copier-answers.yml").read_text(encoding="utf-8")
    return yaml.safe_load(text)


def test_full_preset_enables_distribution(render: Callable[..., Path]) -> None:
    answers = _answers(render(preset="full"))
    assert answers["include_homebrew"] is True
    assert answers["include_scoop"] is True


def test_library_never_asks_distribution(render: Callable[..., Path]) -> None:
    # when: is_app is false for a library, so the toggles are never stored.
    answers = _answers(render(preset="library"))
    assert "include_homebrew" not in answers
    assert "include_scoop" not in answers


def test_app_defaults_distribution_off(render: Callable[..., Path]) -> None:
    answers = _answers(render(preset="tool"))  # cli+tui -> is_app true
    assert answers["include_homebrew"] is False
    assert answers["include_scoop"] is False
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_distribution.py -v`
Expected: FAIL — `KeyError: 'include_homebrew'` (toggle not defined yet).

- [ ] **Step 3: Add the `primary_executable` computed var** to `copier.yml`, immediately after the `primary_component` block (after `copier.yml:238`):

```yaml
# Single source of truth for which prebuilt binary the brew/scoop packaging
# references when several executable toggles are enabled. Precedence
# freezer > compiler > launcher (freezer/compiler are self-contained; launcher
# needs network on first run). Empty ⇒ no executable toggle ⇒ PyPI fallback.
primary_executable:
  type: str
  when: false
  default: "{% if include_freezer %}freezer{% elif include_compiler %}compiler{% elif include_launcher %}launcher{% endif %}"
```

- [ ] **Step 4: Add both toggles as a new section at the END of `copier.yml`** (after the `is_app` block, L244 — `is_app` must be defined before these because their `when:` reads it):

```yaml
# ── ⑧ Distribution (opt-in; publishes to a separate tap/bucket repo) ─────────
include_homebrew:
  type: bool
  default: "{{ 'include_homebrew' in preset_map[preset] }}"
  when: "{{ is_app }}"
  help: >-
    Publish a Homebrew tap formula on each release? Requires a homebrew-tap repo under your account and a HOMEBREW_TAP_TOKEN secret (one-time setup, documented in CONTRIBUTING.md).
include_scoop:
  type: bool
  default: "{{ 'include_scoop' in preset_map[preset] }}"
  when: "{{ is_app }}"
  help: >-
    Publish a Scoop bucket manifest on each release? Requires a scoop-bucket repo under your account and a SCOOP_BUCKET_TOKEN secret (one-time setup, documented in CONTRIBUTING.md). Best paired with an executable toggle (Scoop favors binaries).
```

- [ ] **Step 5: Add both to the `full` preset** in `preset_map` (after `copier.yml:97`, `- include_vpn`):

```yaml
      - include_homebrew
      - include_scoop
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `uv run pytest tests/test_distribution.py -v`
Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add copier.yml tests/test_distribution.py
git commit -m "feat: add include_homebrew/include_scoop toggles and primary_executable"
```

---

### Task 2: README + installation install docs

**Files:**
- Modify: `template/README.md.jinja` (the `{% if is_app %}` app-install block, ~L65-86)
- Modify: `template/docs/installation.rst.jinja` (the `{% if is_app %}` Stable-release block, ~L14-26)
- Test: `tests/test_distribution.py`

**Interfaces:**
- Consumes: `include_homebrew`, `include_scoop`, `github_user`, `github_repo_name`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_distribution.py`:

```python
def _read(root: Path, *parts: str) -> str:
    return (root / Path(*parts)).read_text(encoding="utf-8")


def test_readme_shows_brew_and_scoop_when_enabled(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_scoop=True)
    readme = _read(root, "README.md")
    assert f"brew install {USER}/tap/{PKG}" in readme
    assert f"scoop install {USER}/{PKG}" in readme


def test_readme_omits_brew_and_scoop_when_disabled(render: Callable[..., Path]) -> None:
    readme = _read(render(preset="tool"), "README.md")
    assert "brew install" not in readme
    assert "scoop install" not in readme


def test_installation_rst_shows_brew_when_enabled(render: Callable[..., Path]) -> None:
    rst = _read(render(preset="tool", include_homebrew=True), "docs", "installation.rst")
    assert f"brew install {USER}/tap/{PKG}" in rst
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_distribution.py -k "readme or installation_rst" -v`
Expected: FAIL — brew/scoop strings absent.

- [ ] **Step 3: Read the target blocks** to match surrounding style:

Run: `sed -n '60,90p' template/README.md.jinja && echo '---' && sed -n '10,30p' template/docs/installation.rst.jinja`

- [ ] **Step 4: Add the README lines** inside the existing `{% if is_app %}` block (place after the `uvx` line, before the block's closing `{% endif %}` / library `{% else %}`). Keep one blank line around each guard (MD012):

```jinja
{% if include_homebrew %}
Install with [Homebrew](https://brew.sh) (macOS/Linux):

```sh
brew install {{github_user}}/tap/{{github_repo_name}}
```
{% endif %}
{% if include_scoop %}
Install with [Scoop](https://scoop.sh) (Windows):

```sh
scoop bucket add {{github_user}} https://github.com/{{github_user}}/scoop-bucket
scoop install {{github_user}}/{{github_repo_name}}
```
{% endif %}
```

- [ ] **Step 5: Add the installation.rst blocks** inside its `{% if is_app %}` Stable-release section (after the `uvx` code-block):

```jinja
{% if include_homebrew %}
Homebrew (macOS/Linux):

.. code-block:: sh

    brew install {{github_user}}/tap/{{github_repo_name}}
{% endif %}
{% if include_scoop %}
Scoop (Windows):

.. code-block:: sh

    scoop bucket add {{github_user}} https://github.com/{{github_user}}/scoop-bucket
    scoop install {{github_user}}/{{github_repo_name}}
{% endif %}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_distribution.py -k "readme or installation_rst" -v`
Expected: PASS.

- [ ] **Step 7: Verify markdown lint on a rendered project** (MD012 guard):

Run: `uv run pytest tests/test_distribution.py -v` (all green), then spot-render and lint in Task 9. Commit now:

```bash
git add template/README.md.jinja template/docs/installation.rst.jinja tests/test_distribution.py
git commit -m "docs: document brew/scoop install behind include_homebrew/include_scoop"
```

---

### Task 3: CONTRIBUTING one-time setup docs

**Files:**
- Modify: `template/.github/CONTRIBUTING.md.jinja` ("Repository setup" section)
- Test: `tests/test_distribution.py`

**Interfaces:**
- Consumes: `include_homebrew`, `include_scoop`, `github_user`.

- [ ] **Step 1: Write the failing test** — append:

```python
def test_contributing_documents_tap_setup(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_scoop=True)
    contributing = _read(root, "CONTRIBUTING.md")
    assert "homebrew-tap" in contributing
    assert "HOMEBREW_TAP_TOKEN" in contributing
    assert "scoop-bucket" in contributing
    assert "SCOOP_BUCKET_TOKEN" in contributing


def test_contributing_omits_tap_setup_when_disabled(render: Callable[..., Path]) -> None:
    contributing = _read(render(preset="tool"), "CONTRIBUTING.md")
    assert "HOMEBREW_TAP_TOKEN" not in contributing
    assert "SCOOP_BUCKET_TOKEN" not in contributing
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_distribution.py -k contributing -v`
Expected: FAIL.

- [ ] **Step 3: Find the setup section anchor**

Run: `grep -n "Repository setup\|Trusted Publishing\|pending publisher\|Workflow permissions" template/.github/CONTRIBUTING.md.jinja`

- [ ] **Step 4: Add the gated setup steps** at the end of the "Repository setup" section (adapt heading level to the surrounding doc). Keep one blank line around guards:

```jinja
{% if include_homebrew %}
### Homebrew tap

The release workflow opens a PR to your Homebrew tap on each release. One-time setup:

1. Create the tap repo (once):

   ```sh
   gh repo create {{github_user}}/homebrew-tap --public \
     --description "Homebrew tap for {{github_user}} packages"
   ```

2. Create a fine-grained PAT with **Contents: read/write** and **Pull requests: read/write** scoped to `{{github_user}}/homebrew-tap`, then add it as the `HOMEBREW_TAP_TOKEN` repository secret. When unset, the publish job skips with a notice (never fails the release).
{% endif %}
{% if include_scoop %}
### Scoop bucket

1. Create the bucket repo (once):

   ```sh
   gh repo create {{github_user}}/scoop-bucket --public \
     --description "Scoop bucket for {{github_user}} packages"
   ```

2. Add a fine-grained PAT (**Contents** + **Pull requests** read/write on `{{github_user}}/scoop-bucket`) as the `SCOOP_BUCKET_TOKEN` repository secret. Skips with a notice when unset.
{% endif %}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/test_distribution.py -k contributing -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add template/.github/CONTRIBUTING.md.jinja tests/test_distribution.py
git commit -m "docs: document one-time homebrew-tap/scoop-bucket setup in CONTRIBUTING"
```

---

### Task 4: ADR-017 + root CLAUDE.md

**Files:**
- Create: `docs/adr/017-opt-in-homebrew-scoop-distribution.md`
- Modify: `CLAUDE.md` (root — "Optional components" list + a `primary_executable` note)

**Interfaces:** none (repo-level docs, not templated — no render test).

- [ ] **Step 1: Read ADR-009 for house style**

Run: `sed -n '1,60p' docs/adr/009-optional-external-quality-community-integrations.md`

- [ ] **Step 2: Write ADR-017** following the same section shape (Context / Decision / Consequences). Include verbatim: the two independent `default: false` toggles + `when: is_app`; binary-vs-PyPI payload with `primary_executable` precedence `freezer > compiler > launcher`; publish jobs live in `release.yml` (`needs: finalize-release`) because a `GITHUB_TOKEN`-fired `release: published` cannot trigger another workflow; cross-repo PAT gated-on-secret non-blocking; documented manual `homebrew-tap`/`scoop-bucket` creation; and the two **known limitations** — single-arch binaries (release matrix is per-OS, not per-arch) and best-effort Scoop PyPI fallback (Scoop favors binaries).

- [ ] **Step 3: Update root `CLAUDE.md`** — add to the "Optional components (all boolean)" list, after `include_megalinter` or near the executable toggles:

```markdown
- `include_homebrew` - Homebrew tap formula published on each release (opt-in;
  needs a `homebrew-tap` repo + `HOMEBREW_TAP_TOKEN` secret). See
  [ADR-017](docs/adr/017-opt-in-homebrew-scoop-distribution.md).
- `include_scoop` - Scoop bucket manifest published on each release (opt-in;
  needs a `scoop-bucket` repo + `SCOOP_BUCKET_TOKEN` secret). Both ship the
  prebuilt binary chosen by the `primary_executable` precedence
  (`freezer` > `compiler` > `launcher`) when an executable toggle is enabled,
  else a PyPI/virtualenv fallback.
```

- [ ] **Step 4: Lint the ADR + CLAUDE.md**

Run: `uv run --with sphinx-lint sphinx-lint docs/adr/017-opt-in-homebrew-scoop-distribution.md 2>/dev/null; npx --yes markdownlint-cli2 "docs/adr/017-opt-in-homebrew-scoop-distribution.md" "CLAUDE.md" 2>/dev/null || echo "(run repo's configured markdownlint in Task 9)"`
Expected: no errors (or defer to Task 9's canonical lint).

- [ ] **Step 5: Commit**

```bash
git add docs/adr/017-opt-in-homebrew-scoop-distribution.md CLAUDE.md
git commit -m "docs: add ADR-017 and document homebrew/scoop toggles in CLAUDE.md"
```

---

## PASS 2 — Automation

### Task 5: Formula + manifest templates

**Files:**
- Create: `template/.github/packaging/{% if include_homebrew %}homebrew-formula.rb.tmpl{% endif %}.jinja`
- Create: `template/.github/packaging/{% if include_scoop %}scoop-manifest.json.tmpl{% endif %}.jinja`
- Test: `tests/test_distribution.py`

**Interfaces:**
- Consumes: `github_user`, `github_repo_name`, `short_description`, `primary_executable`.
- Produces (at generated-repo path): `.github/packaging/homebrew-formula.rb.tmpl`, `.github/packaging/scoop-manifest.json.tmpl` with `@@VERSION@@`/`@@URL_*@@`/`@@SHA256_*@@`/`@@SDIST_*@@` placeholders. Formula class name = CamelCase of `github_repo_name`. Binary asset names = `{{github_repo_name}}-{{primary_executable}}-{macos,linux,windows}[.exe]` (matches `release.yml` artifact naming).

- [ ] **Step 1: Write the failing tests** — append:

```python
def test_homebrew_binary_formula_when_executable(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_freezer=True)
    tmpl = _read(root, ".github", "packaging", "homebrew-formula.rb.tmpl")
    assert "@@SHA256_MACOS@@" in tmpl           # binary path
    assert f"{PKG}-freezer-macos" in tmpl        # primary_executable asset
    assert "virtualenv" not in tmpl.lower()


def test_homebrew_pypi_formula_when_no_executable(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True)  # no executable toggle
    tmpl = _read(root, ".github", "packaging", "homebrew-formula.rb.tmpl")
    assert "@@SDIST_SHA256@@" in tmpl            # PyPI path
    assert 'pip", "install"' in tmpl or "pip install" in tmpl


def test_scoop_binary_manifest_when_executable(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_scoop=True, include_compiler=True)
    tmpl = _read(root, ".github", "packaging", "scoop-manifest.json.tmpl")
    assert "@@SHA256_WIN@@" in tmpl
    assert f"{PKG}-compiler-windows.exe" in tmpl


def test_packaging_absent_when_disabled(render: Callable[..., Path]) -> None:
    root = render(preset="tool")
    assert not (root / ".github" / "packaging").exists()
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_distribution.py -k "formula or manifest or packaging_absent" -v`
Expected: FAIL — files absent.

- [ ] **Step 3: Create the Homebrew formula template** at `template/.github/packaging/{% if include_homebrew %}homebrew-formula.rb.tmpl{% endif %}.jinja`:

```jinja
{% set classname = github_repo_name.split('-') | map('capitalize') | join %}
{# Rendered at release time: @@VERSION@@ etc. are substituted by publish-homebrew. #}
class {{classname}} < Formula
  desc "{{short_description}}"
  homepage "https://github.com/{{github_user}}/{{github_repo_name}}"
{% if primary_executable %}
  version "@@VERSION@@"

  on_macos do
    url "@@URL_MACOS@@"
    sha256 "@@SHA256_MACOS@@"
  end

  on_linux do
    url "@@URL_LINUX@@"
    sha256 "@@SHA256_LINUX@@"
  end

  def install
    bin.install Dir["*"].first => "{{github_repo_name}}"
  end
{% else %}
  url "@@SDIST_URL@@"
  sha256 "@@SDIST_SHA256@@"
  version "@@VERSION@@"

  depends_on "python@3.13"

  # Personal-tap style: pip-install from PyPI at build time (no pinned resource
  # blocks — homebrew-pypi-poet is unmaintained). Not homebrew-core acceptable.
  def install
    venv_python = libexec/"bin/python"
    system "python3.13", "-m", "venv", libexec
    system venv_python, "-m", "pip", "install", "{{github_repo_name}}==#{version}"
    bin.install_symlink Dir["#{libexec}/bin/{{github_repo_name}}*"]
  end
{% endif %}

  test do
    assert_match version.to_s, shell_output("#{bin}/{{github_repo_name}} --version")
  end
end
```

- [ ] **Step 4: Create the Scoop manifest template** at `template/.github/packaging/{% if include_scoop %}scoop-manifest.json.tmpl{% endif %}.jinja`:

```jinja
{% if primary_executable %}
{
  "version": "@@VERSION@@",
  "description": "{{short_description}}",
  "homepage": "https://github.com/{{github_user}}/{{github_repo_name}}",
  "architecture": {
    "64bit": {
      "url": "@@URL_WIN@@",
      "hash": "@@SHA256_WIN@@"
    }
  },
  "bin": [["{{github_repo_name}}-{{primary_executable}}-windows.exe", "{{github_repo_name}}"]],
  "checkver": "github",
  "autoupdate": {
    "architecture": {
      "64bit": {
        "url": "https://github.com/{{github_user}}/{{github_repo_name}}/releases/download/v$version/{{github_repo_name}}-{{primary_executable}}-windows.exe"
      }
    }
  }
}
{% else %}
{
  "version": "@@VERSION@@",
  "description": "{{short_description}}",
  "homepage": "https://github.com/{{github_user}}/{{github_repo_name}}",
  "depends": "python",
  "installer": {
    "script": ["python -m pip install --upgrade {{github_repo_name}}==@@VERSION@@"]
  },
  "uninstaller": {
    "script": ["python -m pip uninstall -y {{github_repo_name}}"]
  },
  "checkver": "pypi"
}
{% endif %}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_distribution.py -k "formula or manifest or packaging_absent" -v`
Expected: PASS.

- [ ] **Step 6: Sanity-check rendered syntax** (best-effort; ruby/jq may be absent):

Run: `uv run pytest tests/test_distribution.py -q` then optionally render `preset=full` and `ruby -c .../homebrew-formula.rb.tmpl` (placeholders are valid ruby strings) / `jq -e 'type' <(sed 's/@@[A-Z_]*@@/x/g' .../scoop-manifest.json.tmpl)`.

- [ ] **Step 7: Commit**

```bash
git add "template/.github/packaging" tests/test_distribution.py
git commit -m "feat: add homebrew formula and scoop manifest templates"
```

---

### Task 6: `release.yml` `publish-homebrew` job

**Files:**
- Modify: `template/.github/workflows/release.yml.jinja`
- Test: `tests/test_distribution.py`

**Interfaces:**
- Consumes: `needs.release-please.outputs.{tag_name,version,release_created}`, `finalize-release` (must precede), `primary_executable`, `github_repo_name`.
- Produces: a `publish-homebrew` job in the rendered `release.yml`.

- [ ] **Step 1: Write the failing test** — append:

```python
def test_release_has_publish_homebrew_job(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_freezer=True)
    wf = yaml.safe_load(_read(root, ".github", "workflows", "release.yml"))
    job = wf["jobs"]["publish-homebrew"]
    assert "finalize-release" in job["needs"]
    # gated-on-secret presence flag
    text = _read(root, ".github", "workflows", "release.yml")
    assert "HOMEBREW_TAP_TOKEN_SET" in text
    assert "peter-evans/create-pull-request" in text


def test_release_omits_publish_homebrew_when_disabled(render: Callable[..., Path]) -> None:
    text = _read(render(preset="tool"), ".github", "workflows", "release.yml")
    assert "publish-homebrew" not in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_distribution.py -k publish_homebrew -v`
Expected: FAIL.

- [ ] **Step 3: Read the finalize-release job + existing create-pull-request pin**

Run: `grep -n "finalize-release:\|attach-github-release:\|notify-released-issues:\|create-pull-request\|actions/checkout" template/.github/workflows/release.yml.jinja template/.github/workflows/*all-contributors*.jinja`

- [ ] **Step 4: Add the `publish-homebrew` job** to `release.yml.jinja`, after `finalize-release` (copy the exact `@<sha>  # vX` pins from the grep in Step 3). Wrap every `${{ }}` in `{% raw %}`:

```jinja
{% if include_homebrew %}

  publish-homebrew:
    name: Publish Homebrew formula
    needs: [release-please, finalize-release]
    if: {% raw %}${{ needs.release-please.outputs.release_created == 'true' }}{% endraw %}
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    env:
      TOKEN_SET: {% raw %}${{ secrets.HOMEBREW_TAP_TOKEN != '' }}{% endraw %}
    steps:
      - name: Announce skip when tap token unset
        if: {% raw %}${{ env.TOKEN_SET != 'true' }}{% endraw %}
        run: echo "::notice::HOMEBREW_TAP_TOKEN not set — skipping Homebrew publish."

      - name: Checkout tap repo
        if: {% raw %}${{ env.TOKEN_SET == 'true' }}{% endraw %}
        uses: actions/checkout@<sha>  # v7  (copy exact pin from repo)
        with:
          repository: {% raw %}${{ github.repository_owner }}{% endraw %}/homebrew-tap
          token: {% raw %}${{ secrets.HOMEBREW_TAP_TOKEN }}{% endraw %}
          path: tap
          persist-credentials: false

      - name: Checkout source (for the packaging template)
        if: {% raw %}${{ env.TOKEN_SET == 'true' }}{% endraw %}
        uses: actions/checkout@<sha>  # v7
        with:
          path: src
          persist-credentials: false

      - name: Render formula
        if: {% raw %}${{ env.TOKEN_SET == 'true' }}{% endraw %}
        env:
          TAG_NAME: {% raw %}${{ needs.release-please.outputs.tag_name }}{% endraw %}
          VERSION: {% raw %}${{ needs.release-please.outputs.version }}{% endraw %}
          REPO: {% raw %}${{ github.repository }}{% endraw %}
          GH_TOKEN: {% raw %}${{ github.token }}{% endraw %}
        run: |
          set -euo pipefail
          tmpl="src/.github/packaging/homebrew-formula.rb.tmpl"
          out="tap/Formula/{{github_repo_name}}.rb"
          mkdir -p tap/Formula
          base="https://github.com/$REPO/releases/download/$TAG_NAME"
{% if primary_executable %}
          workdir="$(mktemp -d)"
          declare -A sha
          for label in macos linux; do
            asset="{{github_repo_name}}-{{primary_executable}}-$label"
            gh release download "$TAG_NAME" --repo "$REPO" --pattern "$asset" --dir "$workdir"
            sha[$label]="$(shasum -a 256 "$workdir/$asset" | cut -d' ' -f1)"
          done
          sed \
            -e "s|@@VERSION@@|$VERSION|g" \
            -e "s|@@URL_MACOS@@|$base/{{github_repo_name}}-{{primary_executable}}-macos|g" \
            -e "s|@@SHA256_MACOS@@|${sha[macos]}|g" \
            -e "s|@@URL_LINUX@@|$base/{{github_repo_name}}-{{primary_executable}}-linux|g" \
            -e "s|@@SHA256_LINUX@@|${sha[linux]}|g" \
            "$tmpl" > "$out"
{% else %}
          sdist_url="https://pypi.io/packages/source/${VERSION:0:1}/{{github_repo_name}}/{{github_repo_name}}-$VERSION.tar.gz"
          sdist_sha="$(curl -fsSL "$sdist_url" | shasum -a 256 | cut -d' ' -f1)"
          sed \
            -e "s|@@VERSION@@|$VERSION|g" \
            -e "s|@@SDIST_URL@@|$sdist_url|g" \
            -e "s|@@SDIST_SHA256@@|$sdist_sha|g" \
            "$tmpl" > "$out"
{% endif %}

      - name: Open PR to tap
        if: {% raw %}${{ env.TOKEN_SET == 'true' }}{% endraw %}
        uses: peter-evans/create-pull-request@<sha>  # v8.1.1  (copy exact pin)
        with:
          token: {% raw %}${{ secrets.HOMEBREW_TAP_TOKEN }}{% endraw %}
          path: tap
          commit-message: {% raw %}"chore: update {{ '{{' }} github.event.repository.name {{ '}}' }} to ${{ needs.release-please.outputs.tag_name }}"{% endraw %}
          title: {% raw %}"chore: update {{github_repo_name}} to ${{ needs.release-please.outputs.tag_name }}"{% endraw %}
          branch: chore/{{github_repo_name}}-formula
          base: main
          delete-branch: true
{% endif %}
```

> Note for implementer: the `commit-message` line mixes Jinja and GHA syntax — simplest is to hardcode `{{github_repo_name}}` (known at render time) and keep only `${{ needs… }}` in `{% raw %}`. Verify the rendered YAML with the test in Step 6 and `prek run zizmor` in Task 9.

- [ ] **Step 5: Confirm `primary_executable` branch renders both ways** — the test already covers the freezer (binary) case; add the PyPI case:

```python
def test_publish_homebrew_pypi_branch(render: Callable[..., Path]) -> None:
    text = _read(render(preset="tool", include_homebrew=True), ".github", "workflows", "release.yml")
    assert "@@SDIST_URL@@".replace("@@", "") in text or "pypi.io/packages/source" in text
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_distribution.py -k "publish_homebrew" -v`
Expected: PASS (rendered `release.yml` is valid YAML — `yaml.safe_load` succeeds).

- [ ] **Step 7: Commit**

```bash
git add template/.github/workflows/release.yml.jinja tests/test_distribution.py
git commit -m "feat: add publish-homebrew job to release workflow"
```

---

### Task 7: `release.yml` `publish-scoop` job

**Files:**
- Modify: `template/.github/workflows/release.yml.jinja`
- Test: `tests/test_distribution.py`

**Interfaces:**
- Mirrors Task 6 for Scoop: checks out `scoop-bucket`, renders `scoop-manifest.json.tmpl` to `bucket/{{github_repo_name}}.json`, PRs via `SCOOP_BUCKET_TOKEN`. Binary path substitutes `@@URL_WIN@@`/`@@SHA256_WIN@@` from the `-windows.exe` asset; PyPI path substitutes only `@@VERSION@@`.

- [ ] **Step 1: Write the failing test** — append:

```python
def test_release_has_publish_scoop_job(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_scoop=True, include_compiler=True)
    wf = yaml.safe_load(_read(root, ".github", "workflows", "release.yml"))
    job = wf["jobs"]["publish-scoop"]
    assert "finalize-release" in job["needs"]
    text = _read(root, ".github", "workflows", "release.yml")
    assert "SCOOP_BUCKET_TOKEN_SET" in text or "SCOOP_BUCKET_TOKEN != ''" in text


def test_release_omits_publish_scoop_when_disabled(render: Callable[..., Path]) -> None:
    text = _read(render(preset="tool"), ".github", "workflows", "release.yml")
    assert "publish-scoop" not in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_distribution.py -k publish_scoop -v`
Expected: FAIL.

- [ ] **Step 3: Add the `publish-scoop` job** to `release.yml.jinja` (after `publish-homebrew`), same structure as Task 6 Step 4 with: `repository: …/scoop-bucket`, `token: SCOOP_BUCKET_TOKEN`, `path: bucket`, output `bucket/{{github_repo_name}}.json`, branch `chore/{{github_repo_name}}-manifest`. Windows-asset substitution:

```jinja
{% if primary_executable %}
          asset="{{github_repo_name}}-{{primary_executable}}-windows.exe"
          gh release download "$TAG_NAME" --repo "$REPO" --pattern "$asset" --dir "$workdir"
          sha_win="$(shasum -a 256 "$workdir/$asset" | cut -d' ' -f1)"
          sed \
            -e "s|@@VERSION@@|$VERSION|g" \
            -e "s|@@URL_WIN@@|$base/$asset|g" \
            -e "s|@@SHA256_WIN@@|$sha_win|g" \
            "$tmpl" > "$out"
{% else %}
          sed -e "s|@@VERSION@@|$VERSION|g" "$tmpl" > "$out"
{% endif %}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_distribution.py -k publish_scoop -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add template/.github/workflows/release.yml.jinja tests/test_distribution.py
git commit -m "feat: add publish-scoop job to release workflow"
```

---

### Task 8: ghalint job_secrets exclusion

**Files:**
- Modify: `template/.github/{% if include_web %}ghalint.yaml{% endif %}.jinja` — **rename** the conditional prefix to `{% if include_web or include_homebrew or include_scoop %}` and add the exclusions.
- Test: `tests/test_distribution.py`

**Interfaces:**
- Produces: rendered `.github/ghalint.yaml` that lists `publish-homebrew`/`publish-scoop` under the `job_secrets` `exclude` when their toggles are on (plus the existing web docker jobs when `include_web`).

- [ ] **Step 1: Write the failing test** — append:

```python
def test_ghalint_excludes_publish_jobs(render: Callable[..., Path]) -> None:
    root = render(preset="tool", include_homebrew=True, include_scoop=True)
    ghalint = _read(root, ".github", "ghalint.yaml")
    assert "publish-homebrew" in ghalint
    assert "publish-scoop" in ghalint


def test_ghalint_absent_without_any_secret_job(render: Callable[..., Path]) -> None:
    root = render(preset="tool")  # no web, no brew/scoop
    assert not (root / ".github" / "ghalint.yaml").exists()
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_distribution.py -k ghalint -v`
Expected: FAIL (filename still `include_web`-only; publish jobs absent).

- [ ] **Step 3: Read the current ghalint file**

Run: `cat "template/.github/{% if include_web %}ghalint.yaml{% endif %}.jinja"`

- [ ] **Step 4: Rename the file** so it renders whenever any secret-exposing job exists:

```bash
git mv "template/.github/{% if include_web %}ghalint.yaml{% endif %}.jinja" \
       "template/.github/{% if include_web or include_homebrew or include_scoop %}ghalint.yaml{% endif %}.jinja"
```

- [ ] **Step 5: Edit its contents** so the `job_secrets` `exclude` list is Jinja-composed from the enabled toggles (keep the existing web entries under `{% if include_web %}`):

```jinja
# ghalint policy overrides — jobs that must expose secrets at job-env because
# GitHub `if:` cannot read the `secrets` context.
excludes:
  - policy_name: job_secrets
    jobs:
{% if include_web %}
      - docker-publish-preflight
      - docker-publish
{% endif %}
{% if include_homebrew %}
      - publish-homebrew
{% endif %}
{% if include_scoop %}
      - publish-scoop
{% endif %}
```

> Implementer: match the exact ghalint schema/keys shown by Step 3 (the real key names may differ from this sketch — preserve them).

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_distribution.py -k ghalint -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add -A template/.github/
git commit -m "chore: extend ghalint job_secrets exclusion to publish-homebrew/scoop"
```

---

### Task 9: Full verification + example regen

**Files:**
- Modify (regen): `example/` (gitignored — not committed)
- Modify (if typos flags Ruby/JSON tokens): `_typos.toml`

**Interfaces:** none — this task proves the whole feature renders + lints clean.

- [ ] **Step 1: Run the full repo-level test suite**

Run: `uv run pytest tests/ -v`
Expected: all green (existing + new `test_distribution.py`).

- [ ] **Step 2: Render the three representative app combinations**

```bash
copier copy --data-file .example-input.yml --data preset=full --defaults --trust . /tmp/dist-full --force
copier copy --data-file .example-input.yml --data include_cli=true --data include_homebrew=true --defaults --trust . /tmp/dist-brew-pypi --force
copier copy --data-file .example-input.yml --data include_cli=true --data include_scoop=true --data include_compiler=true --defaults --trust . /tmp/dist-scoop-bin --force
```

- [ ] **Step 3: Lint + zizmor + ghalint on the full render** (`git init` first so ruff/zizmor see a repo):

```bash
cd /tmp/dist-full && git init -q && git add -A
uv run --locked tox run -e style
prek run zizmor --all-files
prek run --all-files   # runs the ghalint local hook + actionlint/yamllint
cd -
```
Expected: green. If ghalint complains the publish jobs still trip `job_secrets`, fix the exclusion keys (Task 8 Step 5) to match the real schema and re-run.

- [ ] **Step 4: Handle any `typos` findings** — if the Ruby/JSON `.tmpl` trip `typos` (e.g. `libexec`, `venv`), add narrow allowances to `_typos.toml` (root) and `template/_typos.toml` if the generated project also flags them. Re-run `prek run --all-files`.

- [ ] **Step 5: Regenerate the committed example** (library preset — should show NO brew/scoop artifacts, proving `when: is_app` gating):

```bash
copier copy --data-file .example-input.yml --defaults . example/ --force
test ! -e example/.github/packaging && echo "OK: no packaging in library example"
```

- [ ] **Step 6: Final full-suite pass + commit any config fixes**

```bash
uv run pytest tests/ -q
git add _typos.toml template/_typos.toml 2>/dev/null; git commit -m "chore: allow packaging-template tokens in typos config" || echo "no typos changes"
```

---

## Self-Review (completed during authoring)

**Spec coverage:** toggles+preset+`primary_executable` → Task 1; README/installation docs → Task 2; CONTRIBUTING setup → Task 3; ADR-017 + CLAUDE.md → Task 4; formula/manifest binary+PyPI paths → Task 5; publish jobs (in `release.yml`, `needs: finalize-release`, gated-on-secret) → Tasks 6-7; ghalint exclusion → Task 8; single-arch + Scoop-fallback limitations → documented in ADR (Task 4); verification across combos → Task 9. All spec sections mapped.

**Type/name consistency:** secret names `HOMEBREW_TAP_TOKEN`/`SCOOP_BUCKET_TOKEN`, repos `homebrew-tap`/`scoop-bucket`, `primary_executable` values `freezer|compiler|launcher|""`, asset names `{{github_repo_name}}-{{primary_executable}}-{macos,linux,windows}[.exe]`, placeholder set `@@VERSION@@/@@URL_*@@/@@SHA256_*@@/@@SDIST_*@@` — used identically across Tasks 5-7.

**Known deviation from spec (intentional, noted in Global Constraints):** target repo names are the conventional `homebrew-tap`/`scoop-bucket` (spec wrote `homebrew-<name>` as a placeholder).
