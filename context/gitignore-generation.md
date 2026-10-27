# .gitignore generation

## cobo generates the gitignore with a hash-sealed fence and lockfiles

**Id:** 3e3bc38e-bc1e-4e65-b74d-e91848262157
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** ADR-012 ([`docs/adr/012-cobo-for-gitignore-generation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/012-cobo-for-gitignore-generation.md))
**Revisit when:** `github/gitignore` stops being the boilerplate source, or cobo changes its fence or lock format
**See:** ci-topology.md#network-dependent-checks-run-on-a-weekly-cron-never-in-the-merge-gate — 3e5b9525-9087-4125-b19f-80f6c226c01f — as of 2026-10-11

cobo fetches the same `github/gitignore` boilerplates the previous gibo
workflow stacked, but writes them inside a sha256-sealed fence and records the
upstream commit and per-file blobs in `cobo.lock`. The repository root lock
carries two fragments — the template source and this repository's own
`.gitignore` (dogfooding) — and `template/cobo.lock` ships verbatim so a
generated project's gitignore is drift-checkable. cobo is always-included
tooling (a mise `pipx:` tool, Renovate-tracked), with no toggle. The project's
own overrides (the freezer spec negation, the C-extension ignore) sit below the
end fence, where cobo preserves them; the negation still lands after the fenced
`*.spec` ignore, so it wins.

**Reason:** gibo was run by hand with no lockfile, no pin the tooling
understood and no way to detect upstream drift, and the overrides were injected
inside the boilerplate it generated.

**Rejected alternative:** keep gibo — the gaps above.

**Consequence:** the cobo-managed `.gitignore` is excluded from the
`trailing-whitespace` hook, because upstream ships trailing whitespace on some
comment lines and trimming inside the fence breaks the seal; `cobo.lock` is
`linguist-generated` and carries its own 2-space EditorConfig stanza (taplo's
`*.toml` glob does not cover `.lock`). Regeneration is `cobo update` followed
by `cobo sync`; a hand edit inside the fence breaks the sha256.

## The seal keeps the two macOS CR patterns; the render still strips them

**Id:** a5df0a9c-aa53-4a8c-add6-566326352a0e
**Type:** decision
**Type:** workaround
**Status:** superseded
**Superseded by:** 61324e22-356d-42aa-b16c-5afbc89185f4
**Evidence:** confirmed
**Source:** ADR-012 §1 ([`docs/adr/012-cobo-for-gitignore-generation.md`](https://github.com/hasansezertasan/copier-pyproject/blob/c06222e28adb395637f4a2c7cdbe68dd39c39bb7/docs/adr/012-cobo-for-gitignore-generation.md)); cobo#120/#121 (the upstreamed `--eol lf` policy), [cobo#124](https://github.com/hasansezertasan/cobo/issues/124), [issue #111](https://github.com/hasansezertasan/copier-pyproject/issues/111), [issue #393](https://github.com/hasansezertasan/copier-pyproject/issues/393)
**Revisit when:** the Copier render preserves a lone carriage return in this file (the cobo half — normalize terminators only, not a mid-line CR — already shipped in cobo 0.6.0)

The fence is sealed with cobo's `--eol lf` policy, persisted as `eol = "lf"` on
the lock fragment. Since cobo 0.6.0 that policy normalizes terminators only
(`CRLF` → `LF`) and keeps a mid-line lone CR — so the sealed
`template/.gitignore` carries the macOS boilerplate's two carriage-return
filenames (`Icon␍`, `.HFS+ Private Directory Data␍`) byte-intact, and the old
"seal LF-normalizes them into `Icon[`/`]`" description is stale. The corruption
moved one stage down the pipeline: Copier renders `.gitignore.jinja` through
Jinja, whose lexer normalizes a lone `\r` to `\n` at scaffold time (verified by
rendering a CR-bearing probe template with the pinned copier). Every rendered
project therefore still checks out the split `Icon[` (unterminated class,
matches nothing, inert) / `]` (a literal pattern matching a file or directory
named `]` at any depth — a non-issue in practice, and no post-fence `!]`
override: it would stamp noise on every generated project for a filename that
essentially never exists) pair — and, because the fence sha256 covers the
CR-bearing bytes, additionally reports `up to date; locally modified` on
`cobo check`. An up-to-date `cobo sync` still succeeds as a no-op, but a later
sync that must apply upstream drift fails without `--force` on the
locally-modified block — until fence verification tolerates the
render-stripped CR (verified by rendering the template and running
`cobo check` and `cobo sync` against the shipped lock).

**Reason:** the template enforces LF everywhere (`.gitattributes`,
EditorConfig, ruff) and there is no LF-only pattern that matches `Icon␍`
precisely (`Icon?` over-matches), so fidelity genuinely requires the CR, and
the CR cannot survive the Jinja render. These are legacy HFS resource-fork
artifacts modern macOS rarely creates and almost never commits — an accepted
tradeoff, not "harmless".

**Rejected alternative:** seal byte-exact and keep the CR — fights the LF
invariant and is re-corrupted by the render anyway.

**Consequence:** the remaining fix is render-side or check-side, not
seal-side: either a Copier/Jinja newline carve-out scoped to this file, or
cobo fence verification that treats a render-stripped lone CR as clean under
`eol = "lf"`. Until then, refreshes come from a template-side `cobo sync`,
never from a local `cobo dump` in a generated project (whose bytes
`copier update` can never reproduce) — that rule is recorded in the NOTE below
the fence in `template/.gitignore`.

## The sealed `.gitignore` ships as a plain, unrendered file

**Id:** 61324e22-356d-42aa-b16c-5afbc89185f4
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [cobo#243](https://github.com/hasansezertasan/cobo/issues/243) (closed as won't-fix cobo-side; the fix is the consumer shipping the file unrendered), maintainer conversation 2026-10-27; the sibling `copier-copier` template already ships a plain `template/.gitignore` with both CRs intact
**Revisit when:** the sealed block needs a value only a render can supply, or Copier preserves a lone carriage return in rendered files
**See:** gitignore-generation.md#the-seal-keeps-the-two-macos-cr-patterns-the-render-still-strips-them — a5df0a9c-aa53-4a8c-add6-566326352a0e — as of 2026-10-27

`template/.gitignore` has no `.jinja` suffix and no Jinja syntax, so Copier copies
it byte for byte and the macOS boilerplate's two lone-CR classes (`Icon␍`,
`.HFS+ Private Directory Data␍`) reach the generated project intact; the
`eol = "lf"` seal verifies there as is. The cause was never the seal: Jinja's
lexer rewrites a lone `\r` to `\n` in any file it renders, and this one never
needed rendering. To make that true, the author section below the fence lost its
toggle-conditional lines and became name-independent and unconditional:
`!/*.spec` (was `!{{pkg}}.spec`), `/src/*/_c_extension.c`, and the `docs/_generated/`
and `docs/_static/versions.json` rules without their `include_docs`/component
guards. The cost is a few inert ignore lines in projects that do not use those
features, the same trade as the always-on Node/GitHubPages fragments; dropping
the `docs/_generated/` guard also removes the condition that drifted from
`conf.py`'s generator guard in #299.

**Reason:** the fix belongs where the corruption happens. cobo normalizes
terminators only and keeps the CR on purpose, because `Icon[]` (the CR stripped
at seal time) ignores nothing; trading seal correctness for one renderer was
cobo's rejected option (its `lf-strict` policy, cobo#249). Every sibling `copier-*`
template seeds its cobo-managed `.gitignore` once as a plain file.

**Rejected alternative:** keep `.gitignore.jinja` and write the CRs as `{{ "\r" }}`
expressions — the rendered output is right but the template source then fails its
own `cobo check`, breaking the dogfooded lock fragment. Also rejected: a `_tasks`
step running `cobo gitignore dump` (forces `--trust`; see the no-`_tasks`
invariant) and accepting the permanently "locally modified" block (a later
`cobo sync` with real upstream drift would need `--force`).

**Consequence:** a plain `template/.gitignore` is also a live ignore file for the
`template/` tree itself, so the sealed Node `.env.*` and `.vscode/*` rules hide
`template/.env.example.jinja` and `template/.vscode/*.json.jinja` from Copier's
file enumeration (verified by diffing the rendered file sets). Exact negations
below the fence (`!/.env.example.jinja`, `!/.vscode/*.jinja`) rescue them and
render as inert lines into generated projects; a blanket `!*.jinja` was
rejected because it would also make a stray `.env.production.jinja` trackable
there. `tests/test_sealed_gitignore.py` guards the CRs, the verbatim copy, those
rescues and that no tracked template file is ignored. Refreshes follow the
[both-lockfiles procedure](../docs/template-architecture.md); the root
`cobo.lock` fragment now tracks `template/.gitignore`.

## Node and GitHubPages ride always-on in the seal

**Id:** 00d055c4-152a-4b0d-b0b6-a8ecf6bdc557
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [issue #393](https://github.com/hasansezertasan/copier-pyproject/issues/393)
**Revisit when:** a fragment arrives that only a subset of generated projects can use without tripping their drift check

The seal pins seven `github/gitignore` boilerplates
(`macOS`, `Windows`, `Linux`, `VisualStudioCode`, `Python`, `Node`,
`GitHubPages` @ `0e5d690`) — unconditionally, with no toggle. Downstream
projects that publish docs to Pages or touch any JS tooling used to hand-add
`Node` + `GitHubPages` ad hoc and diverge from the template until the next
`copier update` clobbered them.

**Reason:** a fragment gated on a toggle (e.g. `GitHubPages` on
`include_docs`) would need a Jinja-conditional seal *and* a Jinja-templated
`cobo.lock`, with drift-check edge cases for every answers combination; the
`VisualStudioCode` precedent already established that always-on is acceptable.
Deciding once here beats every project hand-editing the seal.

**Rejected alternative:** gate `GitHubPages` on `include_docs` — leaner seal
for non-docs projects, rejected for the lock-templating complexity above.

**Consequence:** the refresh re-pinned `57286c3` → `0e5d690` at the same time
(only `Python.gitignore` had changed upstream: `UV` → `uv`, mkdocs/Zensical,
a VSCode comment rewrap). Both root-lock fragments (`template/.gitignore`
and the dogfooded repo `.gitignore`) carry the same seven files, and
`template/cobo.lock` ships the same set to generated projects. The pin refresh
also surfaced the seal-keeps/render-strips CR split above, whose check-side
follow-up lives in the cobo tracker, not here.

**Consequence:** a sealed pattern can also match a *template source* file:
copier honors the worktree gitignore when enumerating `template/`, so the
sealed Node `.env.*` silently dropped `.env.example` from fresh renders (its
`!.env.example` rescue misses the `.jinja` suffix). A collision with the
repo-root `.gitignore` gets a below-fence negation in its author section (never
inside the fence) — here, `!/template/.env.example.jinja`. A collision with
`template/.gitignore`'s own rules cannot be overridden from the root (the nested
file wins), so its exact negation goes below that file's fence instead, and
renders into generated projects as an inert line.

## `copier update` leaves the cobo-managed `.gitignore` and lock alone; adoption still renders them

**Id:** cecafff6-ea1b-4821-942f-30e9c5c6e489
**Type:** decision
**Status:** active
**Evidence:** inferred
**Source:** maintainer conversation, 2026-10-24 (all copier-* templates seed the cobo-managed files once); `copier/_main.py` in copier 9.18.2 and `tests/test_copier_exclude.py`
**Revisit when:** copier renders `_skip_if_exists` patterns with `_copier_operation`, or the generated `cobo.lock` tracks more than `.gitignore`
**See:** gitignore-generation.md#cobo-generates-the-gitignore-with-a-hash-sealed-fence-and-lockfiles — 3e3bc38e-bc1e-4e65-b74d-e91848262157 — as of 2026-10-24

`copier.yml` lists `.gitignore` and `cobo.lock` in `_exclude`, each wrapped in
`{% if _copier_operation == 'update' %}…{% endif %}`. A generated project owns
both after the first render: cobo rewrites the sealed block and the lock, so a
`copier update` three-way merge of the template's copies would conflict with it.
Adoption (`copier copy --overwrite`) still renders both, as a matched pair.
`.gitattributes` and `.editorconfig` are not listed: the generated `cobo.lock`
tracks only `.gitignore`, so nothing else would refresh them.

**Reason:** the user's other copier templates seed the cobo files once, and the
update flow is the only place the merge hurts.

**Rejected alternative:** an unconditional `_skip_if_exists`, as the other
templates use. Copier renders its patterns without `_copier_operation`, so it
cannot be limited to updates, and the adoption copy would keep an existing
`.gitignore` beside the template's fresh `cobo.lock` (`cobo check --strict`
fails).

**Consequence:** `copier update` does not restore a deleted file: the exclusion
prevents rendering even when the file is absent. A project that deletes one of
the two is left with an incomplete pair and must restore the missing file itself
(`cobo gitignore dump … --lock` rebuilds both), but the two cannot be reseeded
out of step. Template changes to the template's `.gitignore` reach existing
projects only through cobo's own updates.
