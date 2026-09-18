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
- **v2.0** (2026-09-18) — first real calibration, from account 89060's
  Cleveland Clinic dashboard (15 cards + dashboard assembly). Two
  independent problems found when the user's own recalled effort (~3 hrs)
  was compared against v1.0's estimate (738 min, ~12.3 hrs) for the same
  work — see "Calibration log" below for the full comparison:
  1. **Comprehension was being charged per resulting card, not per
     requirement.** A single stated ask ("build these 8 metrics for the
     Hiring Activity tab") decomposes into 8 numbered charts/cards in
     `prompts/requirements-intake.md`'s output, but the actual
     understanding work — the Job Owner field limitation, the team-scoping
     choice, which tables apply — happens once, resolving the batch, not
     once per resulting card. Comprehension-time factors below now score
     once per **resolution batch** (requirements grouped by shared
     entity/model per `prompts/requirements-intake.md`'s "Resolving each
     requirement" step 4), not once per card. This alone took the account's
     total from 738 to ~579 min.
  2. **The build-time weights themselves were too high for a professional
     analyst's real speed** — the user's first real anchor: "Phone Screens"
     (1 join, 1 distinct-count aggregation, 3 filters), which v1.0 scored
     at 25 min, actually takes **~3 min**. An early draft of this fix just
     multiplied every v1.0 weight by the resulting ratio (3/25 = 0.12) —
     the user correctly rejected that as not a real fix: it preserves
     v1.0's relative weighting between factors (is a join really worth 2x
     a filter? nobody ever checked), just shrinks all of it by one
     constant. **v2.0 instead reasons each build-time factor directly from
     what the action actually takes in Metabase's notebook editor**, not
     from dividing v1.0's numbers — see "Build-time factors" below for the
     per-factor reasoning. The `base`/`join`/`filter` factors are
     **directly anchored**: they're set so a single-join, 1-aggregation,
     3-filter card sums to exactly the user's real 3-min number.
     `summarize step`/`custom expression`/`formatted column` are reasoned
     from the same kind of UI action (a similarly-quick notebook-editor
     step) but not yet independently anchored. `stage-conversion`,
     `native SQL`, `Model promotion`, and `drill-down wired` are the least
     certain — genuinely different, heavier actions with no anchor yet;
     flagged individually below. Dashboard assembly, a pivot's drill-down
     dashboard, and a documentation Document stay at v1.0 numbers —
     categorically different work (layout, multi-card parameter wiring,
     prose) with no anchor of any kind yet.
  - Per "Versioning" above, v1.0-scored entries in
    `logs/performance-tracking.jsonl` are **not** reinterpreted — they stay
    readable as what v1.0 thought the work was worth. Where a v1.0 entry's
    underlying work has been re-scored under v2.0's per-requirement model
    (as account 89060's was, at the user's request), the new v2.0 entries
    carry a `supersedes` field listing the old `tracking_id`s they replace
    — see `prompts/performance-tracking.md`'s "Log schema".
  - This is explicitly a first pass, not a settled calibration — flagged as
    provisional, to keep being adjusted as more real anchors come in.
  - **Same-session refinement (2026-09-18), after the first drill-down
    batch was actually built (account 89060):** **a straightforward
    drill-down never carries a comprehension charge — only build time,
    full stop**, even one that needed genuine investigation to build
    correctly (an unexpected source table, diffing a sibling to catch a
    divergent condition). That investigation is real work, but it's build
    work, not fresh requirement analysis — the business decision was
    already made once, for the original report card. "Straightforward"
    means a genuinely terminal, plain-record-list destination — any of
    three things makes a drill-down a different case, scored as its own
    separate chart with full comprehension + build instead: customized
    logic of its own, a destination that computes a *different metric*
    rather than showing raw rows, or being itself an intermediate hop that
    carries a *further* drill-down of its own (a chained/multi-level
    case — even a plain record list stops being "just a lookup" once it
    also has to be designed as a launchpad for something else). (Earlier
    passes of this same refinement got it wrong more than once — a flat
    per-drill-down comprehension charge even for the mechanical case, then
    still allowing comprehension for investigative-but-terminal
    drill-downs, then missing the chained-drill-down case entirely — all
    corrected; see "Build-time factors" below for the final three-part
    test, which folds investigative effort into build time as a flagged,
    un-anchored simplification rather than a comprehension charge.) Applied
    to the one drill-down batch already logged for 89060, via `supersedes`
    (same session, still `pending` — not yet a confirmed record another
    consumer could have relied on).

## Comprehension-time factors

Estimates the cost of figuring out what needs to be built — reading the
source material, mapping business language to real fields, resolving
ambiguity — as distinct from the cost of actually building it. **Scored
once per resolution batch** (every requirement grouped together per
`prompts/requirements-intake.md`'s "Resolving each requirement" step 4 —
i.e. the requirements that were actually analyzed together, sharing
discovery/decisions — not once per resulting numbered chart or card),
at the point its recommendation(s) are presented
(`prompts/requirements-intake.md`'s numbered output step). A batch that
decomposes into several cards (e.g. 8 KPI metrics for one tab) still gets
exactly one comprehension score, using the batch's own totals for the
factors below (the widest entity count touched by any card in it, whether
*any* card in it needed new discovery, the number of genuinely distinct
clarifying questions the batch needed, whether *any* card in it needed a
data-quality-gate check). **A straightforward drill-down never carries a
comprehension charge, full stop** — even one that needed real
investigation to build correctly (an unexpected source table, diffing a
sibling for a divergent condition), is scored through build time only,
per "Build-time factors" below. The exception: a drill-down with
customized logic of its own, whose destination computes a different
metric, or that's itself an intermediate hop carrying a *further*
drill-down of its own — any of those three isn't "a drill-down" for
scoring purposes at all, it's scored as its own separate chart with its
own full comprehension total, same as any independently-requested chart
(see "Build-time factors" below for the exact three-part test).

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

Estimates the cost of actually constructing a card, scored against its real
structural shape — never a flat per-chart-type average, and **never
discounted for repetition**: deciding what to build (chart type, fields,
approach) is comprehension's job, scored once per batch above; once that's
decided, a card's build time reflects only its own structural shape, the
same whether it's the 1st or the 8th similarly-shaped card built in a
session (the user's explicit correction going into v2.0 — see the
changelog). Applied **per card**, then summed across every card a
requirement/batch produced to get the batch's own build-time totals (see
`prompts/performance-tracking.md`'s "Log schema" for the `cards` array this
scores against). Applied twice per card during confirmation (see
`prompts/performance-tracking.md`): once against the **final, current**
state of the card (everything it takes to reach the finished, client-ready
version), and once against only the **retained** elements (whatever
survived from the original build, unchanged).

**Each factor below is reasoned directly from the actual notebook-editor
action it represents — never derived by scaling a v1.0 number.** Tagged
`[anchored]` where a real timed data point backs it, `[reasoned]` where
it's a first-principles estimate from the same kind of UI action but not
yet independently timed.

- **Base** — chart creation in MBQL: open the notebook editor, pick the
  table, add the one aggregation every scalar/ratio card has by
  definition, name it, save, quick verify run: **1.5 min** `[anchored]`
  (see below)
- **+0.5 min** per join — pick the join target; Metabase auto-suggests the
  FK condition for a real foreign key, so this is mostly confirming it and
  restricting `fields` to what's needed: `[anchored]`
- **+0.33 min** per filter configured — pick field, operator, value: `[anchored]`
  — **base + 1 join + 3 filters = 1.5 + 0.5 + (0.33×3) = 3.0 min**, matching
  the user's real anchor for "Phone Screens" exactly. This is the only
  combination actually timed so far; everything below extrapolates from
  the same "one notebook-editor click-chain" pace, not from more anchors.
- **+0.5 min** per summarize/aggregation step beyond the first — pick
  function, field, name it: `[reasoned]`, same pace as a filter plus a
  moment to name it
- **+0.5 min** per formatted column (currency/percent/duration
  `column_settings`) — a couple of dropdown picks in the column formatting
  panel: `[reasoned]`
- **+0.75 min** per custom expression or calculated column — writing a
  formula takes more thought than a dropdown pick: `[reasoned]`
- **+1 min** if the query was promoted to a Model — the extra save/naming/
  description step on top of the query logic itself: `[reasoned]`
- **+2.5 min** if the metric required the stage-to-stage
  double-summarization technique (CLAUDE.md "Stage-to-stage conversion
  ratios") — a compound multi-step pattern (filter to the reached-stage
  population, then a second summarize on top of it), roughly the cost of
  several summarize/filter steps stacked: `[reasoned]`, genuinely
  uncertain until a real one gets timed
- **+6 min** if native SQL was genuinely required instead of MBQL — writing
  a raw query from scratch plus the mandatory live-validation run
  `prompts/chart-generation.md` requires for native SQL specifically is
  substantively different work from a notebook-editor click-chain, not
  just a bigger version of it: `[reasoned]`, the least confident number in
  this file until a real one gets timed
- **+5 min build, zero comprehension** per straightforward drill-down
  wired on this card's dashcard (see the three-part "straightforward" test
  two bullets below — a terminal, plain-record-list destination, nothing
  further going on) — `[anchored]` for the mechanical case, from account
  89060's Cleveland Clinic drill-down batch (2026-09-18): building the
  whole drill-down card (copying the report's `joins`/filters verbatim,
  the group-by-plus-id dedup, entity profile link, a context field),
  wiring its `click_behavior`, and verifying against one filtered slice
  (e.g. "Resume Submits Detail"). **A straightforward drill-down never
  carries a comprehension charge, including one that needed genuine
  investigation to build correctly** (discovering the report is built on
  an unexpected table, diffing a ratio's numerator against its sibling to
  catch a divergence, reasoning out a reusable Model instead of building a
  new one) — that investigation is real work, but it's still build work,
  not fresh requirement analysis, and this project doesn't yet have a
  differentiated build weight for it. **Known simplification**: an
  investigative-but-still-terminal drill-down is scored at the same flat 5
  min as a purely mechanical one for now — this under-counts real effort
  on the harder cases and is a first candidate for its own anchor (a timed
  "investigative drill-down" build, separate from the mechanical one
  already anchored) next time this file is calibrated. A drill-down that
  fails the "straightforward" test (customized logic, computes a different
  metric, or is itself an intermediate hop to a further drill-down) gets
  none of this — see the next bullet.
