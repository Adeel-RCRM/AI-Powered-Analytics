# Visual Design Standards

A house design system for **every** chart and dashboard this project builds —
one fixed, professional standard applied identically across every Recruit CRM
account, so the whole body of work reads as one deliberately designed system
rather than whatever Metabase's own automatic defaults happen to produce on a
given day. Applied entirely through Metabase's own `visualization_settings`,
dashboard grid/layout, and native dashboard filters (`series_settings`,
`column_settings`, conditional formatting, goal lines, per-card layout) —
never through CSS or HTML this project doesn't control.

**This standard is universal, not client-specific — and that's deliberate.**
A client's brand colors, logo, or visual identity have no bearing on how a
chart should be built: the palette, layout hierarchy, and every rule below
apply the same way to every account. Never ask a client "what colors do you
want," never vary the categorical order or dashboard hierarchy per account,
and never treat any of this as a per-client customization surface. See
"This is fixed, not a per-client style" at the bottom for the one narrow,
deliberate exception (Recruit CRM itself adopting its own permanent house
palette, project-wide, not per client).

**Scope: governs new work going forward, not retroactive.** Never recolor or
relayout an already-shipped client dashboard's cards to match this file
unless the user specifically asks for that — this project only adds/improves
what it's asked to touch, per CLAUDE.md hard constraint 7's spirit.

## Grounding

Every rule below traces to one of three sources, not house opinion:

- The `dataviz` skill's design-system-agnostic method — a *computable* color
  formula (OKLCH lightness/chroma bands, CVD simulation, WCAG contrast — run
  `node scripts/validate_palette.js` from that skill's base directory rather
  than eyeballing a palette), a form-selection heuristic, and a catalog of
  named anti-patterns. Its validated reference instance is
  `references/palette.md` inside that skill.
- Metabase's own official guidance (`metabase.com/learn` "BI dashboard best
  practices," and the product docs for line/bar/area charts, multi-series
  cards, and pie charts) — this is what tells us which of the rules below are
  actually expressible through a real `visualization_settings` key today,
  and which are Metabase's own recommended defaults.
