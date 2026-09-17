# Project Vision

This is the project's aspirational north star — why it exists and what it's
becoming. It is **not** an operating instruction: CLAUDE.md governs what
Claude actually does session to session, and nothing here overrides or adds
to a hard constraint there. Read this for context on *why* the project is
shaped the way it is; read CLAUDE.md for *how* it runs.

## The goal

To become an intelligent, context-based, creative, visually aesthetic &
minimal, highly functional & optimized, expert-at-Metabase — knowing its
full capabilities in depth and staying current with what Metabase adds in
new releases — professional & accurate, end-to-end chart and dashboard
builder and maintainer of Recruit CRM clients' Advanced Analytics reporting
needs, completely capable of maintaining and sustaining itself while
delivering fully in each of these respects.

## What that means concretely, and where it actually lives

Each part of that goal is meant to be a real, checkable mechanism in this
repository, not just a sentiment — so each one is tied here to where it's
actually implemented:

- **Intelligent & context-based** — the memory layer: confirmed business
  facts with source/date/status carried on every entry
  (`references/metric-glossary.md`, per CLAUDE.md "Data discovery"), a
  stable cross-account schema reference (`references/schema-map.md`), a
  durable landing spot for a flagged discrepancy
  (`references/schema-discrepancies.md`), and a growing library of verified,
  reusable chart/query shapes (`references/canonical-patterns.md`) so the
  project gets faster and more consistent with every account it works on,
  instead of rediscovering the same ground each time.
- **Creative** — actively drawing on Metabase's full display catalog (not
  defaulting to bar/line/table out of habit — see `prompts/chart-generation.md`)
  and the accumulated shapes in `references/canonical-patterns.md`.
- **Visually aesthetic & minimal** — a deliberate house visual style
  (`references/visual-design-standards.md`): a validated, accessible color
  system applied consistently instead of Metabase's own automatic
  assignment, plus consistency conventions (title casing, number precision,
  chart-form choice) so a client's dashboards read as one designed system.
- **Highly functional & optimized** — drill-downs on every chart where a
  sensible target exists (`prompts/drilldowns.md`), cross-filtering over
  duplicated content, and genuinely reaching for Metabase's own native
  capability (Documents, Metrics, subscriptions/alerts) rather than
  hand-rolling a weaker equivalent.
- **Expert at Metabase, staying current** — a standing review dimension
  (`prompts/project-improvement.md`'s "Metabase currency" check) that diffs
  this project's documented `mb` skills/commands against what's actually
  bundled, and CLAUDE.md's plan-gating rule that confirms what this specific
  instance's plan actually supports before relying on it.
- **Professional & accurate** — the data-quality gate, query-transparency
  rules (named steps, real join aliases, no hidden filters), and
  ask-once-per-account discipline that CLAUDE.md already enforces on every
  chart this project creates.
- **Self-maintaining & sustaining** — `prompts/project-improvement.md`'s
  on-demand repo-wide review (now including the Metabase-currency and
  memory-layer-consistency checks), an append-only local audit trail
  (`logs/history.jsonl`) and team-shared backlog
  (`references/project-improvements.md`) that together mean a rough edge
  found once doesn't have to be rediscovered.

## A living document, deliberately

As the project's actual capability grows — a new Metabase feature adopted, a
new convention added — this file should be revisited so it keeps describing
something real rather than drifting into aspiration nobody's checking. That
revisit is the same explicitly-confirmed kind of change as any other edit to
this project's own files (per CLAUDE.md's "Style"), never a silent rewrite.
