# Supply-chain security

## Provenance minting shares the protected publication boundary

**Id:** a0396603-cb34-4151-9d5b-1fc77eb31f6e
**Type:** decision
**Type:** constraint
**Status:** active
**Evidence:** confirmed
**Source:** [issue #185](https://github.com/hasansezertasan/copier-pyproject/issues/185), [PR #318](https://github.com/hasansezertasan/copier-pyproject/pull/318), review discussions on [private availability](https://github.com/hasansezertasan/copier-pyproject/pull/318#discussion_r4065991055) and [the trust boundary](https://github.com/hasansezertasan/copier-pyproject/pull/318#discussion_r4065991056); commit [cc7ce42](https://github.com/hasansezertasan/copier-pyproject/commit/cc7ce42b91d56a0a75901606f93e29afa0315ceb)
**Verification:** corroborated — the release build uses the `publish` environment, includes gated attestation steps and per-platform bundles, and installation docs constrain signer workflow and ref
**Revisit when:** attestation availability, signer verification, or the publishing environment's branch policy changes

The release build attests the distributions it produces and retains the
provenance bundles alongside the release artifacts. Matrix builds attest their
own outputs. Attestation minting runs behind the same externally protected
`publish` environment as package publication, with a main-only deployment policy
configured during repository setup. Referencing the environment in workflow
source alone does not prove that an adopter configured its live policy.
Consumer verification identifies
the release workflow and the `main` ref, not only the repository. The workflow
enables attestation for public repositories and requires explicit opt-in for
private ones.

**Reason:** repository identity alone does not prove that the intended protected
release workflow built an artifact. A branch-dispatched workflow could otherwise
mint repository-backed attestations for arbitrary outputs. GitHub evaluates the
environment's deployment policy outside the dispatched workflow file, so that
boundary also protects provenance minting. The private opt-in avoids breaking
releases on plans without the necessary attestation support.

**Rejected alternative:** leave minting in an unprotected build job and verify
only repository identity. Review rejected this weaker trust boundary.

**Rejected alternative:** attempt attestations unconditionally on private
repositories. Review required explicit opt-in to preserve unsupported private
release paths.

[ADR-002](002-release-please-for-release-automation.md) records why manual release
dispatch remains necessary and why the environment must have a main-only policy.
The verification procedure is in generated `docs/installation.rst`; this entry
records why its signer constraints and the minting boundary exist.

## Relationship between GitHub provenance and PyPI attestations

**Id:** 09b24722-bfa5-460a-bbd7-05d8973b5389
**Type:** decision
**Status:** superseded
**Evidence:** unknown
**Source:** [issue #185](https://github.com/hasansezertasan/copier-pyproject/issues/185), PyPI-side integration question; [PR #318](https://github.com/hasansezertasan/copier-pyproject/pull/318)
**Verification:** uncorroborated — the reviewed sources establish the explicit GitHub provenance path, but no resolution of the PyPI-side overlap question was found
**See:** supply-chain-security.md#provenance-minting-shares-the-protected-publication-boundary — a0396603-cb34-4151-9d5b-1fc77eb31f6e — as of 2026-10-08
**Superseded by:** f5495121-8004-4652-b3ac-af71995c263a

The proposal asked whether the trusted-publishing action's PEP 740 attestations
make the explicit GitHub provenance step partly redundant, or whether both paths
serve a deliberate belt-and-suspenders purpose. The implementation retains the
GitHub path, but the rationale for its relationship to PyPI-side attestations
could not be recovered. No historical reason for keeping both was established;
this was not a finding that either mechanism was defective or safe to remove.

The current decision below resolves the configuration choice from verified
technical differences. It does not turn that new justification into a claim
about the original implementation's intent.

## Retain build provenance and publication attestations as distinct claims

**Id:** f5495121-8004-4652-b3ac-af71995c263a
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** current attestation review, 2026-10-08; [PyPI Publish predicate](https://docs.pypi.org/attestations/publish/v1/), [PyPI attestation production](https://docs.pypi.org/attestations/producing-attestations/), [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations); pinned PyPI action [dc37677](https://github.com/pypa/gh-action-pypi-publish/commit/dc37677b2e1c63e2034f94d8a5b11f265b73ba33), `action.yml` defaults and `attestations.py` signing implementation
**Verification:** corroborated — the build job emits SLSA provenance, the separate PyPI job uses default Trusted Publishing attestations, and both consume the same distribution artifacts without rebuilding
**Revisit when:** the publishing action changes its default predicate or the workflow changes artifact transfer or attestation storage
**See:** supply-chain-security.md#provenance-minting-shares-the-protected-publication-boundary — a0396603-cb34-4151-9d5b-1fc77eb31f6e — as of 2026-10-08

The current configuration retains both mechanisms. GitHub's build step produces
SLSA provenance at build time, with workflow/source/run information and artifact
digests. The pinned PyPI action defaults to a PyPI Publish attestation during
Trusted Publishing to PyPI or TestPyPI: its predicate body is empty, and its
certificate identity identifies the publisher. It is not a second structured
SLSA build statement. PEP 740 defines index-hosted attestation handling rather
than requiring that all attestations make the same claim.

**Reason:** the claims and consumer channels complement one another. GitHub
stores build attestations and the template attaches their bundles to releases;
PyPI exposes publication attestations through its per-file provenance APIs and
UI. The publishing and release-attachment jobs download the built distributions
without rebuilding them, preserving the artifact hashes. PyPI's default signing
does not export the separately created GitHub build-provenance bundle to PyPI.

**Rejected alternative:** remove the explicit GitHub step because PyPI already
signs attestations. The default publication claim does not replace the structured
build claim or the build bundle distributed with GitHub Releases.

**Rejected alternative:** disable PyPI's default attestations as duplicate work.
That would remove the index-hosted publication claim and its discovery channel.
There is overlapping identity/integrity coverage, but neither path currently
replaces all of the other's claims and availability.

GitHub's private-repository entitlement and explicit opt-in govern its build
attestations only. The PyPI action has no equivalent repository-visibility gate;
its default path requires Trusted Publishing and uses public Sigstore signing
infrastructure. API-token publication or an explicit attestation opt-out changes
that path. Main-only publication depends on the configured GitHub environment policy,
not inferred merely from a PyPI publisher's repository/workflow registration.

The verification procedures and availability distinction are in generated
`docs/installation.rst`. This is a present decision grounded in the documented
mechanisms; the original rationale remains unknown in the superseded record.

## Unknown scan visibility fails open; private audits remain useful

**Id:** 8973c4ce-8e76-42fa-b69b-e52fc34eba50
**Type:** decision
**Type:** workaround
**Status:** active
**Evidence:** confirmed
**Source:** [issue #293](https://github.com/hasansezertasan/copier-pyproject/issues/293), [PR #294](https://github.com/hasansezertasan/copier-pyproject/pull/294), [PR #291](https://github.com/hasansezertasan/copier-pyproject/pull/291); commits [0e7fac8](https://github.com/hasansezertasan/copier-pyproject/commit/0e7fac8acb9d7b98f449380791212a7f58ed33f9) and [f19133d](https://github.com/hasansezertasan/copier-pyproject/commit/f19133d059f93c35136a81cb2cdebea017d9cf49)
**Verification:** corroborated — CodeQL and Scorecard coalesce visibility sources with a public default; zizmor selects public SARIF or private inline annotations
**Revisit when:** GitHub documents a reliable visibility source for scheduled runs or private scanning availability changes

CodeQL and Scorecard use two potential visibility sources and default an unknown
result to public. Zizmor instead switches its output mode: public repositories
use the code-scanning dashboard, while private/internal repositories keep the
audit through inline annotations rather than a potentially unsupported upload.

**Reason:** scheduled runs lack the usual repository event payload, and the
other visibility property was undocumented and runtime-unverified in the
investigation. Silently skipping public security scans when both sources are
empty is a worse failure than an unsupported private run reporting an error.
Zizmor's push/PR events have the payload needed for its narrower mode selection;
an unavailable private dashboard does not make the underlying audit useless.

**Rejected alternative:** guard scheduled scans with a single visibility source.
It could silently disable analysis when that source is absent.

**Rejected alternative:** skip the entire private zizmor job. That discards an
audit that can still report through annotations without code-scanning support.

The fallback rationale is confirmed by the sources; actual runtime availability
of the undocumented visibility property remains unknown. Source inspection
corroborates the implemented policy, not that property's runtime behavior.
[ADR-013](013-megalinter-opt-in-lean-complement.md) separately records
MegaLinter's best-effort SARIF upload posture.

## Local and historical secret scanning cover different failure stages

**Id:** 62d903d7-45bb-4790-b28a-f5dd1934983a
**Type:** decision
**Status:** active
**Evidence:** confirmed
**Source:** [issue #175](https://github.com/hasansezertasan/copier-pyproject/issues/175), [PR #236](https://github.com/hasansezertasan/copier-pyproject/pull/236); commit [825f420](https://github.com/hasansezertasan/copier-pyproject/commit/825f420cf4fafcc4444f85b108db84a21b4389e8); `docs/template-architecture.md`, secret scanning
**Verification:** corroborated — generated prek config includes detect-secrets and a baseline, while the security workflow retains gitleaks history scanning
**Revisit when:** either scanner's execution stage or baseline-management contract changes

Generated projects retain both a local, baseline-backed detect-secrets hook and
history-spanning gitleaks in CI.

**Reason:** historical scanning detects exposure after a secret reaches commit
history. A local hook can stop that commit before the exposure occurs. The
committed baseline makes known false positives reviewable instead of requiring
blanket scanner suppression. Similar-looking scanners are therefore deliberate
layers, not redundant lint execution.

**Rejected alternative:** rely on historical gitleaks coverage alone. The issue
identifies the missing before-commit gate as the reason for adding local scanning.
Alternatives among other local scanning tools, and why they lost to
detect-secrets, are unknown in the reviewed evidence.

The baseline maintenance procedure is in generated `.github/CONTRIBUTING.md`.
[ADR-003](003-tox-as-canonical-lint-runner.md) covers the general fast-hook versus
full-suite boundary; this entry records the distinct exposure stages.