- Stephen Few's *Information Dashboard Design* and the general BI-dashboard
  literature on information hierarchy (the "inverted pyramid," the "5-second
  rule," F-pattern scanning, data-ink ratio) — this is where the "Dashboard
  layout" section below comes from.

Where Metabase genuinely doesn't expose a setting for something the
literature recommends (e.g. per-pixel mark specs, custom hover-tooltip
layout, a live chart/table toggle for viewers), this file says so explicitly
rather than inventing a `visualization_settings` key that doesn't exist —
load the `visualization` skill to confirm any key named below before relying
on it, since exact key names can shift across Metabase versions.

## Dashboard layout & information hierarchy

Before any individual chart's styling, the dashboard's own structure is the
first thing a viewer reads — get this wrong and no amount of per-chart polish
saves it.

- **The inverted pyramid.** Order cards top-to-bottom by urgency, not by the
  order requirements happened to be gathered in: headline KPIs and
  status/target numbers at the top, supporting trend charts and
  comparisons in the middle explaining *why* those numbers look the way they
  do, and granular detail tables or drill-down targets at the bottom. This is
  the same structure `prompts/requirements-intake.md`'s dashboard-assembly
  step already gestures at ("KPIs across the top, related charts side by
  side, wide tables full-width") — this section is that rule's full
  justification and the standard to check every dashboard against, not a
  competing rule.
- **Top-left is the highest-value real estate.** Per Metabase's own layout
  guidance, importance degrades top-to-bottom and left-to-right (for a
  left-to-right-reading audience) — put the single most important KPI in the
  top-left cell, not buried mid-grid.
- **The 5-second rule.** A viewer should be able to tell whether things look
  on-track within about five seconds of opening the dashboard, with no
  scrolling, filtering, or hovering required. If the headline KPI(s) aren't
  visible without scrolling on a normal laptop window, the layout has failed
  this regardless of how any individual card looks.
- **Above the fold, but never at the cost of legibility.** Prefer keeping the
  top-priority row visible without scrolling — but per Metabase's own
  guidance, never shrink a card below legible size just to force everything
  onto one screen. A dashboard that needs a second screen's worth of detail
  is fine; a dashboard whose KPI numbers are too small to read is not.
- **Group by subject, and say so.** Cluster cards that cover the same topic
  together on the grid rather than interleaving unrelated subjects; use a
  Metabase text card as a section header/divider between groups on a
  multi-topic dashboard, per Metabase's own guidance on using text cards as
  structural elements, not just commentary.
- **Align time granularity across cards sharing a date filter.** When more
  than one card on the same dashboard responds to the same date-range
  parameter, keep them at the same temporal grain (all weekly, or all
  monthly) — per Metabase's own guidance, mismatched granularity across
  cards under one shared filter reads as the data disagreeing with itself,
  even when both numbers are correct.
- **Data-ink ratio.** Every visual element should carry information. Don't
  override Metabase's already-fairly-minimal chart chrome toward decoration
  (background images, unnecessary borders, 3D-style effects) — if a setting
  doesn't change what the chart communicates, leave Metabase's default in
  place rather than adding it.
- **Minimize chart-type variety by default.** Per Metabase's own guidance,
  don't reach for an exotic display just to make the dashboard look varied —
  bar, line, and table remain the default workhorses for most insights.
  `config/analysis-config.md`'s chart-type table and `prompts/chart-generation.md`'s
  fuller display catalog (treemap, sankey, box plot, scatter, map, gauge)
  still apply exactly as written — reach for one of those when it's a
  *materially* better fit for the specific insight shape, never as visual
  seasoning on an otherwise plain dashboard.

## Choosing the form

Decide the chart's form before touching color — this is `dataviz`'s own
sequencing, and it prevents the single most common failure mode: picking
colors for a chart that shouldn't have been a chart.

- **Is it even a chart?** A single current value (plus maybe a trend) is a
  **scalar/smartscalar** with a comparison, not a one-bar bar chart. A
  handful of headline numbers is a row of KPI cards, not a grouped bar chart.
  A single ratio against a limit is a **progress/gauge**, not a 2-slice pie.
  More than ~7 categories that all genuinely carry meaning is a **table** (or
  table + chart), not a legend with 7+ swatches nobody can hold in their
  head.
- **Never a dual-axis chart (two y-scales on one plot).** This is the single
  most common charting mistake in the literature: the alignment between the
  two scales is arbitrary, so the chart invents a correlation that isn't
  actually in the data. Metabase can auto-split a combo/multi-series card
  onto a second y-axis ("split y-axis when necessary") or let a series be
  pinned to the right axis explicitly — **never do either.** When two
  measures genuinely have different scales, use two separate cards, small
  multiples (side-by-side cards or a dashboard tab), or index both series to
  a common base (both = 100 at the first period) on one shared axis instead.
- **Series-count ladder.** 1-3 series: color alone is comfortable, direct
  label if it fits. 4 series: still fine for a stacked/grouped bar or
  multi-line, but direct labels stop being optional. 5-6: soft cap — lean on
  the legend. 7-8: the hard token ceiling (see "Categorical color" below) —
  past it, fold the tail into "Other," facet into small multiples, or switch
  to a table.
- **A stricter cap for "all-pairs" forms.** Scatter, bubble, map/choropleth,
  treemap, and small-multiples are different from a bar/line/stack: *any two*
  marks can end up side by side, not just neighbors in a fixed order. These
  forms cap at **3** distinct categorical colors, not 8 — past 3, fold the
  rest into "Other" or facet rather than adding a 4th color to one of these
  forms.
- **Pie/donut stays small.** Cap a pie at the categories that are genuinely
  comparable at a glance (≤ ~6 for comparing close values) — use Metabase's
  own minimum-slice-size setting (the pie chart's "minimum slice %" control)
  to fold small remaining categories into "Other" automatically, rather than
  hand-filtering the query or letting the legend sprawl past what a donut can
  communicate. Never use a pie/donut to compare values that are close to each
  other — a bar reads more precisely; save the pie for a genuine
  part-of-whole story with one or two categories that clearly dominate.

## Color

Color is assigned by the *job* it does, never hand-picked, and always
assigned explicitly — never left to Metabase's own automatic series
coloring.

### Categorical color — series identity

Assign these eight hues, **in this fixed order**, to a chart's distinct
series/categories — never cycle past slot 8:

| Slot | Hue | Light | Dark |
|------|-----|-------|------|
| 1 | blue | `#2a78d6` | `#3987e5` |
| 2 | orange | `#eb6834` | `#d95926` |
| 3 | aqua | `#1baf7a` | `#199e70` |
| 4 | yellow | `#eda100` | `#c98500` |
| 5 | magenta | `#e87ba4` | `#d55181` |
| 6 | green | `#008300` | `#008300` |
| 7 | violet | `#4a3aa7` | `#9085e9` |
| 8 | red | `#e34948` | `#e66767` |

The Dark column is the same eight hues re-stepped for a dark chart surface,
not a separate palette — both columns pass the full CVD/contrast validator
(`node scripts/validate_palette.js` from the `dataviz` skill's base
directory) independently: worst adjacent CVD ΔE 9.1 light / 8.4 dark,
worst adjacent normal-vision ΔE 19.6 light / 19.3 dark. **Metabase renders
every dashboard this project builds in its standard light theme today** —
the Dark column exists so this standard is ready, not so it's wired into
`series_settings` by default; only switch a card to the Dark column's
values if that specific card is genuinely being viewed under Metabase's own
night/embed dark theme (see "Accessibility" below), and never mix columns
on the same chart.

Apply via `visualization_settings.series_settings.<series name>.color` —
load the `visualization` skill for the exact key shape per chart type. This
is the same discipline CLAUDE.md's "Combo chart series display" already
requires for `display`: set the value explicitly for **every** series, not
just the ones that need to differ from a default.

A **single-series** chart still gets slot 1 (`#2a78d6`) set explicitly rather
than left to Metabase's default, so a dashboard's primary metric reads the
same blue everywhere.

**Color follows the entity across the whole dashboard, not just within one
chart.** If the same categorical dimension (a recruiter, a job source, a
pipeline stage treated nominally) appears broken out on more than one card
on the same dashboard, that category keeps the same color slot on every
card it appears on — a viewer who learns "Sarah is blue" on the first chart
shouldn't see her repainted green on the third. Assign the slot order once
per dashboard (by first appearance, or by an existing convention already set
for that dimension) and reuse it.

**Color follows the entity, never its rank or a filter's current result** —
if a dashboard filter can change which categories appear, a category keeps
its slot whenever it's present; the survivors don't get repainted just
because a different set showed up.

**Never color-rank a nominal category.** Coloring bars darker-where-bigger
when the categories have no inherent order (recruiters, job sources,
clients) double-encodes bar length as hue and burns the identity channel on
information the bar's own length already shows. A category with no real
order gets one flat color per slot; only a genuinely ordered category (see
"Ordinal color" below) earns a value-ramp.

Beyond **8 distinct categories** (3 for an all-pairs form — see "Choosing
the form"), don't invent a 9th color — fold the rest into "Other,"
reconsider the chart form (a table lists more categories legibly than a
legend can), or facet.

### Ordinal color — position in a known sequence

A category whose *order itself carries meaning* — a hiring-pipeline stage,
a size tier, an age band, a cohort bucket — is a fundamentally different
color job from plain categorical identity, and gets a different treatment:
**one hue, monotone lightness steps**, using the exact same blue ramp as
"Sequential color" below, so the color visibly encodes the progression.
Distribute the account's confirmed stage/tier order evenly across that
ramp's steps — lightest for the earliest stage, darkest for the last.

This is the common case for this project specifically: a "candidates by
pipeline stage" bar/funnel chart should **never** use the 8-hue categorical
palette (that palette says "these are unrelated identities"), and should
instead ramp one hue from light to dark across the account's confirmed
stage order (per CLAUDE.md's hiring-stage-order rule — never invent that
order, always ask). The test: if reordering the categories would change
what the chart means, it's ordinal; if it wouldn't (recruiter names, job
sources), it's categorical.

### Sequential color — magnitude (heatmap / range formatting)

One hue (blue), light → dark, for a table/pivot cell background or range
formatting where the lightest step means "near zero," and (per "Ordinal
color" above) for any chart whose categories carry a fixed, meaningful
order:

| Step | Hex | Step | Hex | Step | Hex | Step | Hex |
|------|-----|------|-----|------|-----|------|-----|
| 100 | `#cde2fb` | 250 | `#86b6ef` | 400 | `#3987e5` | 550 | `#1c5cab` |
| 150 | `#b7d3f6` | 300 | `#6da7ec` | 450 | `#2a78d6` | 600 | `#184f95` |
| 200 | `#9ec5f4` | 350 | `#5598e7` | 500 | `#256abf` | 650 | `#104281` |
| | | | | | | 700 | `#0d366b` |

Apply through a table/pivot's single-color conditional-formatting range —
load the `visualization` skill for the exact keys. Never use a multi-hue
"rainbow" ramp for magnitude — one hue, light to dark, is the entire rule.

**Dark mode reuses this exact same ramp** — it isn't a second table. The
ramp only changes which step anchors the "near zero" end: on a dark chart
surface, don't recede all the way to step 100 (too close to the dark
surface itself to read as a mark) — for an **ordinal** ramp specifically
(a discrete ordered category, not a continuous heatmap), stay within step
250–600 on light (`#86b6ef`, 2.06:1, is the lightest still-legible step) and
step 600 or darker on dark (`#184f95`, 2.15:1, is the darkest still-legible
step) — see the `dataviz` skill's `references/palette.md` "Sequential hue"
section for the full derivation. A **sequential** (continuous magnitude)
ramp can still recede to the lightest step in either mode, since "reads as
near-zero" is the intended effect there, not a legibility floor.

### Diverging color — polarity (over/under a baseline)

Blue ↔ red with a neutral gray midpoint, for a metric with a meaningful
"above vs. below a baseline" reading — performance vs. target, delta from a
prior period. Apply through a 3-color conditional-formatting range, equal
steps per arm. The midpoint must read as "nothing" and the two poles must
read as genuinely opposite — never a hue at the midpoint, and never two
poles from the same warm/cool family.

| | Light | Dark |
|---|-------|------|
| Blue pole | `#2a78d6` (categorical slot 1) | `#3987e5` (categorical slot 1, dark) |
| Red pole | `#e34948` (categorical slot 8) | `#e66767` (categorical slot 8, dark) |
| Neutral midpoint | `#f0efec` | `#383835` |

Each mode's poles are that mode's own categorical blue/red steps (from
"Categorical color" above) — never mix a light pole with a dark midpoint or
vice versa.

### Status color — fixed, reserved meaning

| Role | Hex | Light-surface contrast | Dark-surface contrast |
|---|---|---|---|
| good | `#0ca30c` | 3.27 | 5.19 |
| warning | `#fab219` | 1.79 | 9.49 |
| serious | `#ec835a` | 2.57 | 6.60 |
| critical | `#d03b3b` | 4.68 | 3.62 |

**Status is mode-invariant** — the same four hex values are used in both
light and dark dashboards (unlike the categorical palette, which re-steps
per mode); only the contrast against the surface changes, which is why
warning/serious already need the icon+label pairing below on a light
surface specifically, not on dark. Reserve these for an actual state
judgment (e.g. flagging a KPI because it's under threshold) — never reuse
one as "just another series" color, and never let a categorical series
borrow one of these four hues either. **The collision rule:** when a series
*means* good/bad (an error rate, a pass/fail split), it wears status
tokens; when it's just "series 4," it wears the categorical palette — never
both readings on the same chart.
Metabase can't render an icon inside a formatted cell, so a status color is
never the only signal: pair it with a clear label (the column header, or
the KPI's own title) rather than color alone — two of these steps sit below
a 3:1 contrast on a light surface by design, so a viewer who can't rely on
color still needs the label to read the state. Culturally, red/green
good-bad is a Western default, not a universal one — where that matters,
lean harder on the label/icon pairing rather than assuming the color alone
reads correctly for every viewer.

## KPI / trend-indicator direction semantics

Metabase's `smartscalar` display auto-computes a period-over-period
comparison with its own default coloring (an increase reads as "good," a
decrease as "bad") — this default is **not safe to accept unexamined**.
Before shipping any smartscalar/trend KPI card:

- **Decide whether "up" is actually good for this specific metric.**
  Placements, deal value closed, and candidates sourced going up is good.
  Cost of calls, time-to-fill, and candidate drop-off going up is bad. Check
  Metabase's comparison/direction setting for the card against the metric's
  real meaning (load the `visualization` skill for the exact key — it may
  live under the smartscalar's own settings rather than a generic one) and
  correct it when the metric is one where a rise is the bad outcome, rather
  than leaving Metabase's raw increase-is-green default in place by
  omission.
- **Add a goal line where the metric has a known target or threshold** —
  Metabase's own dashboard guidance recommends this specifically so a
  viewer can tell "good," "expected," or "off track" from the chart itself,
  not just from an isolated number. Only add one where a real target
  actually exists (a confirmed SLA, a stated client goal) — never invent a
  threshold.
- **Prefer a trend/comparison view over a bare number** when the data
  supports it — a plain scalar with no period-over-period or sparkline
  context answers "what" but not "is that good," which is the whole point
  of a KPI card. This is why `display: "smartscalar"` (comparison + trend)
  is generally preferred over a bare `scalar` per CLAUDE.md's "Chart type
  defaults," not just a stylistic choice.

## Data labels & legends

**Legend:** always present for two or more series — never remove it for a
"cleaner" look. A single-series chart needs no legend box (the title already
names what's plotted).

**Value labels — use Metabase's own "Some values" mode as the default, not
"All."** Metabase's `graph.show_values` setting supports showing all values,
some values (Metabase's own legibility-aware selection), or none — labeling
literally every point on a dense chart (e.g. daily data across several
months) is chaos that goes unread, while labeling every value on a genuinely
low-cardinality chart (a funnel with a handful of stages, a bar chart with
≤ ~8 categories) is exactly the case where "All" is the right, readable
default. In practice:

- **Low-cardinality discrete comparisons** (funnel, a bar/row chart with a
  small number of categories, a pie/donut within its cap) → show all
  values; at this density every value legitimately belongs on screen, per
  the series-count ladder above.
- **High-cardinality continuous trends** (a line/area chart with many x-axis
  points — daily/weekly data over months) → use Metabase's "some values"
  legibility mode rather than forcing every point, and rely on the legend
  plus Metabase's native hover tooltip (already available on every chart,
  labeled or not) for the rest.
- **Combo charts** — label only the series that's actually the story (e.g.
  the overlaid "Total" line), via the per-series value toggle on the chart's
  Data tab, not every bar in a busy stacked-bar-plus-line combo.
- **Pie charts** — unchanged: `pie.percent_visibility` set to `"inside"` or
  `"both"`, never `"off"`.
- **Tables, pivot tables, and single-value displays** (scalar, smartscalar,
  progress/KPI) already show every value directly in the cell/number
  itself — no separate label setting applies.

Load the `visualization` skill to confirm the exact key/value pair Metabase
currently uses for the all/some/none choice and the per-series override
before building — this file governs the *rule*, not a specific key name
that could shift across a Metabase version.

## Number formatting & precision

`config/analysis-config.md`'s "Value formatting" table already decides which
*unit* a field gets (currency/percent/duration/count) — this section is
about consistency and legibility on top of the correct unit:

- **Hold one precision per unit across every card on the same dashboard**
  (don't show one percentage as `42%` and a similar one nearby as `42.31%`).
- **Axis ticks round to clean numbers** (0 / 1,000 / 2,000, not 0 / 947 /
  1,894) and always carry a thousands separator.
- **Large standalone values** (a hero KPI number, a stat-tile value) should
  use Metabase's own compact/auto-formatting for large numbers where the
  `visualization` skill confirms it's available, rather than a raw
  `1284000` a viewer has to parse digit by digit.

## Table & pivot formatting

Governed by CLAUDE.md's "Table formatting" section (center-aligned columns,
cleaned-up date headers, row highlight, `table.cell_column` mini-bar) — not
duplicated here. On top of that baseline, apply Metabase's own conditional
formatting to any table/pivot column where a value crossing a threshold is
part of the insight (not just decoration) — this is the Sequential/Diverging
color jobs above, applied through the table's own formatting rules rather
than a chart's series color.

## Filters & dashboard parameters

- **One filter set, scoping everything it should.** Metabase already renders
  dashboard filters as a single control row above the dashboard's content —
  the discipline this project owns is making sure every card that shares a
  filter's dimension is actually mapped to it (per CLAUDE.md's "Drill-downs"
  visible-filter rule and the dashboard-assembly step in
  `prompts/requirements-intake.md`), never a filter that silently does
  nothing for a card that should respond to it.
- **Reuse before adding.** On an existing dashboard, map new cards to a
  filter that already covers the same dimension rather than creating a
  second, redundant one for the same thing.
- **Date range is usually the filter a viewer reaches for first** — when a
  dashboard has more than one filter, a date-range parameter (where one
  exists) is the natural leftmost/first control.

## Accessibility

CLAUDE.md's "Data labels" (now the revised, density-aware rule above) and
this file's legend rule already put a real number or a legend swatch on
every chart project-wide — that's exactly the visible-label relief this
palette's lower-contrast slots (magenta, yellow, aqua on a light surface)
require. The one thing this file adds on top: never remove Metabase's own
legend for a "cleaner" look on a chart with 2+ series — a legend-less,
color-only distinction is exactly what the `dataviz` skill's method exists
to prevent. The Dark columns in "Categorical color," "Diverging color," and
"Status color" above are already validated against Metabase's dark chart
surface (`#1a1a19`) — if this project ever embeds a dashboard using
Metabase's own dark/night theme, use those values directly rather than
re-deriving new ones; only run `node scripts/validate_palette.js
"<hex,...>" --mode dark --surface "<dark surface hex>"` again if this
standard's hues themselves are ever changed (see "This is fixed, not a
per-client style" below), since that would invalidate the pre-computed
numbers documented above.

## Consistency conventions

- **Title casing** — Title Case for chart and dashboard titles, matching how
  `prompts/requirements-intake.md` presents recommendations.
- **Number precision** — see "Number formatting & precision" above.
- **Chart form consistency** — don't switch chart forms for the same insight
  shape across cards on one dashboard without a reason (e.g. one trend as a
  line, a near-identical adjacent trend as a bar) — pick a form per
  "Choosing the form" above and hold it across the dashboard.

## This is fixed, not a per-client style

These hex values and layout rules are the standing design system for every
Recruit CRM account this project touches — they are never customized,
tuned, or asked-about per client. The one narrow exception: if Recruit CRM
itself ever decides to adopt its own permanent house palette in place of
this reference instance, that's a single, deliberate, project-wide change —
run `node scripts/validate_palette.js "<hex,hex,...>" --mode light` (and
`--mode dark` if ever relevant) from the `dataviz` skill's own base
directory per its "Snap-to-passing" method, then replace this file's color
tables with the resulting validated set for every future account at once —
never a one-off swap for a single client's dashboard.
