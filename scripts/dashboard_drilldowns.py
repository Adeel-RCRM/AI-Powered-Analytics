"""
Shared drill-down building blocks for create_default_dashboard.py and
create_important_metrics_dashboard.py.

Both scripts otherwise keep their own self-contained copies of `mb`/`mb_body`/
`resolve_child_collection`/etc. (an existing, deliberate convention - see each
script's own docstring) - that duplication is left alone here. This module
holds only the click_behavior/detail-card logic that's genuinely identical in
both scripts, per CLAUDE.md's Drill-downs section and prompts/drilldowns.md.

Nothing here talks to Metabase directly - every function is a pure JSON
builder. The calling script is still the one shelling out to `mb`.

## What this covers, and what it deliberately simplifies

Every dashcard on both dashboards resolves to one of:
  - a **single** dashcard-level click_behavior into a shared per-entity detail
    list (the large majority - see click_behavior_link / last_stage_breakout_columns)
  - a **per-column** click_behavior on a multi-metric `table` card
    (column_settings[...]['click_behavior'] - same click_behavior_link shape,
    just nested differently - see CLAUDE.md "Drilling into one aggregated
    metric out of several on the same card")
  - a **dedicated drill-down dashboard** for a multi-metric `pivot` card,
    since a pivot doesn't reliably honor a per-column click_behavior (see
    click_behavior_dashboard_link and prompts/drilldowns.md "Drill-downs for
    a pivot table")
  - no click_behavior at all, when the card's own query has no `aggregation`
    clause at all (already the most granular view - e.g. "Job's Opening
    Duration")

Three deliberate, documented simplifications (both scripts' module docstrings
call out the first two explicitly - this isn't a silent gap):

  1. **A breakout dimension built from an `["expression", ...]` clause (a
     bucketed/computed dimension, e.g. work-experience-in-years bucketed into
     "0-2"/"3-4"/... text ranges) is never passed through as a click_behavior
     column source.** A plain entity detail list has no equivalent bucketed
     column to filter against - passing the clicked bucket's label through as
     an equality filter on the *raw* underlying field would silently produce
     wrong (usually empty) results, which is worse than the chart simply
     having one fewer dimension wired through. See
     `last_stage_breakout_columns` below.
  2. **A multi-series graph card (more than one entry in
     `visualization_settings["graph.metrics"]`, e.g. a stacked row/bar chart
     with several real series) gets one dashcard-level click_behavior keyed
     on its breakout dimension(s) only - never a per-series split.**
     Metabase's click_behavior model has no per-series concept for graph
     displays (only per-column, and only on a `table`), so there is no
     mechanism to send different series' clicks to different destinations on
     a bar/row/line/area/combo card. This is different from the genuine
     per-column case, which only applies to `table`/`pivot` displays.
  3. **A denormalized name field with no profile field of its own on the
     same table (e.g. Assignments' `candidate_full_name`, Call Logs'
     `related_company_name`, Deals' `candidate_name`/`company_name`/
     `job_name`) is shown as plain text, never linked.** The entity-profile-
     link recipe in prompts/drilldowns.md covers this case by joining to the
     named entity's own table for its profile field (see that file's rule 2)
     - this module's `build_entity_detail_query[_dedup]` only pairs a name
     column with a profile column already present on the *same* table (see
     their `profile_field` display_columns option), so a name field that
     would need a join to reach its profile column simply stays unlinked
     text instead. Entities whose own table carries the field directly
     (Candidates, Jobs, Companies, Contacts) are unaffected.
"""
import json


def field_ref(field_id, base_type=None, join_alias=None):
    """Classic-MBQL field ref: ['field', <id>, {options}] - id first, options
    second. This is the grammar `parameter_mappings`/`click_behavior`
    dimension refs use throughout this project (see both scripts' existing
    `parameter_mappings` construction) - distinct from the options-first
    `dataset_query` pMBQL grammar the *card query itself* is written in."""
    opts = {}
    if base_type:
        opts["base-type"] = base_type
    if join_alias:
        opts["join-alias"] = join_alias
    return ["field", field_id, opts]


