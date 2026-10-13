# Standalone executables

## Three architecture-named executable toggles instead of one brand toggle

**Id:** d5aed1a0-0b7c-4ac3-9d75-fb9568d9e34d
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-007 ([`docs/adr/007-standalone-executable-toggles.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/007-standalone-executable-toggles.md))
**Revisit when:** a fourth standalone-executable architecture appears, or a category's strongest tool changes

`include_launcher` (PyCrucible, uv-bootstrap launcher), `include_compiler`
(Nuitka, source-to-machine-code) and `include_freezer` (PyInstaller,
interpreter-plus-deps bundle) replace the single `include_pycrucible` toggle.
All three default to `false` outside the `full` preset, which turns them on, and
combine freely; there is no `when:` gating and no mutually exclusive choice.

**Reason:** the single toggle conflated a brand with a capability and covered
one of three architectures that make materially different promises — a tiny
online-first-run launcher, a compiled native binary, a fully offline bundle — and
that a project may legitimately want together (a launcher for connected users
and an offline bundle for air-gapped ones). Naming the architecture rather than
the tool means swapping PyCrucible for PyApp later needs no variable rename.

**Rejected alternative:** one `executable_tool` enum — forces mutual exclusion
that is wrong for these categories and blocks adding a fourth later.

**Rejected alternative:** PyApp or UVBox — same launcher category as
PyCrucible, lateral not new capability. cx_Freeze and py2exe — weaker freezers
(py2exe Windows-only). mypyc — module-level, not whole-app. Briefcase — targets
native installers and GUI/mobile packaging, out of scope for a single-file
executable. PyOxidizer — archived.

**Consequence:** a breaking rename for existing answers files with no automatic
migration (Copier does not rename variables). Build dependencies live in the uv
`tool` group and are Renovate-tracked like every other pin. Each toggle must be
exercised independently and in combination.

## Executables are named per tool and OS and all target the package main module

**Id:** 1b37b4df-147f-4d71-8249-4003ecfe4302
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-007 ([`docs/adr/007-standalone-executable-toggles.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/007-standalone-executable-toggles.md))
**Revisit when:** `attach-github-release` stops flattening downloaded artifacts by filename, or component selection moves out of `__main__.py`

Each build names its binary `<pkg>-<tool>-<os-label>` rather than a bare
`<pkg>`. All three builds target the package's `__main__.py`, which was
generalized from a CLI-only form into the single entry that selects and
launches whichever component is enabled; with an executable toggle on but no
runnable component selected, `main()` raises a `SystemExit` with an
explanatory message.

**Reason:** the release job collects every executable artifact with
`merge-multiple`, which flattens by filename — bare names made per-OS (and,
with more than one toggle, per-tool) binaries silently overwrite each other and
drop platforms from the release. One entrypoint keeps the PyInstaller spec, the
Nuitka command and the PyCrucible config free of duplicated component
conditionals and guarantees the binary *runs* the app rather than importing a
module that never invokes it. A binary that builds and exits non-zero with a
reason beats one that silently does nothing and looks broken.

**Consequence:** PyCrucible takes the name via its output option, Nuitka via
`--output-filename` (otherwise a generic `__main__.bin`), PyInstaller is renamed
after the build because its spec cannot see the CI matrix. The PyInstaller spec
is rendered for reproducible builds and un-ignored in the generated
`.gitignore` (the default `*.spec` ignore would keep it uncommitted and break
the fresh-checkout release build); Nuitka's flags live in the mise task and CI
step since it has no spec equivalent. The mise `package` task was split per
architecture, which also fixed a latent bug where the whole `mise.toml` body
sat in one raw block and rendered the PyCrucible task regardless of the toggle.

## Every executable toggle adds a PR-time build-check job

**Id:** 69443ac8-be5b-401a-b45d-53d19c54045c
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-007 ([`docs/adr/007-standalone-executable-toggles.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/007-standalone-executable-toggles.md))
**Revisit when:** the test suite starts exercising the built binary, or the per-OS build cost outweighs the signal

Each enabled toggle renders a per-OS, `fail-fast: false` `build-<tool>-check`
job in `ci.yml` that builds the executable on every push and pull request,
verifies the binary was produced, smoke-runs it with `--help` for a CLI
project, uploads a short-retention preview artifact and gates the `check` job.
It mirrors the release build commands but never publishes.

**Reason:** the test suite always runs the source tree, never the built
binary, so a dependency or Python bump that breaks packaging would otherwise
fail silently at release time instead of against the offending diff.

**Rejected alternative:** build only at release time — the previous state.
