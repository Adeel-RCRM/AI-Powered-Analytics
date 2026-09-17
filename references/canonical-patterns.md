# Canonical Patterns

Recurring, genuinely reusable chart/query *shapes* this project has already
built and verified — not business-term definitions (those go in
`references/metric-glossary.md`) and not structural schema facts (those go in
`references/schema-map.md`). A pattern here is a **construction**: which
entities it joins, what it ranks/summarizes and how, and when it does (and
doesn't) apply — the kind of thing `prompts/requirements-intake.md`'s
resolution ladder checks first, before falling back to schema/glossary
lookups or live discovery.

## How this file is organized

Each pattern is its own subsection, named for what it computes — not for the
one chart it was first built for. Include:

- **Applies to** — the entity/table shape this pattern needs (e.g. "any
  account with a `hiring_stage`-style pipeline table").
- **Construction** — the reusable logic in plain terms: which tables it
  joins, what it ranks or summarizes, and the key steps (per CLAUDE.md "Query
  transparency" — name the steps, don't just describe a black box).
- **Confirmed on** — which account(s) this has actually been built and
  verified for.
- **When NOT to reuse it** — the specific conditions that mean this shape
  doesn't apply (a different join cardinality, a business rule that varies by
  account, etc.) — reusing a pattern where it doesn't actually fit is worse
  than not having one.

## Adding a new pattern

Only after a chart is built and verified (`prompts/chart-generation.md` step
7/8) and its underlying logic is genuinely reusable across more than one
likely question or account — not for a true one-off (see CLAUDE.md "Chart
creation" for the same reusability bar applied to Models). Append a new
subsection here rather than editing an existing one if a later account's
version of the same idea has a materially different construction — note the
difference under "When NOT to reuse it" on the original instead of silently
overwriting it.

---

_(no patterns recorded yet)_