def dimension_ref(fref, stage_number=0):
    return ["dimension", fref, {"stage-number": stage_number}]


def _compact(obj):
    return json.dumps(obj, separators=(",", ":"))


def click_behavior_link(target_card_id, column_sources=None, parameter_sources=None):
    """The confirmed custom-destination click_behavior shape (per
    prompts/drilldowns.md "The confirmed click_behavior shape for
    custom-destination filtering") - used both as a whole-dashcard
    `visualization_settings.click_behavior` (single-metric case) and nested
    under `column_settings.<col>.click_behavior` (per-column case).

    column_sources / parameter_sources: lists of (source_id, source_name,
    target_field_ref) triples. A "column" source is a dynamic value from the
    clicked row (source_id/source_name = the output column name on the
    *clicked* card); a "parameter" source is the current value of a
    dashboard filter bound to the clicked card (source_id = that parameter's
    id, source_name = its display name, e.g. "Date"). target_field_ref is a
    field_ref() into the *destination* card's own query."""
    mapping = {}
    for source_id, source_name, target_fref in column_sources or []:
        dref = dimension_ref(target_fref)
        key = _compact(dref)
        mapping[key] = {
            "source": {"type": "column", "id": source_id, "name": source_name},
            "target": {"type": "dimension", "id": key, "dimension": dref},
            "id": key,
        }
    for param_id, param_name, target_fref in parameter_sources or []:
        dref = dimension_ref(target_fref)
        key = _compact(dref)
        mapping[key] = {
            "source": {"type": "parameter", "id": param_id, "name": param_name},
            "target": {"type": "dimension", "id": key, "dimension": dref},
            "id": key,
        }
    return {"type": "link", "linkType": "question", "targetId": target_card_id, "parameterMapping": mapping}


def click_behavior_dashboard_link(target_dashboard_id, mappings):
    """The confirmed pivot-table dedicated-drill-down-dashboard click_behavior
    shape (per prompts/drilldowns.md "Drill-downs for a pivot table") - set
    on the pivot's own dashcard-level `click_behavior`, targeting a whole
    dashboard rather than a single question.

    mappings: list of (dest_param_id, source_kind, source_id, source_name)
    tuples - dest_param_id is the destination dashboard's own filter
    parameter id (its `parameters[].id`, an opaque slug/string); source_kind
    is "column" (the pivot's own clicked-row breakout value) or "parameter"
    (a dashboard filter already bound to the pivot)."""
    mapping = {}
    for dest_param_id, source_kind, source_id, source_name in mappings:
        mapping[dest_param_id] = {
            "source": {"type": source_kind, "id": source_id, "name": source_name},
            "target": {"type": "parameter", "id": dest_param_id},
            "id": dest_param_id,
        }
    return {"type": "link", "linkType": "dashboard", "targetId": target_dashboard_id, "parameterMapping": mapping}


def last_stage_breakout_columns(dataset_query, resolve_column_name):
    """Return the column names of every plain `['field', {opts}, id]`
    breakout entry in the query's LAST stage (the stage that produces what's
    actually displayed) - skipping any `['expression', ...]` breakout entry
    (see module docstring, simplification 1). `resolve_column_name(old_id)`
    maps a template's original field id back to its column name - the
    default script's flat `field_names` map, or the important-metrics
    script's `field_entity_map` (old_id -> {entity, column}), depending on
    which template this card came from."""
    stage = dataset_query["stages"][-1]
    names = []
    for b in stage.get("breakout", []):
        if isinstance(b, list) and len(b) == 3 and b[0] == "field" and isinstance(b[2], (int, float)):
            name = resolve_column_name(int(b[2]))
            if name:
                names.append(name)
    return names


