# hatch-vcs archival version support

**Issue:** [#122](https://github.com/hasansezertasan/copier-pyproject/issues/122)
**Date:** 2026-08-03

## Problem

`template/pyproject.toml.jinja` configures hatch-vcs with a hard-coded literal
fallback:

```toml
[tool.hatch.version]
source = "vcs"
fallback-version = "0.1.0"
```

The generated `docs/installation.rst.jinja` documents installing from a GitHub
source tarball (`https://github.com/<user>/<repo>/tarball/main`). That archive
contains **no `.git` directory**, so hatch-vcs (via setuptools-scm) cannot derive
a version and substitutes the literal `fallback-version`. Once a project passes
`0.1.0`, every tarball/sdist-from-archive install keeps reporting `0.1.0` in
`<pkg> version`, dependency resolution, and diagnostics — a silent
misreport.

## Fix

Adopt setuptools-scm's canonical **git archive support** mechanism (hatch-vcs
delegates version resolution to setuptools-scm, which reads `.git_archival.txt`).
GitHub's tarball/archive generation honors `.gitattributes export-subst`, so the
placeholders below are expanded to the real commit hash, date, and
`git describe` output at archive-creation time.

### 1. New file `template/.git_archival.txt.jinja`

Stable content (the setuptools-scm-recommended form for releases):

```
node: $Format:%H$
node-date: $Format:%cI$
describe-name: $Format:%(describe:tags=true,match=*[0-9]*)$
```

- The `*[0-9]*` match pattern catches release-please's `v1.2.3` tags.
- In a normal git checkout the literal `$Format:...$` strings remain unexpanded;
  setuptools-scm detects this and ignores the file, falling back to live git
  metadata. So the file is safe to commit and ship.
- No Jinja variables are needed inside the file, but it carries the `.jinja`
  extension for consistency with the template's rendering pipeline (Copier renders
  it verbatim).

### 2. `template/.gitattributes.jinja`

Add, in the language/normalization region (**above** the `export-ignore` block):

```
.git_archival.txt export-subst
```

`.git_archival.txt` must **not** be added to the `export-ignore` list — it has to
ship *inside* the archive for the expanded values to reach the installed package.

### 3. `template/pyproject.toml.jinja`

Change the fallback from a plausible-looking early release to an obvious
"unknown" sentinel:

```toml
fallback-version = "0.0.0"
```

The fallback is kept (not removed): it is still the required last resort when an
archive is taken from a commit with no reachable tag. `0.0.0` reads clearly as
"version could not be determined" rather than masquerading as a real release.

## Non-goals

- No new `copier.yml` option — archival support is always-on, like the existing
  hatch-vcs setup.
- No change to the release/sdist build path (`uv build` runs against a real git
  checkout and already resolves versions correctly).
- `installation.rst.jinja` needs no change — the documented tarball flow simply
  becomes correct.

## Verification

1. Regenerate the example:
   `copier copy --data-file .example-input.yml --defaults . example/ --force`
2. `cd example && uv run --locked tox run -e style`
   (validate-pyproject, taplo, editorconfig-checker must pass).
3. Confirm placeholder expansion against a real archive:
   `git -C example archive HEAD | tar -xO .git_archival.txt` shows expanded
   `node:`/`describe-name:` values (not literal `$Format:...$`).
