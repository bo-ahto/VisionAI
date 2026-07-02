#!/usr/bin/env python3
"""Build a dry-run canonical artist merge map for official v0.1.

The script consumes the reviewed priority candidate table and creates a proposed
canonical artist-key map for P0/P1 identity split candidates. It does not update
the SQLite DB. Overlapping candidate groups are merged into connected
components, then each component chooses the artist_key with the largest current
valid_price_count as canonical.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[2]
DB_PATH = REPO / "data" / "track6" / "service_v0_1" / "price_prediction_v0_1.sqlite"
PRIORITY_CSV = (
    REPO
    / "experiments"
    / "track6"
    / "PP-OFFICIAL-V01_identity_external_review_priority"
    / "identity_external_review_priority.csv"
)
OUT_DIR = REPO / "experiments" / "track6" / "PP-OFFICIAL-V01_artist_identity_merge_dry_run"
DOC_JSON = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_merge_dry_run.json"
DOC_MD = REPO / "docs" / "track6" / "experiments" / "price_prediction_official_v0_1_artist_identity_merge_dry_run.md"
CREATED_AT = datetime.now().astimezone().isoformat(timespec="seconds")


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        self.parent.setdefault(item, item)
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, a: str, b: str) -> None:
        root_a = self.find(a)
        root_b = self.find(b)
        if root_a != root_b:
            self.parent[root_b] = root_a

    def groups(self) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for item in list(self.parent):
            grouped[self.find(item)].append(item)
        return {key: sorted(values) for key, values in grouped.items()}


def load_json_list(value: object) -> list[str]:
    try:
        parsed = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    priority = pd.read_csv(PRIORITY_CSV)
    priority = priority[priority["priority_tier"].isin(["P0_identity_merge_first", "P1_identity_merge_review"])].copy()
    with sqlite3.connect(DB_PATH) as conn:
        registry = pd.read_sql_query("SELECT * FROM artist_registry", conn)
        aliases = pd.read_sql_query("SELECT artist_key, alias_text, alias_normalized, source FROM artist_aliases", conn)
        observations = pd.read_sql_query("SELECT artist_key, COUNT(*) AS observation_rows FROM artwork_price_observations GROUP BY artist_key", conn)
    return priority, registry, aliases, observations


def build_components(priority: pd.DataFrame) -> tuple[dict[str, list[str]], dict[str, list[dict[str, Any]]]]:
    union_find = UnionFind()
    evidence_by_root_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for _, row in priority.iterrows():
        keys = load_json_list(row.get("candidate_artist_keys_json"))
        if len(keys) < 2:
            continue
        first = keys[0]
        union_find.find(first)
        for key in keys[1:]:
            union_find.union(first, key)
        evidence = {
            "priority_tier": row.get("priority_tier"),
            "normalized_alias": row.get("normalized_alias"),
            "normalized_aliases": load_json_list(row.get("normalized_aliases_json")),
            "split_loss_price_count": int(row.get("split_loss_price_count") or 0),
            "max_abs_price_delta_pct": float(row.get("max_abs_price_delta_pct") or 0.0),
            "candidate_artist_keys": keys,
        }
        for key in keys:
            evidence_by_root_key[key].append(evidence)
    groups = union_find.groups()
    evidence_by_root: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for root, keys in groups.items():
        seen = set()
        for key in keys:
            for evidence in evidence_by_root_key.get(key, []):
                marker = json.dumps(evidence, ensure_ascii=False, sort_keys=True)
                if marker in seen:
                    continue
                seen.add(marker)
                evidence_by_root[root].append(evidence)
    return groups, evidence_by_root


def choose_canonical(keys: list[str], registry_by_key: pd.DataFrame) -> str:
    rows = registry_by_key.loc[[key for key in keys if key in registry_by_key.index]].copy()
    if rows.empty:
        return sorted(keys)[0]
    rows = rows.reset_index(drop=True)
    rows["valid_price_count"] = pd.to_numeric(rows["valid_price_count"], errors="coerce").fillna(0).astype(int)
    rows = rows.sort_values(["valid_price_count", "artist_key"], ascending=[False, True])
    return str(rows.iloc[0]["artist_key"])


def build_dry_run() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    priority, registry, aliases, observations = load_inputs()
    groups, evidence_by_root = build_components(priority)
    registry_by_key = registry.set_index("artist_key", drop=False)
    obs_by_key = observations.set_index("artist_key")["observation_rows"].to_dict()
    alias_count_by_key = aliases.groupby("artist_key").size().to_dict() if not aliases.empty else {}
    component_rows: list[dict[str, Any]] = []
    map_rows: list[dict[str, Any]] = []

    for root, keys in groups.items():
        if len(keys) < 2:
            continue
        canonical = choose_canonical(keys, registry_by_key)
        component_registry = registry_by_key.loc[[key for key in keys if key in registry_by_key.index]].copy()
        birth_years = sorted({
            int(value)
            for value in pd.to_numeric(component_registry.get("birth_year"), errors="coerce").dropna().tolist()
        }) if not component_registry.empty else []
        valid_counts = {
            key: int(registry_by_key.loc[key]["valid_price_count"])
            for key in keys
            if key in registry_by_key.index
        }
        source_keys = [key for key in keys if key != canonical]
        reassigned_observations = int(sum(int(obs_by_key.get(key, 0)) for key in source_keys))
        reassigned_aliases = int(sum(int(alias_count_by_key.get(key, 0)) for key in source_keys))
        evidences = evidence_by_root.get(root, [])
        priority_tiers = sorted({str(item.get("priority_tier")) for item in evidences})
        aliases_for_review = sorted({
            alias
            for item in evidences
            for alias in ([str(item.get("normalized_alias"))] + [str(v) for v in item.get("normalized_aliases", [])])
            if alias and alias != "nan"
        })
        component_id = f"artistmerge_{len(component_rows) + 1:04d}"
        component_rows.append({
            "component_id": component_id,
            "canonical_artist_key": canonical,
            "component_artist_keys_json": json.dumps(keys, ensure_ascii=False),
            "source_artist_keys_json": json.dumps(source_keys, ensure_ascii=False),
            "priority_tiers_json": json.dumps(priority_tiers, ensure_ascii=False),
            "aliases_for_review_json": json.dumps(aliases_for_review, ensure_ascii=False),
            "distinct_birth_years_json": json.dumps(birth_years, ensure_ascii=False),
            "requires_human_confirmation": bool(len(birth_years) > 1),
            "combined_valid_price_count": int(sum(valid_counts.values())),
            "canonical_valid_price_count": int(valid_counts.get(canonical, 0)),
            "reassigned_valid_price_count": int(sum(valid_counts.get(key, 0) for key in source_keys)),
            "reassigned_observation_rows": reassigned_observations,
            "reassigned_alias_rows": reassigned_aliases,
            "evidence_group_count": int(len(evidences)),
        })
        for source_key in source_keys:
            map_rows.append({
                "component_id": component_id,
                "from_artist_key": source_key,
                "to_canonical_artist_key": canonical,
                "from_valid_price_count": int(valid_counts.get(source_key, 0)),
                "from_observation_rows": int(obs_by_key.get(source_key, 0)),
                "from_alias_rows": int(alias_count_by_key.get(source_key, 0)),
                "requires_human_confirmation": bool(len(birth_years) > 1),
                "dry_run_only": True,
            })

    components = pd.DataFrame(component_rows).sort_values(
        ["requires_human_confirmation", "reassigned_valid_price_count", "reassigned_observation_rows"],
        ascending=[True, False, False],
    ).reset_index(drop=True)
    merge_map = pd.DataFrame(map_rows)
    registry_count = int(len(registry))
    source_key_count = int(merge_map["from_artist_key"].nunique()) if not merge_map.empty else 0
    payload = {
        "created_at": CREATED_AT,
        "priority_input_rows": int(len(priority)),
        "merge_component_rows": int(len(components)),
        "merge_edge_rows": int(len(merge_map)),
        "source_artist_keys_to_merge": source_key_count,
        "current_artist_registry_rows": registry_count,
        "projected_artist_registry_rows_after_merge": registry_count - source_key_count,
        "reassigned_valid_price_count": int(components["reassigned_valid_price_count"].sum()) if not components.empty else 0,
        "reassigned_observation_rows": int(components["reassigned_observation_rows"].sum()) if not components.empty else 0,
        "components_requiring_human_confirmation": int(components["requires_human_confirmation"].sum()) if not components.empty else 0,
        "dry_run_only": True,
    }
    return components, merge_map, payload


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 20) -> str:
    if frame.empty:
        return "- 없음\n"
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in frame[columns].head(max_rows).iterrows():
        values = [str(row.get(col, "")).replace("\n", " ") for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(components: pd.DataFrame, merge_map: pd.DataFrame, payload: dict[str, Any]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_JSON.parent.mkdir(parents=True, exist_ok=True)
    components_csv = OUT_DIR / "artist_identity_merge_components_dry_run.csv"
    map_csv = OUT_DIR / "artist_identity_merge_map_dry_run.csv"
    components.to_csv(components_csv, index=False)
    merge_map.to_csv(map_csv, index=False)
    payload = {
        **payload,
        "components_csv": str(components_csv.relative_to(REPO)),
        "merge_map_csv": str(map_csv.relative_to(REPO)),
    }
    DOC_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [
        "# 공식 v0.1 작가 식별자 병합 dry-run",
        "",
        f"- 작성일: {CREATED_AT}",
        "- 적용 여부: 실제 DB 미수정",
        f"- 병합 component: {payload['merge_component_rows']:,}건",
        f"- 병합 대상 source artist_key: {payload['source_artist_keys_to_merge']:,}건",
        f"- 재배치될 가격 이력 수: {payload['reassigned_valid_price_count']:,}건",
        f"- 재배치될 관측 row 수: {payload['reassigned_observation_rows']:,}건",
        f"- 예상 artist_registry row 수: {payload['current_artist_registry_rows']:,} -> {payload['projected_artist_registry_rows_after_merge']:,}",
        "",
        "## 1. 결론",
        "",
        "- P0/P1 동일 작가 분리 후보를 바로 병합하지 않고 dry-run map으로 분리했다.",
        "- 겹치는 후보 그룹은 연결 component로 합쳐 한 artist_key가 여러 번 이동하지 않게 했다.",
        "- 실제 적용 전에는 component별 대표 작품, 생년, 국적, 외부 출처를 확인해야 한다.",
        "",
        "## 2. 상위 병합 component",
        "",
        markdown_table(
            components,
            [
                "component_id",
                "canonical_artist_key",
                "component_artist_keys_json",
                "aliases_for_review_json",
                "distinct_birth_years_json",
                "combined_valid_price_count",
                "reassigned_valid_price_count",
                "reassigned_observation_rows",
                "requires_human_confirmation",
            ],
            30,
        ),
        "",
        "## 3. 산출물",
        "",
        f"- Component CSV: `{payload['components_csv']}`",
        f"- Merge map CSV: `{payload['merge_map_csv']}`",
        f"- JSON: `{str(DOC_JSON.relative_to(REPO))}`",
    ]
    DOC_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    components, merge_map, payload = build_dry_run()
    payload = write_outputs(components, merge_map, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
