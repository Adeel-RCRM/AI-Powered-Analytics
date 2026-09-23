#!/usr/bin/env python3
"""
Build the standard Advanced Analytics "Default Dashboard" for a Recruit CRM
account, replicating the reference dashboard (Metabase dashboard 12908) onto
that account's own data.

Every Metabase operation goes through the `mb` CLI via subprocess - this
script never calls the Metabase REST API directly and never touches a
database driver. It never fabricates data: every table/field/filter value it
uses is discovered live from the target account's own tables, and any entity
that doesn't exist for this account is skipped (not faked).

This script only ever adds new content - it never deletes, archives, or
modifies anything (per CLAUDE.md hard constraint 7). A card whose query
fails dry-run validation is simply never created (see build_card_query /
the dry-run check in main) - nothing gets created and then torn down. If a
"Default Dashboard" already exists for the account, the script stops rather
than touching it (see check_existing_dashboard).

This flow always saves into the account's own collection (see CLAUDE.md
"Where created charts live" - Convention B), never "Data Team WIP" - a
genuine top-level collection (never nested under collection 199), named
"Shared Collection <account>" by default, though some accounts already
have one under a different, custom name (see resolve_account_own_collection).
This script never creates or touches that parent collection itself - if no
matching top-level collection exists for the account, it stops rather than
creating one or falling back to "Data Team WIP". Once found, that
collection mandatorily gets three sub-collections - Cards, Models,
Drill-downs (see ensure_structural_subcollections) - created if missing,
without touching anything already sitting directly in the account's
collection. Every card this script creates lives in a "Default Dashboard
Cards" sub-collection under Cards (see resolve_dashboard_cards_collection);
the dashboard itself is created directly in the account's own collection
and pinned there (`collection_position`). If a "Default Dashboard" already
exists for this account under the old "Data Team WIP" convention (from
before this flow switched to the account's own collection), the script
stops rather than creating a second copy elsewhere (see
check_legacy_dashboard).

Every monetary card (Total Cost of Calls, Deal Target Achieved, Total Deal
Value per Company, Deal Value Closed Over Time) is formatted in the currency
confirmed for this run (see --currency) rather than a hardcoded symbol - a
client could be billed in USD, EUR, GBP, or anything else, and this is never
assumed (see CLAUDE.md "Value formatting"). The confirmed currency is also
written back to references/metric-glossary.md's own "## Account <n>" section
(see record_currency_in_glossary) - the same ask-once-per-account write-back
this project's conversational flows already do - so a later Requirements
Intake session on the same account doesn't re-ask a currency this script
already confirmed.

Every pie's slices, and every multi-series bar/line/row/area card's series,
get an explicit color from references/visual-design-standards.md's fixed
8-hue categorical palette (see apply_series_colors) - assigned by running
that card's own already-validated query live and coloring its real,
distinct category values in a stable alphabetical order, never by rank.
Single-series cards already carry their color in the template itself (a
metric-name-keyed series_settings entry) and are left alone. A genuinely
ordinal breakout (e.g. an ordered pipeline stage) still gets nominal
coloring here rather than the standard's ordinal ramp, since that needs a
per-account confirmed stage order this fully automated flow never asks for.

Every qualifying dashcard also gets a click_behavior drill-down (see CLAUDE.md
"Drill-downs" and prompts/drilldowns.md), built entirely from
default_dashboard_template.json's own "drilldown_entities"/"drilldown_cards"/
per-card "drill" keys via scripts/dashboard_drilldowns.py (shared with
create_important_metrics_dashboard.py): most cards get a single
click_behavior into a shared per-entity detail list; "% Candidates Placed per
Job" (a multi-value pivot) gets its own dedicated drill-down dashboard
instead, since a pivot can't reliably honor a per-column click_behavior. Two
documented simplifications apply project-wide (see dashboard_drilldowns.py's
own docstring): a bucketed/computed breakout dimension is never passed
through as a click target (no raw column to filter against on a plain detail
list), and a multi-series graph card ("Job Status Overview by Company Name")
gets one whole-chart click target keyed on its breakout dimension, not a
per-series split (Metabase's click_behavior model has no per-series concept
outside a `table` display). All drill-down cards/dashboards land in this
account's "Default Dashboard Drill-downs" sub-collection under Drill-downs
(a pivot's own dedicated dashboard goes directly in Drill-downs itself,
unpinned) - never a pre-existing card/dashboard, per hard constraint 7.

Usage:
    python3 scripts/create_default_dashboard.py --profile <mb-profile> [--account <number>] [--currency <ISO code>] [--test-collection-id <id>]

If --account or --currency is omitted, the script prompts for it interactively.
--test-collection-id redirects the whole dashboard/Cards/Models/Drill-downs
structure into an arbitrary collection instead of resolving (and pinning
into) the account's own real collection - see CLAUDE.md "Locating the
account's data" (account 662's "AI Analytics Test Folder (Do Not Touch)").
"""
import argparse
import copy
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import dashboard_drilldowns

TEMPLATE_PATH = Path(__file__).parent / "default_dashboard_template.json"
LOG_PATH = Path(__file__).parent.parent / "logs" / "history.jsonl"
GLOSSARY_PATH = Path(__file__).parent.parent / "references" / "metric-glossary.md"
LEGACY_PARENT_COLLECTION_ID = 199  # "Data Team WIP" - see CLAUDE.md; only
# consulted here to check for a pre-existing dashboard from before this flow
# switched to the account's own collection (see check_legacy_dashboard).
DASHBOARD_NAME = "Default Dashboard"
CARDS_SUBCOLLECTION_NAME = f"{DASHBOARD_NAME} Cards"
DRILLDOWNS_SUBCOLLECTION_NAME = f"{DASHBOARD_NAME} Drill-downs"
STRUCTURAL_SUBCOLLECTIONS = ("Cards", "Models", "Drill-downs")  # mandatory
# under the account's own collection - see CLAUDE.md "Where created charts
# live" (Convention B).
DEFAULT_DEAL_TARGET_GOAL = 1_000_000  # from the reference dashboard's "Deal Target Achieved" card
IST = ZoneInfo("Asia/Kolkata")
# references/visual-design-standards.md "Categorical color" - fixed order, never cycled.
CATEGORICAL_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
# Above this many distinct breakout values, a field isn't well-formed
# categorical data (e.g. a free-text "city" column) - don't pick an
# arbitrary top 8 out of it at all. See assign_categorical_colors.
CATEGORICAL_COLOR_CARDINALITY_CAP = 100