def build_entity_detail_query(database_id, table_id, fields_by_name, display_columns):
    """Build one plain entity-detail-list dataset_query + visualization_settings.

    display_columns: list of dicts, each one of:
      - {"column": "<field name>", "label": "<header>"} - a plain visible
        column.
      - {"column": "<name field>", "label": "<header>", "profile_field":
        "<profile field name>"} - a name column that gets replaced by its
        profile-link column when that profile field exists on this account's
        table (per prompts/drilldowns.md's entity-profile-link recipe: the
        plain name column is hidden, the profile column is shown formatted
        as a link with its link_text pulling in the plain name) - falls back
        to just showing the plain name column, unlinked, when the profile
        field isn't present for this account (never assumed to carry over).

    This builds a plain `fields`-based row list - correct for an entity with
    no duplicate `id` values (Jobs, Candidates, Contacts, Companies, Call
    Logs). For a duplicate-id table (Assignments, Deals - see CLAUDE.md's
    data-model section), use build_entity_detail_query_dedup instead, which
    builds a `breakout`-only stage (no `aggregation` clause - the MBQL
    equivalent of `SELECT DISTINCT`) over the same columns, which is what
    actually prevents duplicate-id row inflation. The calling script's
    `drilldown_entities` template spec says which one applies per entity.

    Returns (dataset_query, visualization_settings, missing_columns) -
    missing_columns lists any *non-profile* display_columns whose field
    wasn't found on this account's table (dropped, not fatal - same "skip
    what can't be built" pattern as the rest of this project)."""
    return _build_entity_detail_query(database_id, table_id, fields_by_name, display_columns, dedup=False)


def build_entity_detail_query_dedup(database_id, table_id, fields_by_name, display_columns):
    """Same as build_entity_detail_query, but for a duplicate-id table
    (Assignments, Deals - see CLAUDE.md's data-model section): a
    `breakout`-only stage with no `aggregation` clause, the MBQL equivalent
    of `SELECT DISTINCT` over exactly the displayed columns - required so
    the detail list doesn't show one row per stage-history/collaborator
    event instead of one row per candidate-job-pair/deal."""
    return _build_entity_detail_query(database_id, table_id, fields_by_name, display_columns, dedup=True)


def _build_entity_detail_query(database_id, table_id, fields_by_name, display_columns, dedup):
    resolved = []  # list of (kind, field_id, column_name, label)
    missing = []
    for dc in display_columns:
        profile_field = dc.get("profile_field")
        profile_id = fields_by_name.get(profile_field) if profile_field else None
        name_id = fields_by_name.get(dc["column"])
        if profile_id is not None and name_id is not None:
            resolved.append(("profile", profile_id, profile_field, dc.get("label", dc["column"]), dc["column"], name_id))
        elif name_id is not None:
            resolved.append(("plain", name_id, dc["column"], dc.get("label", dc["column"]), None, None))
        else:
            missing.append(dc["column"])

    if not resolved:
        return None, None, missing

    field_entries = []
    table_columns = []
    column_settings = {}
    for kind, fid, col_name, label, link_text_col, hidden_name_id in resolved:
        field_entries.append(["field", {}, fid])
        if kind == "profile":
            table_columns.append({"name": col_name, "enabled": True})
            table_columns.append({"name": link_text_col, "enabled": False})
            field_entries.append(["field", {}, hidden_name_id])
            column_settings[_compact(["name", col_name])] = {
                "view_as": "link",
                "link_text": "{{" + link_text_col + "}}",
                "column_title": label,
            }
        else:
            table_columns.append({"name": col_name, "enabled": True})
            column_settings[_compact(["name", col_name])] = {"column_title": label}

    stage = {"lib/type": "mbql.stage/mbql", "source-table": table_id}
    if dedup:
        stage["breakout"] = field_entries
    else:
        stage["fields"] = field_entries

    query = {"lib/type": "mbql/query", "database": database_id, "stages": [stage]}
    viz = {"table.columns": table_columns, "column_settings": column_settings}
    return query, viz, missing