- **A drill-down is only "straightforward" — and only gets the flat weight
  above — when it's a genuinely terminal, plain underlying-record-list
  destination with nothing further going on.** Any of these three makes it
  a different case, scored as its own separate chart instead (not "a
  drill-down" for scoring purposes at all):
  1. **Customized logic of its own** — anything beyond a straight copy of
     the report's own `joins`/filters/expressions.
  2. **Its destination computes a different metric** — a rate, a ranking,
     another aggregation — rather than showing raw underlying rows.
  3. **It's an intermediate hop, not a terminal one** — it carries its
     *own* further `click_behavior` to yet another destination (a
     multi-level/chained drill-down). Even a plain record list stops being
     "just a lookup" once it also has to be designed as a jumping-off
     point for something else — that's real, additional design work a
     terminal detail card never needs.

  Score any of these three through the normal comprehension
  (base/entities/discovery/questions/data-quality, per
  "Comprehension-time factors" above) and build (base/joins/summarize/
  custom-expressions/filters/etc., per the factors above) — exactly as if
  it had been independently requested. The test: "show me the rows behind
  this count, and that's the end of the click-through" is a lookup (the
  flat weight above applies, no comprehension); anything that adds its own
  logic, computes something new, or itself becomes a launchpad for another
  click is chart design that happens to be reached by a click, not a
  lookup — CLAUDE.md's "Drill-downs" custom-destination mechanism supports
  linking to any of these, but only the first, terminal, record-list kind
  is genuinely "fiddly wiring," not fresh design.