def log_event(event_type, **fields):
    """Append one entry to logs/history.jsonl - see CLAUDE.md "History log"."""
    entry = {"timestamp": datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S+05:30"), "type": event_type, **fields}
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def record_currency_in_glossary(account, currency_code):
    """Write this run's confirmed currency back to
    references/metric-glossary.md - per CLAUDE.md "Value formatting"'s
    ask-once-per-account convention. This project's conversational flows
    already write a confirmed currency back immediately (see
    prompts/discovery.md section 4, prompts/chart-generation.md's currency
    step); this script resolves the exact same per-account fact via
    --currency/an interactive prompt but, before this, only ever recorded it
    in logs/history.jsonl's default_dashboard_created entry - an audit-trail
    fact, not the shared per-account memory a later Requirements Intake
    session on the same account actually checks before re-asking. Idempotent
    and conservative: creates a new `## Account <n>` section if none exists,
    adds a Currency line to an existing section that doesn't have one yet,
    and never silently overwrites an existing Currency line that names a
    different value - it prints a warning instead, leaving reconciliation
    (and this file's own dated `Superseded` convention) to a human. Heading
    matches inside the file's own fenced-code-block *example* section (its
    "## Account sections" walkthrough shows a literal "## Account 662" as a
    template, not a real entry) are skipped - matching that example instead
    of a real section would silently write into throwaway template text."""
    text = GLOSSARY_PATH.read_text()
    heading = f"## Account {account}"
    date_str = datetime.now(IST).strftime("%Y-%m-%d")
    currency_line = (
        f"**Currency:** {currency_code} (confirmed via "
        f"`scripts/create_default_dashboard.py --currency`, {date_str})."
    )

    code_spans = [m.span() for m in re.finditer(r"```.*?```", text, re.DOTALL)]

    def find_real_heading():
        pos = 0
        while True:
            idx = text.find(heading, pos)
            if idx == -1:
                return None
            if not any(s <= idx < e for s, e in code_spans):
                return idx
            pos = idx + 1

    start = find_real_heading()
    if start is not None:
        after_heading = start + len(heading)
        next_heading = re.search(r"\n## ", text[after_heading:])
        end = after_heading + (next_heading.start() if next_heading else len(text) - after_heading)
        section = text[start:end]
        if "**Currency:**" in section:
            if f"**Currency:** {currency_code}" not in section:
                print(f"  NOTE: references/metric-glossary.md already has a different Currency line "
                      f"for Account {account} - not overwriting; reconcile by hand if {currency_code} "
                      "genuinely supersedes it.")
            return
        new_section = section.rstrip("\n") + f"\n\n{currency_line}\n"
        text = text[:start] + new_section + text[end:]
    else:
        marker = "\n## Unattributed"
        new_section = f"\n{heading}\n\n{currency_line}\n"
        if marker in text:
            idx = text.index(marker)
            text = text[:idx] + new_section + text[idx:]
        else:
            text = text.rstrip("\n") + "\n" + new_section

    GLOSSARY_PATH.write_text(text)

# Every Recruit CRM account's data lives in "Production Starrocks" (this is
# the live, queryable copy). Some accounts also have an older, unreachable
# copy of the same tables in the legacy "Recruit CRM" Redshift database
# (id 13371338) - that one must never be used.
STARROCKS_DATABASE_ID = 13371569

# Cards whose value is a monetary sum - see CLAUDE.md "Value formatting".
# Their currency is never assumed (a client could be billed in USD, EUR,
# GBP, etc.) - it's confirmed with the user once per run (see --currency)
# and applied here instead of a hardcoded symbol.
MONETARY_CARD_KEYS = {"total_cost_of_calls", "deal_target_achieved", "total_deal_value_per_company", "deal_value_closed_over_time"}
CURRENCY_CODE_RE = re.compile(r"^[A-Za-z]{3}$")


class MbError(RuntimeError):
    pass


def mb(profile, *args, allow_fail=False):
    """Shell out to the mb CLI. Never talks to Metabase any other way."""
    cmd = ["mb", *args, "--profile", profile, "--json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode not in (0,) and not allow_fail:
        raise MbError(
            f"mb {' '.join(args)} failed (exit {result.returncode}):\n{result.stderr.strip() or result.stdout.strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        if allow_fail:
            return None
        raise MbError(f"mb {' '.join(args)} did not return JSON:\n{result.stdout}\n{result.stderr}")


def mb_body(profile, *args, body):
    """Same as mb(), but writes `body` to a temp JSON file passed via --file."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(body, f)
        tmp_path = f.name
    try:
        return mb(profile, *args, "--file", tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def verify_auth(profile):
    status = mb(profile, "auth", "status", allow_fail=True)
    if status is None or not status.get("present") or status.get("user") is None:
        print(
            "Metabase authentication could not be verified. "
            "Please check the Metabase API key/configuration."
        )
        sys.exit(1)
    return status["url"]


def discover_table(profile, table_name):
    """Find a table by its exact underlying name (e.g. 'candidates_662') on
    Production Starrocks specifically. Returns the table id, or None if not
    found there. Some accounts also have an older, unreachable copy of the
    same tables in the legacy Redshift database ("Recruit CRM", id
    13371338) - that copy must never be used, so the search is scoped to
    Starrocks and the result's database is double-checked defensively.
    The shared warehouse has far too many tables for a full metadata pull, so
    use `mb search` (per CLAUDE.md's "Locating the account's data") and
    confirm the exact raw name via `table get` - search results surface
    `display_name` under `name`, not the raw table name, so a substring
    search alone isn't a reliable exact match."""
    results = mb(profile, "search", table_name, "--models", "table", "--db-id", str(STARROCKS_DATABASE_ID), "--limit", "10")
    for item in results.get("data", []):
        table = mb(profile, "table", "get", str(item["id"]), "--fields", "id,name,db_id")
        if table.get("name") == table_name and table.get("db_id") == STARROCKS_DATABASE_ID:
            return table["id"]
    return None


def get_fields(profile, table_id):
    """name -> field id map for a table, paginating if needed."""
    fields = {}
    offset = 0
    while True:
        resp = mb(profile, "table", "fields", str(table_id), "--offset", str(offset))
        for f in resp.get("data", []):
            fields[f["name"]] = f["id"]
        if not resp.get("has_more"):
            break
        offset = resp["next_offset"]
    return fields


def resolve_entities(profile, account, template):
    """For every entity referenced by the template, find this account's real
    table + field map. Entities that don't exist are omitted (not faked)."""
    resolved = {}
    for entity, prefix in template["entity_table_prefix"].items():
        table_name = f"{prefix}_{account}"
        table_id = discover_table(profile, table_name)
        if table_id is None:
            print(f"  - {table_name}: not found on Production Starrocks, skipping cards for '{entity}'")
            continue
        fields = get_fields(profile, table_id)
        resolved[entity] = {"table_id": table_id, "fields": fields, "table_name": table_name}
        print(f"  - {table_name}: table {table_id}, {len(fields)} fields")
    return resolved


def remap_field_ids(node, field_names, name_to_new_id):
    """Walk dataset_query, replacing every ['field', {...}, old_id] with the
    equivalent new field id, and return the set of old ids we couldn't map."""
    missing = set()

    def walk(n):
        if isinstance(n, list):
            if len(n) == 3 and n[0] == "field" and isinstance(n[2], (int, float)):
                old_id = int(n[2])
                col_name = field_names.get(str(old_id))
                new_id = name_to_new_id.get(col_name) if col_name else None
                if new_id is None:
                    missing.add(old_id)
                else:
                    n[2] = new_id
                return
            for x in n:
                walk(x)
        elif isinstance(n, dict):
            for v in n.values():
                walk(v)

    walk(node)
    return missing


def find_equality_literals(node, field_names, acc):
    """Scan a dataset_query for ['=', {...}, ['field', {...}, id], <literal>]
    triples so we can verify the literal category value actually occurs in
    this account's data before trusting a filter/count-where on it."""
    if isinstance(node, list):
        if (
            len(node) == 4
            and node[0] == "="
            and isinstance(node[2], list)
            and node[2][0] == "field"
            and isinstance(node[3], str)
        ):
            old_id = int(node[2][2])
            col_name = field_names.get(str(old_id))
            if col_name:
                acc.append((col_name, node[3]))
        for x in node:
            find_equality_literals(x, field_names, acc)
    elif isinstance(node, dict):
        for v in node.values():
            find_equality_literals(v, field_names, acc)


def distinct_values(profile, database_id, table_id, field_id):
    query = {
        "lib/type": "mbql/query",
        "database": database_id,
        "stages": [{"lib/type": "mbql.stage/mbql", "source-table": table_id, "breakout": [["field", {}, field_id]]}],
    }
    result = mb_body(profile, "query", body=query)
    return {row[0] for row in result.get("data", {}).get("rows", [])}


def build_card_query(profile, card, resolved):
    entity = resolved.get(card["entity"])
    if entity is None:
        return None, f"entity '{card['entity']}' not available for this account"

    query = copy.deepcopy(card["dataset_query"])
    query["database"] = STARROCKS_DATABASE_ID
    query["stages"][0]["source-table"] = entity["table_id"]

    missing = remap_field_ids(query, card["field_names"], entity["fields"])
    if missing:
        return None, f"fields {missing} not found on {entity['table_name']}"

    # Verify every literal category value (e.g. hiring_stage = "Placed") this
    # card depends on actually occurs in the account's real data - stage/
    # status label values are not guaranteed portable across accounts.
    literals = []
    find_equality_literals(card["dataset_query"], card["field_names"], literals)
    for col_name, literal in literals:
        field_id = entity["fields"].get(col_name)
        if field_id is None:
            continue
        values = distinct_values(profile, STARROCKS_DATABASE_ID, entity["table_id"], field_id)
        if literal not in values:
            return None, f"value '{literal}' not found in {entity['table_name']}.{col_name} (has: {sorted(values)[:8]})"

    return query, None


def validate_and_create_card(profile, name, display, query, visualization_settings, collection_id):
    """Dry-run validate then create - same validation pipeline as the report
    cards below, factored out for the drill-down detail/metric cards, which
    don't go through build_card_query's template-remap path (their queries
    are already fully resolved when this is called)."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(query, f)
        tmp_path = f.name
    validation = subprocess.run(
        ["mb", "query", "--file", tmp_path, "--dry-run", "--profile", profile, "--json"],
        capture_output=True, text=True,
    )
    Path(tmp_path).unlink(missing_ok=True)
    if validation.returncode != 0:
        return None, "query failed dry-run validation"
    body = {
        "name": name,
        "display": display,
        "dataset_query": query,
        "visualization_settings": visualization_settings or {},
        "collection_id": collection_id,
    }
    result = mb_body(profile, "card", "create", body=body)
    return result["id"], None


def apply_deal_goal(card, visualization_settings, deal_goal):
    if card["key"] == "deal_target_achieved":
        visualization_settings = copy.deepcopy(visualization_settings)
        visualization_settings["progress.goal"] = deal_goal
    return visualization_settings


def apply_currency_formatting(card, visualization_settings, currency_code):
    """Format this card's monetary total using the currency confirmed with
    the user (see CLAUDE.md "Value formatting") - never a hardcoded symbol,
    since a client could be billed in USD, EUR, GBP, or anything else."""
    if card["key"] not in MONETARY_CARD_KEYS:
        return visualization_settings
    visualization_settings = copy.deepcopy(visualization_settings)
    column_settings = visualization_settings.setdefault("column_settings", {})
    column_settings['["name","sum"]'] = {
        "number_style": "currency",
        "currency": currency_code,
        "currency_style": "symbol",
    }
    return visualization_settings


def rank_values_by_metric(rows, dim_idx, metric_idx):
    """Sum each breakout value's real metric total across every row it
    appears in (a pie has one row per value; a 2-dimension cartesian series
    can repeat across x-axis buckets) - this is what decides which values
    are prominent enough on the actual rendered chart to be worth an
    explicit color, not the values' names."""
    totals = {}
    for row in rows:
        if not row or dim_idx >= len(row):
            continue
        value = row[dim_idx]
        if value is None:
            continue
        metric = row[metric_idx] if metric_idx is not None and metric_idx < len(row) else None
        totals[value] = totals.get(value, 0) + (metric if isinstance(metric, (int, float)) else 0)
    return totals


def assign_categorical_colors(value_totals):
    """Pick the fixed 8-hue categorical palette for the values that actually
    dominate the chart (by real summed metric total, ties broken
    alphabetically for a deterministic result on reruns) - magnitude only
    decides WHICH values earn an explicit color, never the color's own
    intensity (see references/visual-design-standards.md's 'Never
    color-rank a nominal category': that rule bans a magnitude-driven
    lightness ramp on a nominal field; each chosen value still gets one
    flat palette hue, same as any other categorical slot). The 9th value
    and beyond are left uncolored (Metabase's own default) rather than
    cycling the palette or inventing a slot the standard doesn't define -
    Metabase's own pie.slice_threshold/legend already recede a long tail
    visually, so this is consistent with, not a workaround for, that.
    Above CATEGORICAL_COLOR_CARDINALITY_CAP distinct values, this isn't
    coloring a bounded set of categories at all (a free-text field with
    thousands of dirty values, e.g. an unstructured "city" column) - see
    references/visual-design-standards.md's pie/all-pairs caps and CLAUDE.md's
    "Data quality gate" - so nothing gets colored, not even a top-8 guess,
    rather than implying those 8 particular values were deliberately chosen
    as meaningful."""
    if len(value_totals) > CATEGORICAL_COLOR_CARDINALITY_CAP:
        return {}
    ranked = sorted(value_totals.items(), key=lambda kv: (-kv[1], str(kv[0])))
    return {str(v): CATEGORICAL_PALETTE[i] for i, (v, _) in enumerate(ranked) if i < len(CATEGORICAL_PALETTE)}


def apply_series_colors(profile, card, query, visualization_settings):
    """Color a pie's slices, or a multi-series bar/line/row/area chart's
    series, using this account's real category values - run live via the
    card's own already-validated query, never guessed or hardcoded (a
    template can't know an account's actual Call Type/Deal Stage/source
    values in advance). See references/visual-design-standards.md's
    'Categorical color'. This treats every breakout value as nominal
    (assign_categorical_colors' flat, never value-ranked slots); a
    genuinely ordinal dimension (e.g. a hiring/deal pipeline stage, where
    order carries meaning) would need this account's confirmed stage order
    instead (CLAUDE.md's hiring-stage-order rule, never queried/invented) -
    out of reach for this fully automated, no-per-account-questions flow,
    so a pie/series breakout on a stage-like field still gets nominal
    coloring here rather than the ordinal ramp a conversational
    Requirements Intake build would use. A card that already carries its
    own explicit color (pie.colors/pie.rows, or series_settings) is left
    completely alone. Single-series cards (one dimension, one-or-more named
    metrics) already carry their color directly in the template via a
    metric-name-keyed series_settings entry and are left untouched too
    (skipped by the len(dims) != 2 check)."""
    display = card["display"]
    if display == "pie":
        if "pie.colors" in visualization_settings or "pie.rows" in visualization_settings:
            return visualization_settings
        result = mb_body(profile, "query", "--max-bytes", "0", body=query)
        cols = [c["name"] for c in result.get("data", {}).get("cols", [])]
        rows = result.get("data", {}).get("rows", [])
        if len(cols) < 2:
            return visualization_settings
        dim_col = visualization_settings.get("pie.dimension") or cols[0]
        if isinstance(dim_col, list):  # concentric rings - color only the innermost
            dim_col = dim_col[0]
        metric_col = visualization_settings.get("pie.metric") or cols[-1]
        if dim_col not in cols or metric_col not in cols:
            return visualization_settings
        totals = rank_values_by_metric(rows, cols.index(dim_col), cols.index(metric_col))
        colors = assign_categorical_colors(totals)
        if not colors:
            return visualization_settings
        visualization_settings = copy.deepcopy(visualization_settings)
        visualization_settings["pie.colors"] = colors
        return visualization_settings

    if display in ("bar", "line", "area", "row"):
        dims = visualization_settings.get("graph.dimensions") or []
        if len(dims) != 2 or "series_settings" in visualization_settings:
            return visualization_settings
        series_col = dims[1]
        result = mb_body(profile, "query", "--max-bytes", "0", body=query)
        cols = [c["name"] for c in result.get("data", {}).get("cols", [])]
        rows = result.get("data", {}).get("rows", [])
        if series_col not in cols:
            return visualization_settings
        metrics = visualization_settings.get("graph.metrics") or []
        metric_col = metrics[0] if metrics else cols[-1]
        if metric_col not in cols:
            return visualization_settings
        totals = rank_values_by_metric(rows, cols.index(series_col), cols.index(metric_col))
        colors = assign_categorical_colors(totals)
        if not colors:
            return visualization_settings
        visualization_settings = copy.deepcopy(visualization_settings)
        visualization_settings["series_settings"] = {v: {"color": hexcode} for v, hexcode in colors.items()}
        return visualization_settings

    return visualization_settings


def find_collection_node(node, target_id):
    """`mb collection tree` takes no id argument - it always returns the
    whole tree from the true root, regardless of what's passed - so finding
    a non-root collection's children means walking the tree ourselves. Every
    call site passes `--max-bytes 0` (uncapped) defensively, though the real
    tree (well past `mb`'s default 24576-byte cap once an account's own
    collection has more than a handful of children) turned out not to
    actually get truncated by the default cap either way - so that wasn't
    the cause of a real, observed failure mode: two script runs against the
    same account close together in time (confirmed at ~9 minutes, and again
    within about a minute) each created their own "Cards"/"Models"/
    "Drill-downs" instead of sharing one, because `resolve_child_collection`
    below didn't see the first run's newly created sub-collection in its own
    tree fetch - looks like server-side staleness in the collection-tree
    endpoint under load, not anything this script controls. Rather than
    chase that further, `resolve_child_collection` below is self-healing
    against it (a second, independent lookup via `mb collection items`
    before *and* after creating - see its own docstring) instead of relying
    on this tree fetch alone."""
    if node["id"] == target_id:
        return node
    for child in node.get("children", []):
        found = find_collection_node(child, target_id)
        if found is not None:
            return found
    return None


def find_child_collection(profile, parent_id, name):
    """Look up a child collection of `parent_id` by exact (trimmed) name via
    `mb collection items` - a targeted, per-collection listing, distinct
    from the whole-tree fetch `resolve_child_collection` also tries below.
    Returns the lowest (= earliest-created) matching id, or None. Used both
    as a second opinion before creating and as the post-create self-heal
    recheck - see resolve_child_collection's docstring."""
    items = mb(profile, "collection", "items", str(parent_id), "--models", "collection", "--max-bytes", "0")
    matches = [i for i in items.get("data", []) if i.get("name", "").strip() == name]
    if not matches:
        return None
    return min(matches, key=lambda i: i["id"])["id"]


def resolve_child_collection(profile, parent_id, name):
    """Find a child collection of `parent_id` by exact (trimmed) name, or
    create it if it doesn't exist yet. Returns (collection_id, created).

    Self-healing against a confirmed race: two script runs against the same
    account close together in time (observed at ~9 minutes and again at
    ~1 minute apart) each created their own "Cards"/"Models"/"Drill-downs"
    instead of sharing one - `mb collection tree`'s view of what the other
    run had already created was stale (see find_collection_node's docstring;
    root cause unconfirmed, likely server-side). Rather than trying to prove
    a read is fresh before trusting it, this checks via a second, independent
    lookup (`mb collection items`, not `collection tree`) both before
    creating and immediately after - a collection is guaranteed empty the
    instant it's created, so if that second check turns up an *older*
    sibling with the same name, the new one is simply archived and the
    older one's id returned instead. Safe and correct regardless of which
    lookup (if either) was actually stale."""
    tree = mb(profile, "collection", "tree", "--max-bytes", "0")
    root = tree[0] if isinstance(tree, list) else tree
    parent_node = find_collection_node(root, parent_id)
    for child in (parent_node.get("children", []) if parent_node else []):
        if child["name"].strip() == name:
            return child["id"], False

    existing = find_child_collection(profile, parent_id, name)
    if existing is not None:
        return existing, False

    created = mb_body(
        profile, "collection", "create",
        body={"name": name, "parent_id": parent_id},
    )
    new_id = created["id"]

    older = find_child_collection(profile, parent_id, name)
    if older is not None and older != new_id:
        mb(profile, "collection", "archive", str(new_id), allow_fail=True)
        return older, False

    return new_id, True


def resolve_account_own_collection(profile, account):
    """Find this account's own client-facing collection - a genuine
    top-level collection (parent_id null, never nested under "Data Team
    WIP") named "Shared Collection <account>" by default, though some
    accounts already have one under a different, custom name (see
    CLAUDE.md "Where created charts live" - Convention B). `mb collection
    tree` returns a flat list of every top-level collection (each carrying
    its own nested `children`) - matched here by the account number
    appearing in one of *those* top-level names, never by descending into
    any collection's children (that would also catch "Data Team WIP"
    sub-collections sharing the same number, which are a different
    convention). This project never creates this parent collection itself -
    returns (None, None) if nothing matches, and the caller must stop."""
    tree = mb(profile, "collection", "tree", "--max-bytes", "0")
    if not isinstance(tree, list):
        tree = [tree]
    matches = [c for c in tree if account in c["name"]]
    if not matches:
        return None, None
    if len(matches) > 1:
        print(f"  Multiple top-level collections match account {account}:")
        for c in matches:
            print(f"    {c['id']}: {c['name']!r}")
        chosen = input("  Which collection id is this account's own collection? ").strip()
        for c in matches:
            if str(c["id"]) == chosen:
                return c["id"], c["name"]
        print(f"  '{chosen}' doesn't match any of the listed collection ids.")
        sys.exit(1)
    return matches[0]["id"], matches[0]["name"]


def ensure_structural_subcollections(profile, parent_id):
    """Ensure the account's own collection has its three mandatory
    sub-collections - Cards, Models, Drill-downs (see CLAUDE.md "Where
    created charts live" - Convention B) - creating whichever are missing.
    Never touches anything else already sitting in the parent collection."""
    return {name: resolve_child_collection(profile, parent_id, name)[0] for name in STRUCTURAL_SUBCOLLECTIONS}


def resolve_dashboard_cards_collection(profile, cards_collection_id):
    """This run's cards live in a 'Default Dashboard Cards' sub-collection
    under the account's own collection's Cards folder."""
    return resolve_child_collection(profile, cards_collection_id, CARDS_SUBCOLLECTION_NAME)


def search_dashboards_by_name(profile, name):
    """`mb search --models dashboard`'s compact (non---full) item shape
    always carries `collection_id: null` - the real value only exists as a
    nested `collection.id` in `--full` output, or via `--fields
    id,name,collection.id` in compact mode (much smaller than `--full`,
    since search results carry a lot of ranking/metadata bulk otherwise).
    Confirmed live: a naive `item.get("collection_id")` check against this
    command's default output never matches anything, silently defeating
    every "does this dashboard already exist" guard in this project that
    used it - see check_existing_dashboard/check_legacy_dashboard below."""
    results = mb(profile, "search", name, "--models", "dashboard", "--limit", "50", "--fields", "id,name,collection.id")
    return results.get("data", [])


def check_legacy_dashboard(profile, account):
    """Look for a 'Default Dashboard' already sitting in this account's old
    'Data Team WIP' sub-collection, from before this flow switched to the
    account's own collection (see CLAUDE.md "Where created charts live" -
    "Avoiding a duplicate across the two conventions"). Returns
    (dashboard_id, collection_id), or (None, None) if there isn't one."""
    tree = mb(profile, "collection", "tree", "--max-bytes", "0")
    root = tree[0] if isinstance(tree, list) else tree
    wip_node = find_collection_node(root, LEGACY_PARENT_COLLECTION_ID)
    if wip_node is None:
        return None, None
    for child in wip_node.get("children", []):
        if child["name"].strip() == account:
            legacy_collection_id = child["id"]
            for item in search_dashboards_by_name(profile, DASHBOARD_NAME):
                if (item.get("collection") or {}).get("id") == legacy_collection_id and item.get("name") == DASHBOARD_NAME:
                    return item["id"], legacy_collection_id
    return None, None


def check_existing_dashboard(profile, account_collection_id):
    for item in search_dashboards_by_name(profile, DASHBOARD_NAME):
        if (item.get("collection") or {}).get("id") == account_collection_id and item.get("name") == DASHBOARD_NAME:
            return item["id"]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="mb CLI profile to use (confirm via mb auth list/status first)")
    parser.add_argument("--account", help="Recruit CRM account number. Prompted for if omitted.")
    parser.add_argument("--deal-target-goal", type=float, default=DEFAULT_DEAL_TARGET_GOAL,
                         help=f"Goal value for the 'Deal Target Achieved' card (default: {DEFAULT_DEAL_TARGET_GOAL}, taken from the reference dashboard)")
    parser.add_argument("--currency", help="ISO 4217 code (e.g. USD, EUR, GBP, INR) for this account's monetary "
                         "charts (Total Cost of Calls, Deal Target Achieved, Total Deal Value per Company, Deal "
                         "Value Closed Over Time). Never assumed - prompted for if omitted (see CLAUDE.md "
                         "\"Value formatting\").")
    parser.add_argument("--test-collection-id", type=int, help="Skip resolving the account's own client-facing "
                         "collection and use this collection id instead as the target for the dashboard/Cards/"
                         "Models/Drill-downs structure - for testing against a dedicated scratch collection "
                         "(e.g. account 662's 'AI Analytics Test Folder (Do Not Touch)') instead of a real "
                         "client-facing one. See CLAUDE.md \"Locating the account's data\".")
    args = parser.parse_args()

    profile = args.profile

    currency_code = args.currency
    while not currency_code or not CURRENCY_CODE_RE.match(currency_code):
        if currency_code:
            print(f"'{currency_code}' doesn't look like a 3-letter ISO 4217 currency code - try again.")
        currency_code = input("Which currency should this account's monetary charts be formatted in "
                               "(ISO code, e.g. USD, EUR, GBP, INR)? ").strip()
    currency_code = currency_code.upper()

    print(f"Verifying Metabase authentication for profile '{profile}'...")
    base_url = verify_auth(profile)
    print(f"  authenticated against {base_url}")

    account = args.account or input("Which Recruit CRM account would you like to build the default dashboard for? Please provide the account number: ").strip()
    if not account:
        print("No account number provided.")
        sys.exit(1)

    template = json.loads(TEMPLATE_PATH.read_text())

    print(f"\nResolving account {account}'s tables...")
    resolved = resolve_entities(profile, account, template)
    if not resolved:
        reason = f"no tables found on Production Starrocks for account {account} (looked for e.g. 'candidates_{account}')"
        print(f"\nNo tables found for account {account} (looked for e.g. 'candidates_{account}'). "
              "Please verify the account number.")
        log_event("default_dashboard_failed", account=account, reason=reason, profile=profile)
        sys.exit(1)

    if args.test_collection_id:
        account_collection_id = args.test_collection_id
        account_collection_name = f"test collection override {account_collection_id}"
        print(f"\nUsing --test-collection-id override: collection {account_collection_id} "
              "(skipping account-collection resolution and the legacy-dashboard check - this is a scratch run).")
    else:
        print(f"\nResolving account {account}'s own collection...")
        account_collection_id, account_collection_name = resolve_account_own_collection(profile, account)
        if account_collection_id is None:
            print(f"\nNo existing top-level account collection found for account {account} (looked for the "
                  f"account number in a genuine top-level collection's name, e.g. 'Shared Collection {account}', "
                  "outside 'Data Team WIP'). This project never creates that parent collection itself - it needs "
                  "to exist first. Please create it (or tell me its existing name/id) and re-run.")
            log_event("default_dashboard_failed", account=account, collection_mode="account_collection",
                      reason="no existing top-level account collection found", profile=profile)
            sys.exit(1)
        print(f"  collection {account_collection_id} ({account_collection_name!r})")

        legacy_dashboard_id, legacy_collection_id = check_legacy_dashboard(profile, account)
        if legacy_dashboard_id:
            print(f"\nA '{DASHBOARD_NAME}' (id {legacy_dashboard_id}) already exists in this account's old "
                  f"'Data Team WIP' collection (id {legacy_collection_id}), from before this flow switched to "
                  "the account's own collection. Stopping rather than creating a second copy elsewhere.")
            log_event("default_dashboard_skipped", account=account, collection_mode="account_collection",
                      dashboard_id=legacy_dashboard_id, collection_id=legacy_collection_id,
                      reason=f"{DASHBOARD_NAME} already exists in legacy Data Team WIP collection", profile=profile)
            sys.exit(1)

    structural = ensure_structural_subcollections(profile, account_collection_id)
    print(f"  Cards {structural['Cards']}, Models {structural['Models']}, Drill-downs {structural['Drill-downs']}")

    cards_collection_id, cards_created = resolve_dashboard_cards_collection(profile, structural["Cards"])
    print(f"  '{CARDS_SUBCOLLECTION_NAME}' collection {cards_collection_id} ({'created' if cards_created else 'existing'})")

    existing = check_existing_dashboard(profile, account_collection_id)
    if existing:
        print(f"\nA '{DASHBOARD_NAME}' (id {existing}) already exists in this account's collection. "
              "Stopping rather than creating a duplicate.")
        log_event("default_dashboard_skipped", account=account, collection_mode="account_collection",
                  dashboard_id=existing, collection_id=account_collection_id,
                  reason=f"{DASHBOARD_NAME} already exists", profile=profile)
        sys.exit(1)

    print(f"\nCreating cards ({len(template['cards'])} in template)...")
    created_cards = {}  # key -> {id, tab, layout, param_mappings, entity}
    skipped = []
    for card in template["cards"]:
        query, err = build_card_query(profile, card, resolved)
        if err:
            skipped.append((card["name"], err))
            print(f"  SKIP  {card['name']}: {err}")
            continue

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(query, f)
            tmp_path = f.name
        validation = subprocess.run(
            ["mb", "query", "--file", tmp_path, "--dry-run", "--profile", profile, "--json"],
            capture_output=True, text=True,
        )
        Path(tmp_path).unlink(missing_ok=True)
        if validation.returncode != 0:
            skipped.append((card["name"], f"query failed validation: {validation.stdout or validation.stderr}"))
            print(f"  SKIP  {card['name']}: failed dry-run validation")
            continue

        viz = apply_deal_goal(card, card["visualization_settings"], args.deal_target_goal)
        viz = apply_currency_formatting(card, viz, currency_code)
        viz = apply_series_colors(profile, card, query, viz)
        body = {
            "name": card["name"],
            "display": card["display"],
            "dataset_query": query,
            "visualization_settings": viz,
            "collection_id": cards_collection_id,
        }
        result = mb_body(profile, "card", "create", body=body)
        created_cards[card["key"]] = {
            "id": result["id"],
            "tab": card["tab"],
            "layout": card["layout"],
            "param_mappings": card["param_mappings"],
            "entity": card["entity"],
        }
        print(f"  OK    {card['name']} -> card {result['id']}")

    if not created_cards:
        print("\nNo cards could be created for this account. Nothing to assemble into a dashboard.")
        log_event("default_dashboard_failed", account=account, collection_mode="account_collection",
                  reason="no cards could be created", cards_skipped=[{"name": n, "reason": r} for n, r in skipped],
                  profile=profile)
        sys.exit(1)

    print(f"\nCreated {len(created_cards)}/{len(template['cards'])} cards ({len(skipped)} skipped).")

    print("\nResolving drill-down collection...")
    drilldowns_collection_id, _ = resolve_child_collection(profile, structural["Drill-downs"], DRILLDOWNS_SUBCOLLECTION_NAME)
    print(f"  '{DRILLDOWNS_SUBCOLLECTION_NAME}' collection {drilldowns_collection_id}")

    print("\nBuilding drill-down detail cards...")
    param_names = {p["slug"]: p["name"] for p in template["dashboard_parameters"]}
    cards_by_key = {c["key"]: c for c in template["cards"]}
    entity_detail_cards = {}  # entity key -> card id
    for entity_key, spec in template.get("drilldown_entities", {}).items():
        entity = resolved.get(entity_key)
        if entity is None:
            continue
        builder = dashboard_drilldowns.build_entity_detail_query_dedup if spec["dedup"] else dashboard_drilldowns.build_entity_detail_query
        query, viz, missing_cols = builder(STARROCKS_DATABASE_ID, entity["table_id"], entity["fields"], spec["columns"])
        if query is None:
            print(f"  SKIP  {entity_key} detail: none of its display columns exist on this account's table")
            continue
        name = f"{DASHBOARD_NAME}: {entity_key.replace('_', ' ').title()} Detail"
        card_id, err = validate_and_create_card(profile, name, "table", query, viz, drilldowns_collection_id)
        if err:
            print(f"  SKIP  {entity_key} detail: {err}")
            continue
        entity_detail_cards[entity_key] = card_id
        print(f"  OK    {entity_key} detail -> card {card_id}" + (f" (missing columns: {missing_cols})" if missing_cols else ""))
        log_event("drilldown_added", account=account, kind="entity_detail", entity=entity_key,
                  card_id=card_id, collection_id=drilldowns_collection_id)

    extra_drilldown_cards = {}  # drilldown_cards key -> card id
    for card in template.get("drilldown_cards", []):
        query, err = build_card_query(profile, card, resolved)
        if err:
            print(f"  SKIP  {card['name']}: {err}")
            continue
        card_id, err = validate_and_create_card(profile, card["name"], card.get("display", "table"),
                                                  query, card.get("visualization_settings", {}), drilldowns_collection_id)
        if err:
            print(f"  SKIP  {card['name']}: {err}")
            continue
        extra_drilldown_cards[card["key"]] = card_id
        print(f"  OK    {card['name']} -> card {card_id}")
        log_event("drilldown_added", account=account, kind="metric_detail", key=card["key"],
                  card_id=card_id, collection_id=drilldowns_collection_id)

    def resolve_drill_target(target_key):
        return entity_detail_cards.get(target_key, extra_drilldown_cards.get(target_key))

    print("\nBuilding pivot drill-down dashboards...")
    pivot_dashboards = {}  # report card key -> {"dashboard_id": ..., "row_params": [...]}
    for key, c in created_cards.items():
        drill = cards_by_key[key].get("drill")
        if not drill or drill["kind"] != "pivot_dashboard":
            continue
        value_card_ids = sorted({resolve_drill_target(t) for t in drill["value_cards"].values() if resolve_drill_target(t) is not None})
        if not value_card_ids:
            print(f"  SKIP  {drill['dashboard_name']}: no underlying value cards available")
            continue
        row_params = [
            {"slug": dim, "id": f"pivotparam{i}", "name": dim.replace("_", " ").title(),
             "type": "date/all-options" if dim.endswith("_on") or dim.endswith("_date") else "string/="}
            for i, dim in enumerate(drill["row_dimensions"])
        ]
        pivot_dashcards = []
        dcid = -1
        for i, card_id in enumerate(value_card_ids):
            pm = []
            for p in row_params:
                new_fid = resolved[c["entity"]]["fields"].get(p["slug"])
                if new_fid is None:
                    continue
                pm.append({"parameter_id": p["id"], "target": ["dimension", ["field", new_fid, None]]})
            pivot_dashcards.append({"id": dcid, "card_id": card_id, "row": i * 6, "col": 0,
                                     "size_x": 24, "size_y": 6, "parameter_mappings": pm})
            dcid -= 1
        pivot_body = {
            "name": drill["dashboard_name"],
            "description": "",  # never omit - an unset description persists as null, which breaks the dashboard header's description box in the Metabase UI
            "collection_id": structural["Drill-downs"],
            "dashcards": pivot_dashcards,
            "parameters": [{"id": p["id"], "name": p["name"], "slug": p["slug"], "type": p["type"]} for p in row_params],
        }
        pivot_dashboard = mb_body(profile, "dashboard", "create", body=pivot_body)
        pivot_dashboards[key] = {"dashboard_id": pivot_dashboard["id"], "row_params": row_params}
        print(f"  OK    {drill['dashboard_name']} -> dashboard {pivot_dashboard['id']}")
        log_event("drilldown_added", account=account, kind="pivot_dashboard", key=key,
                  dashboard_id=pivot_dashboard["id"], collection_id=structural["Drill-downs"])

    print("\nAssembling dashboard...")
    tabs_present = []
    for t in template["tabs"]:
        if any(c["tab"] == t for c in created_cards.values()):
            tabs_present.append(t)
    tab_ids = {name: -(i + 1) for i, name in enumerate(tabs_present)}

    dashcards = []
    dashcard_id = -1
    drilldowns_wired = 0
    for key, c in created_cards.items():
        parameter_mappings = []
        param_sources = []  # (parameter_id, parameter_name, target_field_ref) for click_behavior
        for pm in c["param_mappings"]:
            new_field_id = resolved[c["entity"]]["fields"].get(pm["column_name"])
            if new_field_id is None:
                continue
            parameter_mappings.append({
                "parameter_id": pm["parameter_slug"],
                "target": ["dimension", ["field", new_field_id, None]],
            })
            param_sources.append((pm["parameter_slug"], param_names.get(pm["parameter_slug"], pm["parameter_slug"]),
                                   dashboard_drilldowns.field_ref(new_field_id)))

        dashcard = {
            "id": dashcard_id,
            "card_id": c["id"],
            "dashboard_tab_id": tab_ids[c["tab"]],
            "row": c["layout"]["row"],
            "col": c["layout"]["col"],
            "size_x": c["layout"]["size_x"],
            "size_y": c["layout"]["size_y"],
            "parameter_mappings": parameter_mappings,
        }

        drill = cards_by_key[key].get("drill")
        column_sources = []
        if drill and drill["kind"] in ("single", "per_column"):
            orig_card = cards_by_key[key]
            col_names = dashboard_drilldowns.last_stage_breakout_columns(
                orig_card["dataset_query"], lambda oid, oc=orig_card: oc["field_names"].get(str(oid)))
            for cn in col_names:
                new_fid = resolved[c["entity"]]["fields"].get(cn)
                if new_fid is not None:
                    column_sources.append((cn, cn, dashboard_drilldowns.field_ref(new_fid)))

        if drill and drill["kind"] == "single":
            target_id = resolve_drill_target(drill["target"])
            if target_id is not None:
                cb = dashboard_drilldowns.click_behavior_link(target_id, column_sources, param_sources)
                dashcard["visualization_settings"] = {"click_behavior": cb}
                drilldowns_wired += 1
        elif drill and drill["kind"] == "per_column":
            col_settings = {}
            for agg_name, target_key in drill["columns"].items():
                target_id = resolve_drill_target(target_key)
                if target_id is None:
                    continue
                cb = dashboard_drilldowns.click_behavior_link(target_id, column_sources, param_sources)
                col_settings[json.dumps(["name", agg_name], separators=(",", ":"))] = {"click_behavior": cb}
            if col_settings:
                dashcard["visualization_settings"] = {"column_settings": col_settings}
                drilldowns_wired += 1
        elif drill and drill["kind"] == "pivot_dashboard":
            pv = pivot_dashboards.get(key)
            if pv is not None:
                mappings = [(p["id"], "column", p["slug"], p["slug"]) for p in pv["row_params"]]
                cb = dashboard_drilldowns.click_behavior_dashboard_link(pv["dashboard_id"], mappings)
                dashcard["visualization_settings"] = {"click_behavior": cb}
                drilldowns_wired += 1

        dashcards.append(dashcard)
        dashcard_id -= 1

    parameters = []
    for p in template["dashboard_parameters"]:
        if p["slug"] == "recruiter" and "call_logs" not in resolved:
            continue  # only call-log cards use this filter
        parameters.append({
            "id": p["slug"],
            "name": p["name"],
            "slug": p["slug"],
            "type": p["type"],
            **({"default": p["default"]} if "default" in p else {}),
        })

    dashboard_body = {
        "name": DASHBOARD_NAME,
        "description": "",  # never omit - an unset description persists as null, which breaks the dashboard header's description box in the Metabase UI
        "collection_id": account_collection_id,
        "collection_position": 1,  # pinned - see CLAUDE.md "Where created charts live"
        "tabs": [{"id": tab_ids[name], "name": name, "position": i} for i, name in enumerate(tabs_present)],
        "dashcards": dashcards,
        "parameters": parameters,
    }
    dashboard = mb_body(profile, "dashboard", "create", body=dashboard_body)
    dashboard_id = dashboard["id"]

    print(f"  dashboard {dashboard_id} created")

    print("\nVerifying...")
    verify = mb(profile, "dashboard", "get", str(dashboard_id), "--fields", "id,name,collection_id")
    assert verify["id"] == dashboard_id

    print(f"\nDone. '{DASHBOARD_NAME}' (id {dashboard_id}) for account {account}:")
    print(f"  {len(created_cards)} cards created in '{CARDS_SUBCOLLECTION_NAME}' (collection {cards_collection_id}), "
          f"{len(skipped)} skipped, dashboard pinned in collection {account_collection_id} ({account_collection_name!r})")
    print(f"  {drilldowns_wired}/{len(created_cards)} dashcards wired with a drill-down "
          f"({len(entity_detail_cards)} entity detail cards, {len(extra_drilldown_cards)} metric detail cards, "
          f"{len(pivot_dashboards)} pivot drill-down dashboards, in '{DRILLDOWNS_SUBCOLLECTION_NAME}' / 'Drill-downs')")
    if skipped:
        print("  Skipped:")
        for name, reason in skipped:
            print(f"    - {name}: {reason}")
    print(f"  {base_url}/dashboard/{dashboard_id}")

    log_event(
        "default_dashboard_created",
        account=account,
        collection_mode="account_collection",
        dashboard_id=dashboard_id,
        collection_id=account_collection_id,
        cards_collection_id=structural["Cards"],
        models_collection_id=structural["Models"],
        drilldowns_collection_id=structural["Drill-downs"],
        charts_collection_id=cards_collection_id,
        cards_created=len(created_cards),
        cards_skipped=[{"name": n, "reason": r} for n, r in skipped],
        drilldowns_created=len(entity_detail_cards) + len(extra_drilldown_cards) + len(pivot_dashboards),
        drilldowns_wired=drilldowns_wired,
        profile=profile,
        currency=currency_code,
    )
    record_currency_in_glossary(account, currency_code)


if __name__ == "__main__":
    main()
