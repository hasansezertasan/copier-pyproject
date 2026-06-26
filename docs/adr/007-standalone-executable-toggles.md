# ADR-007: Three independent standalone-executable toggles (launcher / compiler / freezer)

## Status

Accepted (2026-06). Supersedes the original single `include_pycrucible` toggle.

## Context

The template originally shipped one optional standalone-executable path:
`include_pycrucible`.
[PyCrucible](https://github.com/razorblade23/PyCrucible) is **not** a freezer in
the PyInstaller sense — it produces a small (~2 MB) Rust *launcher* that embeds
the project as a zip and bootstraps [`uv`](https://docs.astral.sh/uv/) at
**runtime**. On first run it downloads a Python interpreter and the project's
dependencies through `uv`; later runs start instantly from the populated cache.

That single toggle conflated a brand with a capability, and it covered only one
of the three architectures the standalone-executable ecosystem actually splits
into (see
[awesome-python-standalone](https://github.com/hasansezertasan/awesome-python-standalone)):

| Architecture | Example tools | Runtime promise |
|--------------|---------------|-----------------|
| **launcher** (uv-bootstrap) | **PyCrucible**, PyApp, UVBox | tiny binary; downloads Python+deps on first run; needs network once |
| **compiler** (source→machine code) | **Nuitka** | compiles to C/native; faster startup + some obfuscation; needs a C toolchain to build |
| **freezer** (bundle interpreter+deps) | **PyInstaller**, cx_Freeze, py2exe | ships interpreter+stdlib+deps in one artifact; fully offline; no Python on target |

These are not substitutes — they make materially different promises (online
launcher vs. compiled native binary vs. offline bundle), and a project may
reasonably want more than one (a small launcher for connected users *and* an
offline bundle for air-gapped distribution).

## Decision

Replace the single `include_pycrucible` toggle with **three independent boolean
toggles**, one per architecture, each mapped to the strongest representative
tool of its category:

| Toggle | Tool | Category |
|--------|------|----------|
| `include_launcher` | [PyCrucible](https://github.com/razorblade23/PyCrucible) | uv-bootstrap launcher |
| `include_compiler` | [Nuitka](https://nuitka.net/) | source→machine-code compiler |
| `include_freezer` | [PyInstaller](https://pyinstaller.org/) | interpreter+deps freezer |

All three default to `false` and are freely combinable — there is no `when:`
gating and no mutually-exclusive choice variable. The toggle name describes the
*architecture*, not the brand, so swapping the underlying tool later (e.g.
PyCrucible→PyApp) does not require renaming the variable.

### Why architecture-named booleans instead of one `executable_tool` enum

An enum would force the three paths to be mutually exclusive, which is wrong:
they solve different problems and legitimately coexist. Independent booleans also
keep the door open to add a fourth architecture later without restructuring.

### Why these three tools

- **PyCrucible** for *launcher* — already in use; smallest artifact; always-current
  interpreter/deps; trivial CI step. Its true peers (PyApp, UVBox) are the same
  category, so adding them would be lateral, not new capability.
- **Nuitka** for *compiler* — the mature compile-to-C option; gives runtime speed
  and source obfuscation that neither a launcher nor a freezer provides. (mypyc
  is narrower — module-level, not whole-app — so it loses here.)
- **PyInstaller** for *freezer* — the de-facto standard offline bundler: widest
  ecosystem, GUI support, `.spec`-file reproducibility. cx_Freeze and py2exe are
  weaker (smaller community; py2exe is Windows-only) with no upside over it.

### Rejected for the categories we cover

- **PyApp / UVBox** — same launcher category as PyCrucible.
- **cx_Freeze / py2exe** — weaker freezers than PyInstaller.
- **Briefcase** — targets native app *installers* (`.app`/`.msi`/`.dmg`) and
  GUI/mobile packaging; larger surface, out of scope for "single-file executable".
- **PyOxidizer** — archived/unmaintained.

## Consequences

- `include_pycrucible` is **renamed** to `include_launcher`. This is a breaking
  rename for existing answers files; there is no automatic migration (Copier does
  not rename variables), so a `copier update` of a project that had
  `include_pycrucible: true` must set `include_launcher: true`.
- Two new toggles, `include_compiler` (Nuitka) and `include_freezer`
  (PyInstaller), join it. With all three `false` (the default) nothing changes.
- Build dependencies live in the uv-managed `tool` dependency group alongside the
  existing profiling/Cython tooling, kept current by Renovate like every other
  pin — consistent with [ADR-003](003-tox-as-canonical-lint-runner.md)'s
  single-source-of-truth stance.
- The release workflow gains a `build-freezer` (PyInstaller) and a
  `build-compiler` (Nuitka) matrix job (Ubuntu/Windows/macOS, `fail-fast: false`)
  next to the renamed `build-launcher` (PyCrucible) job; all three are
  independent and their artifacts are attached to the still-draft release by
  `attach-github-release`. See [ADR-002](002-release-please-for-release-automation.md).
- Each build names its binary `<pkg>-<tool>-<os-label>` (e.g.
  `myapp-compiler-linux`, `myapp-freezer-windows.exe`) rather than a bare
  `<pkg>`. This is required for correctness, not cosmetics: `attach-github-release`
  collects every executable artifact with `download-artifact`'s `merge-multiple`,
  which flattens them into one directory by *filename*. Without the `<tool>-<os>`
  qualifier the per-OS binaries (and, with more than one toggle, the per-tool
  binaries) share a name and silently overwrite each other, dropping platforms
  from the release. PyCrucible takes the name via `-o`/`output:`, Nuitka via
  `--output-filename` (it otherwise emits a generic `__main__.bin`), and
  PyInstaller — whose `.spec` `name=` can't see the CI matrix — is renamed after
  the build.
- All three builds target the package's `__main__.py` as their single runnable
  entrypoint, so the component-selection logic (CLI/GUI/TUI/web/MCP/worker → the
  callable that actually launches the app) lives in `__main__.py` and nowhere
  else. `__main__.py` is generalized from the previous CLI-only form into a
  universal entry that defines/imports a `main()` for whichever component is
  enabled. This keeps the spec, the Nuitka command, and `[tool.pycrucible]` free
  of duplicated entrypoint conditionals, and — critically — ensures the produced
  binary *runs* the app rather than merely importing a module that defines but
  never invokes it. Enabling an executable toggle with no runnable component
  (CLI/GUI/TUI/web/MCP/worker) selected is a degenerate but allowed combination:
  `__main__.main()` falls back to a no-op body, so the produced binary builds and
  runs but does nothing.
- For PyInstaller a `{{github_repo_name}}.spec.jinja` is rendered for a
  reproducible, editable build, and the generated `.gitignore` un-ignores that
  one spec (the default `*.spec` ignore would otherwise keep it uncommitted and
  break the release workflow's fresh-checkout build); Nuitka's flags live in the
  mise task and the CI step (Nuitka has no spec-file equivalent); PyCrucible
  keeps its `[tool.pycrucible]` config block.
- The mise `package` task is split into per-architecture tasks
  (`package`/`compile`/`freeze`) each properly gated. This also fixes a latent
  bug: `mise.toml.jinja` wrapped its whole body in one `{% raw %}` block, so the
  PyCrucible task previously rendered even when the toggle was off.
- More template surface to test: each toggle must be exercised independently and
  in combination, the way `worker_broker` is tested across brokers.
