# Effort Estimation Rubric

Translates the real, structural shape of a Requirements Intake
requirement — what it took to understand, and what it took to build — into
an estimated manual-equivalent time, in minutes. Used by
`prompts/performance-tracking.md` to score how much of a delivered
requirement is genuinely this project's contribution versus the user's own
manual work, and what that contribution was worth in time.

**This is an estimate, not a measurement, and every entry that uses it says
so.** There is no controlled experiment behind these numbers — they're a
documented, consistently-applied judgment, the same kind of judgment an
experienced analyst already makes informally when estimating how long a
piece of work will take. What makes it trustworthy isn't precision, it's
that the same rubric, versioned and inspectable, is applied the same way
every time — so a change in the numbers over time reflects a change in this
project's actual output, not a change in how generously it's being scored.

## Versioning

Every scored entry in `logs/performance-tracking.jsonl` records the
`rubric_version` that scored it. When this file's weights change, bump the
version and add a changelog entry below — **never silently reinterpret an
old entry under a new version's weights.** An old entry stays honestly
readable as "what version N thought this was worth," the same append-only
spirit as `references/metric-glossary.md`'s `Superseded` notes.

**Changelog:**
- **v1.0** (2026-09-18) — initial rubric. Weights are starting estimates
  grounded in typical Metabase-analyst work patterns, not yet calibrated
  against a real timed manual build — see "Keeping this rubric honest"
  below.

## Comprehension-time factors

Estimates the cost of figuring out what needs to be built — reading the
source material, mapping business language to real fields, resolving
ambiguity — as distinct from the cost of actually building it. Scored once
per requirement-unit, at the point its recommendation is presented
(`prompts/requirements-intake.md`'s numbered output step).

- **Base, by source type:**
  - Stated directly (a written ask, a numbered list item): **3 min**
  - Extracted from a pasted transcript: **8 min** (parsing informal speech,
    separating the actual ask from surrounding conversation)
  - Extracted from an attached document (PDF, image, spec doc): **6 min**
- **Matched an existing `references/canonical-patterns.md` shape:**
  multiply the base by **0.25** — this is mostly a lookup, not fresh
  analysis.
- **+3 min** per additional entity/table beyond the first that the
  requirement touches.
- **+5 min** if this requirement needed genuinely new discovery — a table
  or account not already covered by `references/schema-map.md` or an
  existing `## Account <n>` section in `references/metric-glossary.md`.
- **+6 min** per clarifying question that was genuinely necessary to
  resolve *this specific requirement* (per
  `prompts/requirements-intake.md`'s "When to actually ask a question" —
  not a question asked for a different requirement in the same batch).
- **+4 min** if resolving this requirement genuinely required checking it
  against the data quality gate (CLAUDE.md "Data quality gate" /
  `config/analysis-config.md` thresholds) before trusting the shape.

Sum these for `comprehension_minutes`.

## Build-time factors

Estimates the cost of actually constructing the chart, scored against its
real structural shape — never a flat per-chart-type average. Applied twice
per requirement-unit during confirmation (see
`prompts/performance-tracking.md`): once against the **final, current**
state of the card (everything it takes to reach the finished, client-ready
version), and once against only the **retained** elements (whatever
survived from the original build, unchanged).

- **Base** — chart creation in MBQL, single table, no joins, no custom
  expressions or filters: **10 min**
- **+6 min** per join
- **+4 min** per summarize/aggregation step beyond the first
- **+5 min** per custom expression or calculated column
- **+12 min** if the metric required the stage-to-stage
  double-summarization technique (CLAUDE.md "Stage-to-stage conversion
  ratios")
- **+20 min** if native SQL was genuinely required instead of MBQL (writing
  it, plus the mandatory live-validation run `prompts/chart-generation.md`
  requires for native SQL specifically)
- **+10 min** if the query was promoted to a Model (the extra save/naming/
  description step, on top of the query logic itself)
- **+3 min** per filter configured
- **+3 min** per formatted column (currency/percent/duration
  `column_settings`)
- **+15 min** per drill-down wired on this card's dashcard (CLAUDE.md
  "Drill-downs" — copying `dataset_query` construction verbatim,
  restricting join fields, verifying against a filtered slice, is
  genuinely fiddly to reproduce by hand)

**Scored separately, as their own unit (not folded into any one chart):**
- **+12 min** flat for dashboard assembly — layout plus parameter/filter
  wiring (`prompts/requirements-intake.md` "Assemble the dashboard(s)")
- **+25 min** flat for a pivot table's dedicated drill-down dashboard
  (`prompts/drilldowns.md` "Drill-downs for a pivot table")
- **+20 min** flat for a companion documentation Document (CLAUDE.md
  "Dashboard documentation")

Sum the applicable factors for `build_minutes`.

## How the two combine

Per requirement-unit, at the point a card is created
(`prompts/chart-generation.md` step 10):

- Score `comprehension_minutes` once, from the requirement as resolved.
- Score `build_minutes_snapshot` against the card exactly as created.
- Snapshot the card's actual `dataset_query`/`visualization_settings`/
  `click_behavior` alongside these scores — this is what a later
  confirmation diffs against (see `prompts/performance-tracking.md`).

At confirmation, after diffing the live card against its snapshot:

- `build_minutes_final` — score every structural element present in the
  **current** state (retained and changed/added together).
- `build_minutes_retained` — score only the elements identical to the
  snapshot.
- `pct_claude_build = build_minutes_retained / build_minutes_final`
- `build_minutes_saved = build_minutes_retained` (a direct sum of retained
  elements' own weights — never `pct_claude_build × build_minutes_final`;
  computing it as a ratio-multiplication would hide which specific elements
  it came from, the same opacity CLAUDE.md's "Query transparency" already
  forbids inside a chart's own query).
- `total_time_saved_minutes = comprehension_minutes + build_minutes_saved`
  for a `built_clean`/`built_modified` outcome. For `infeasible_data`, it's
  `comprehension_minutes` alone (`build_minutes_saved` is 0 — nothing was
  built). For `infeasible_tool_capability`, and for an
  `extra_manual_addition` classified as a missed original requirement, it's
  0 either way — see `prompts/performance-tracking.md`'s outcome taxonomy
  for why.

This is deliberately never netted against how long the AI-assisted build
itself took, or how long the user's later manual fixes took — see
CLAUDE.md "Performance tracking" for why both are excluded from this figure
and tracked separately instead.

## Keeping this rubric honest

Scoring a contribution's own value against a rubric this project also
maintains is a real self-assessment risk — nothing structurally prevents
the weights above from drifting flattering over time, especially across
prompt or model changes. Two guardrails, both required:

1. **Keep every factor mechanical.** A weight is only ever attached to a
   countable structural fact (a join, a step, a chart type, a drill-down) —
   never a subjective "this felt complex" judgment call added on top.
2. **Calibrate periodically, not per-request.** Every so often — not on
   every confirmation — sanity-check a rubric estimate against a real,
   actually-timed manual build of something comparable (a teammate builds
   an equivalent chart by hand, timed, independent of this project). Log
   the comparison below regardless of whether it confirms or contradicts
   the current weights; if it contradicts them meaningfully, bump the
   version and adjust, per "Versioning" above.

## Calibration log

_(no calibration checks recorded yet)_
