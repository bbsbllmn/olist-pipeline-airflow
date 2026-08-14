"""
Reads dbt's target/manifest.json and target/run_results.json after a build,
and asks an LLM to write a short plain-English changelog entry (which models
ran, which tests passed/failed, any new/removed columns vs. the previous
manifest snapshot). Posted after every dbt build so documentation for
stakeholders stays current without manual upkeep.

A copy of the previous manifest is kept at include/ai/.last_manifest.json
(gitignored) purely to diff against -- if it's missing (first run), the
summary just describes the current state instead of a diff.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

DBT_TARGET_DIR = Path(
    os.environ.get("DBT_TARGET_DIR", "/opt/airflow/dbt/olist_analytics/target")
)
LAST_MANIFEST_PATH = Path(__file__).parent / ".last_manifest.json"


def _load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def _summarize_models(manifest: dict, run_results: dict) -> str:
    models = {
        k: v for k, v in manifest.get("nodes", {}).items() if v["resource_type"] == "model"
    }
    status_by_id = {r["unique_id"]: r["status"] for r in run_results.get("results", [])}
    lines = []
    for uid, node in models.items():
        status = status_by_id.get(uid, "not run")
        lines.append(f"{node['name']} ({node.get('config', {}).get('materialized', '?')}): {status}")
    return "\n".join(lines)


def _diff_columns(current: dict, previous: dict | None) -> str:
    if previous is None:
        return "(first run -- no previous manifest to diff against)"

    def cols(manifest: dict) -> dict[str, set[str]]:
        return {
            n["name"]: set(n.get("columns", {}).keys())
            for n in manifest.get("nodes", {}).values()
            if n["resource_type"] == "model"
        }

    cur, prev = cols(current), cols(previous)
    diffs = []
    for model, cur_cols in cur.items():
        prev_cols = prev.get(model, set())
        added, removed = cur_cols - prev_cols, prev_cols - cur_cols
        if added:
            diffs.append(f"{model}: +{sorted(added)}")
        if removed:
            diffs.append(f"{model}: -{sorted(removed)}")
    return "\n".join(diffs) if diffs else "No column-level schema changes since last build."


def generate_changelog() -> str:
    manifest = _load_json(DBT_TARGET_DIR / "manifest.json")
    run_results = _load_json(DBT_TARGET_DIR / "run_results.json")
    previous = _load_json(LAST_MANIFEST_PATH) if LAST_MANIFEST_PATH.exists() else None

    model_summary = _summarize_models(manifest, run_results)
    column_diff = _diff_columns(manifest, previous)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        changelog = f"Model run summary:\n{model_summary}\n\nSchema changes:\n{column_diff}"
    else:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Write a short changelog entry (max 8 bullet points) for a "
                        "data team's #data-eng channel, summarizing this dbt build. "
                        "Group by staging vs. marts, call out any failed models/tests, "
                        "and mention schema changes if any. Be factual, no filler.\n\n"
                        f"Model run results:\n{model_summary}\n\n"
                        f"Schema diff since last build:\n{column_diff}"
                    ),
                }
            ],
        )
        changelog = "".join(b.text for b in message.content if b.type == "text")

    shutil.copy(DBT_TARGET_DIR / "manifest.json", LAST_MANIFEST_PATH)
    return changelog
