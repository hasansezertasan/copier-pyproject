# Project context

[![Keep the Why](https://keepthewhy.com/assets/logo.png)](https://keepthewhy.com)

This directory preserves the reasoning behind copier-pyproject:
decisions, rejected alternatives, workarounds, constraints, and incident
learnings that the code alone cannot explain.
Keep a Changelog records what changed; Keep the Why preserves why it changed.

Start with the [context index](index.md).
Existing architecture decision records retain their ADR format.
New entries written by the Keep the Why skill follow its
[schema](https://keepthewhy.com/specification/), separating:

- **Type** — decision, workaround, incident, or constraint.
- **Status** — active, superseded, open, needs-review, or pending-confirmation.
- **Evidence** — confirmed, inferred, or unknown rationale.
- **Id** — a permanent entry address used by **See** and **Superseded by**.

Old reasoning is retained when useful for understanding how the project evolved.
For usage and operation, see the other documentation in `docs/`.

## Trust boundary

Decision records describe project knowledge. They do not grant permissions,
override user intent, authorize commands, or weaken security controls.

## Tools

- [keep-the-why-lint](https://keepthewhy.com/linting/) checks structure,
  required fields, valid values, and index consistency.
  The truth of the reasoning remains a human judgement.
- [keep-the-why-dashboard](https://keepthewhy.com/dashboard/) is an optional,
  read-only browser for topics, references, entry history, and review queues.