- **A reused chart or drill-down card is counted once — reuse itself is
  free at the card-build level.** When an already-built card (a chart or a
  straightforward drill-down) gets pointed at from an *additional*
  dashcard or table column — e.g. one drill-down card serving a standalone
  KPI, a per-column mapping on a table, and a ratio's numerator all at
  once — its own `joins`/`filters`/etc. build weight is credited exactly
  once, at first build. It is **not** re-credited (or re-charged) for
  every place it gets wired to. **+1 min, `[reasoned]`, per additional
  wiring, charged as dashboard build time, not chart/drill-down build
  time** — picking the existing target, mapping its columns/filters, and a
  quick verify is real but minor work, and it belongs to the same bucket
  as "Scored separately" below (dashboard assembly), not to the reused
  card's own build total. Keep this cost visible as its own line (a
  `reuse_wirings` list, not folded into a card's `build_minutes`) so it
  stays attributable to "extra dashboard wiring," not inflated card-build
  time — same "Query transparency" spirit as never collapsing two real
  costs into one number.

**Scored separately, as their own unit (not folded into any one chart's
batch, and not summed into a requirement's build total) — and
deliberately kept at v1.0 weights, unscaled:** dashboard assembly, a
pivot's drill-down dashboard, and a documentation Document are a
categorically different kind of work from building one card (layout,
parameter/filter wiring across many cards at once, writing prose) — the
reasoning above (single-card notebook-editor actions) doesn't transfer to
this kind of task. These three stay at v1.0's numbers until they get their
own real anchor:
- **+12 min** flat for dashboard assembly — layout plus parameter/filter
  wiring (`prompts/requirements-intake.md` "Assemble the dashboard(s)")
- **+25 min** flat for a pivot table's dedicated drill-down dashboard
  (`prompts/drilldowns.md` "Drill-downs for a pivot table")
- **+20 min** flat for a companion documentation Document (CLAUDE.md
  "Dashboard documentation")

Sum the applicable per-card factors for that card's own `build_minutes`,
then sum every card's `build_minutes` in the same batch for the batch's
`build_minutes` total. `dashboard_assembly` / `pivot_drilldown_dashboard` /
`documentation` stay their own separate units, scored once each, never
folded into a chart batch's total.

## How the two combine

Per **resolution batch** (see "Comprehension-time factors" above — the
requirements analyzed together, which may decompose into several cards),
once every card it produced has been built and verified
(`prompts/chart-generation.md` step 10, coordinated by
`prompts/requirements-intake.md`'s resolution loop — see
`prompts/performance-tracking.md`'s "Step 1" for exactly when the entry is
written):

- Score `comprehension_minutes` once for the whole batch, from the
  requirement(s) as resolved.
- Score each resulting card's own `build_minutes_snapshot` against that
  card exactly as created, and snapshot its actual
  `dataset_query`/`visualization_settings`/`click_behavior` — this is what
  a later confirmation diffs against (see `prompts/performance-tracking.md`).
  These live in the batch entry's `cards` array, one element per card.
- `build_minutes_snapshot_total` — the sum of every card's own
  `build_minutes_snapshot` in the batch.

At confirmation, after diffing each card in the batch against its own
snapshot:

- Per card: `build_minutes_final` (every structural element present in its
  **current** state) and `build_minutes_retained` (only the elements
  identical to its snapshot) — same per-card diffing mechanics as before,
  unchanged by the batch grouping.
- `build_minutes_final_total` / `build_minutes_retained_total` — sum each
  across every card in the batch.
- `pct_claude_build = build_minutes_retained_total / build_minutes_final_total`
- `build_minutes_saved = build_minutes_retained_total` (a direct sum of
  retained elements' own weights across every card in the batch — never
  `pct_claude_build × build_minutes_final_total`; computing it as a
  ratio-multiplication would hide which specific elements it came from, the
  same opacity CLAUDE.md's "Query transparency" already forbids inside a
  chart's own query).
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

- **2026-09-18, account 89060 (Cleveland Clinic dashboard), v1.0 → v2.0.**
  v1.0 estimated 738 min (~12.3 hrs) total across 15 cards + dashboard
  assembly, scored per-card. The user's own recalled real effort for the
  whole thing was ~3 hrs. Two real anchors from this session:
  - Comprehension is genuinely spent once per resolution batch (the client's
    "8 metrics for the Hiring Activity tab" ask), not once per resulting
    card — confirmed by the user directly, not inferred.
  - Real build time for "Phone Screens" (1 join, 1 distinct-count
    aggregation, 3 filters, no visualization_settings) — a card the v1.0
    rubric scored at 25 min build — is **~3 min** for a professional
    analyst who already knows what to build. Rather than scale v1.0's
    weights by the resulting ratio (rejected — it would carry forward
    v1.0's never-validated relative weighting between factors), the `base`/
    `join`/`filter` weights were set directly so this exact shape sums to
    3 min (1.5 + 0.5 + 0.33×3 = 3.0). Every other per-card factor is a
    first-principles estimate from the same "one notebook-editor action"
    pace, individually tagged `[reasoned]` vs. `[anchored]` in "Build-time
    factors" above, not derived from this one data point either.
  - Applying both fixes (batch-level comprehension + the reasoned build
    weights) to account 89060's actual logged work: 69 min comprehension
    (4 batches) + ~72 min build (15 cards, retained) ≈ **141 min (~2.35
    hrs)** — in the right neighborhood of the user's ~3 hr estimate, not
    an exact match. Logged as-is rather than further hand-tuned to close
    the last gap — see the note below.
  - **This is one calibration pass, not a finished one.** Only the `base`/
    `join`/`filter` factors are genuinely anchored; `summarize step`/
    `custom expression`/`formatted column` are reasoned from the same kind
    of action but untimed; `stage-conversion`/`native SQL`/`Model
    promotion` are the least confident numbers in the file; `drill-down
    wired` has no number at all yet (see "Add the drill-downs" work this
    session for where that anchor comes from). The three flat "own unit"
    costs (dashboard assembly, pivot drill-down dashboard, documentation)
    are still unvalidated v1.0 guesses. The user's own words going into
    this: "we will keep fixing the logic until I'm satisfied with it" —
    treat v2.0 as a working draft, not a settled number, and expect
    further versions as more real anchors come in.
