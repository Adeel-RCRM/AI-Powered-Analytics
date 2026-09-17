# Visual Design Standards

A house visual style for **new** charts and dashboards this project builds,
so a client's whole set of dashboards reads as one consistent, deliberately
designed system rather than whatever Metabase's own automatic color
assignment happens to produce. Grounded in the `dataviz` skill's
design-system-agnostic method and its validated reference palette
(`references/palette.md` in that skill) — applied here through Metabase's own
`visualization_settings` (`series_settings`, `column_settings`, conditional
formatting), never through CSS or HTML this project doesn't control.

**Scope: governs new work going forward, not retroactive.** Never recolor an
already-shipped client dashboard's cards to match this file unless the user
specifically asks for that — this project only adds/improves what it's asked
to touch, per CLAUDE.md hard constraint 7's spirit.

## Categorical color — series identity

Assign these eight hues, **in this fixed order**, to a chart's distinct
series/categories — never leave color to Metabase's own automatic
assignment, and never cycle past slot 8:

| Slot | Hue | Hex |
|------|-----|-----|
| 1 | blue | `#2a78d6` |
| 2 | orange | `#eb6834` |
| 3 | aqua | `#1baf7a` |
| 4 | yellow | `#eda100` |
| 5 | magenta | `#e87ba4` |
| 6 | green | `#008300` |
| 7 | violet | `#4a3aa7` |
| 8 | red | `#e34948` |

Apply via `visualization_settings.series_settings.<series name>.color` —
load the `visualization` skill for the exact key shape per chart type. This
is the same discipline CLAUDE.md's "Combo chart series display" already
requires for `display`: set the value explicitly for **every** series, not
just the ones that need to differ from a default.

A **single-series** chart still gets slot 1 (`#2a78d6`) set explicitly rather
than left to Metabase's default, so a dashboard's primary metric reads the
same blue everywhere. Beyond **8 distinct categories**, don't invent a 9th
color — fold the rest into "Other," reconsider the chart form (a table lists
more categories legibly than a legend can), or facet, per the `dataviz`
skill's own series-cap rule.

**Color follows the entity, never its rank or a filter's current result** —
if a dashboard filter can change which categories appear, a category keeps
its slot whenever it's present; the survivors don't get repainted just
because a different set showed up.

## Sequential color — magnitude (heatmap / range formatting)

One hue (blue), light → dark, for a table/pivot cell background or range
formatting where the lightest step means "near zero":

| Step | Hex | Step | Hex | Step | Hex | Step | Hex |
|------|-----|------|-----|------|-----|------|-----|
| 100 | `#cde2fb` | 250 | `#86b6ef` | 400 | `#3987e5` | 550 | `#1c5cab` |
| 150 | `#b7d3f6` | 300 | `#6da7ec` | 450 | `#2a78d6` | 600 | `#184f95` |
| 200 | `#9ec5f4` | 350 | `#5598e7` | 500 | `#256abf` | 650 | `#104281` |
| | | | | | | 700 | `#0d366b` |

Apply through a table/pivot's single-color conditional-formatting range —
load the `visualization` skill for the exact keys.

## Diverging color — polarity (over/under a baseline)

Blue ↔ red with a neutral gray midpoint (`#f0efec`), for a metric with a
meaningful "above vs. below a baseline" reading — performance vs. target,
delta from a prior period. Apply through a 3-color conditional-formatting
range, equal steps per arm.

## Status color — fixed, reserved meaning

| Role | Hex |
|------|-----|
| good | `#0ca30c` |
| warning | `#fab219` |
| serious | `#ec835a` |
| critical | `#d03b3b` |

Reserve these for an actual state judgment (e.g. flagging a KPI because it's
under threshold) — never reuse one as "just another series" color. Metabase
can't render an icon inside a formatted cell, so a status color is never the
only signal: pair it with a clear label (the column header, or the KPI's own
title) rather than color alone — two of these steps sit below a 3:1 contrast
on a light surface by design, so a viewer who can't rely on the color still
needs the label to read the state.

## Accessibility — mostly already covered

CLAUDE.md's "Data labels" rule (`graph.show_values` / `pie.percent_visibility`)
already puts a real number on every bar/segment project-wide — that's exactly
the visible-label relief this palette's lower-contrast slots (magenta,
yellow, aqua on a light surface) require, so no extra step is needed on top
of a rule that already applies to every chart. The one thing this file adds:
never remove Metabase's own legend for a "cleaner" look on a chart with 2+
series — a legend-less, color-only distinction is exactly what the
`dataviz` skill's method exists to prevent.

## Consistency conventions

- **Title casing** — Title Case for chart and dashboard titles, matching how
  `prompts/requirements-intake.md` presents recommendations.
- **Number precision** — CLAUDE.md's "Value formatting" already decides which
  *unit* a field gets (currency/percent/duration/count); hold one precision
  per unit across every card on the same dashboard (e.g. don't show one
  percentage as `42%` and a similar one nearby as `42.31%`).
- **Chart form consistency** — don't switch chart forms for the same insight
  shape across cards on one dashboard without a reason (e.g. one trend as a
  line, a near-identical adjacent trend as a bar) — pick a form per the
  `dataviz` skill's `references/choosing-a-form.md` and hold it.

## Swapping in a real brand palette later

These hex values are the `dataviz` skill's validated **reference** palette,
not a Recruit CRM or client brand palette. To swap in a real brand's colors:
run `node scripts/validate_palette.js "<hex,hex,...>" --mode light` (and
`--mode dark` if ever relevant) from the `dataviz` skill's own base
directory, per its "Snap-to-passing" method, and replace this file's tables
with the resulting validated set — keep the structure and rules, swap only
the values.
