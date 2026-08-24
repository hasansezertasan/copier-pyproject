# ADR-028: No empty `all` extra — component deps are core dependencies

## Status

Proposed (2026-08).

## Context

Generated projects once declared a per-component optional extra (`web`, `gui`,
`worker`, ...) and an aggregate `all` extra that pulled them in. That model was
already abandoned: a component is chosen at *generation* time, and the rendered
`__main__` imports it unconditionally, so `pip install <pkg>` must pull its
runtime dependency or the console script fails at launch. Every component's deps
therefore moved into the core `[project] dependencies` list.

What survived the move was the shell:

- `[project.optional-dependencies]` with a single, permanently empty `all = []`;
- `<pkg>[all]` in the `dev` dependency group;
- `extras = ["all"]` on six tox settings — `env_run_base` (inherited by the
  per-version test envs and by `prek`/`profile`/`cli`/`worker`), `style`,
  `docs-build`, `docs-server`, `docs-linkcheck`, and `integration`;
- `uv run --no-default-groups --extra all --group docs …` in four docs workflows.

None of it installed anything. Worse, it was actively misleading: the `style`
env carried a comment claiming optional components "are only importable when
their extra is installed", ADR-006 stated that dropping `extras = ["all"]` would
break `.. automodule:: pkg.web.app`, and ADR-008 justified eager broker imports
on the grounds that "every test/tox environment installs `extras = ["all"]` (so
the driver is always present)". All three described a mechanism that had stopped
doing any work — the deps were present because they were *core*, not because of
the extra. A reader auditing the packaging would have drawn the wrong conclusion
about what guarantees what.

The counter-argument for keeping it: a pre-wired seam. An adopter who later
wants a genuinely optional dependency adds one line to `all = []` instead of
editing the dev group and six tox envs.

## Decision

**Remove the `all` extra and every reference to it.** Generated projects ship no
`[project.optional-dependencies]` table at all.

- `all = []` and its comment block are deleted from `pyproject.toml.jinja`.
- The `dev` group's `<pkg>[all]` self-reference is dropped entirely (rather than
  reduced to `<pkg>`): `uv sync` and tox's own packaging install the project, so
  the self-reference was redundant even before the extra emptied out.
- All six `extras = ["all"]` tox settings are removed (including the
  `env_run_base` one every test env inherited). Each env still installs the
  project itself, which is what actually supplied the dependencies.
- The four docs workflows drop `--extra all`; `uv run --no-default-groups
  --group docs …` still installs the project.

The seam argument does not survive contact with the misleading-documentation
cost. A one-time 8-site edit *if* an adopter ever needs an extra is cheaper than
a permanent empty declaration that three separate documents cite as load-bearing.

## Consequences

- **`uv run --extra all` in an adopter's own scripts breaks.** A `copier update`
  hazard for any project that hand-added such a call; the remedy is to delete
  the flag.
- **The adopter must re-lock.** Removing the extra and the `<pkg>[all]` dev
  entry changes the project metadata `uv.lock` records
  (`[package.optional-dependencies]`, `[package.metadata.requires-dev]`), so a
  committed lockfile goes stale the moment the copier-update PR lands. Renovate's
  copier manager re-renders but does not re-lock, and CI, the `prek` system
  hooks, and the `mise` tasks all use `uv run --locked` — which hard-fails on a
  stale lockfile, so the update PR is red until someone runs `uv lock`. Applying
  this update means running `uv lock` and committing the result in the same PR;
  `docs/maintaining/setup.rst` now states this for copier updates generally.
- **Adding a real optional extra is now an explicit act.** Re-introducing one
  means declaring the extra, adding it to the dev group, and adding `extras` to
  whichever tox envs genuinely need it — which is the correct blast radius to
  reason about, rather than inheriting `all` everywhere by default.
- **ADR-006 and ADR-008 are corrected**, not just edited around: both now
  attribute dependency availability to core `dependencies`. ADR-008's revision
  note about lazy broker imports reaches the same conclusion by the accurate
  route.
- **The invariant to preserve:** a runnable component's runtime dependency
  belongs in the core `dependencies` list under its `{% if include_x %}` guard.
  Do not reach for an extra — see `CLAUDE.md`, "Adding New Optional Components".
