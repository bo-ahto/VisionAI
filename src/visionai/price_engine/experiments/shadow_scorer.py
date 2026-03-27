"""Shadow Mode — Retrospective Scorer.

경매 결과 확정 후 shadow 기록과 대조하여 실제 MAPE를 산출한다.
기획서 참조: 9장 #10
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from visionai.price_engine.validation.metrics import compute_metrics

logger = logging.getLogger(__name__)

SHADOW_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "shadow_logs"


def load_shadow_logs(
    shadow_dir: Path | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """shadow 기록을 로드한다.

    Args:
        shadow_dir: 기록 디렉토리.
        date_from: "YYYYMMDD" 시작일 (포함).
        date_to: "YYYYMMDD" 종료일 (포함).
    """
    if shadow_dir is None:
        shadow_dir = SHADOW_DIR

    records = []
    for f in sorted(shadow_dir.glob("shadow_*.jsonl")):
        file_date = f.stem.replace("shadow_", "")
        if date_from and file_date < date_from:
            continue
        if date_to and file_date > date_to:
            continue

        with open(f, encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Malformed JSON skipped: %s line %d", f.name, line_num)

    logger.info("Loaded %d shadow records", len(records))
    return records


def score_shadow_logs(
    records: list[dict],
    actuals: dict[tuple[str, int, int], int] | None = None,
) -> pd.DataFrame:
    """shadow 기록에 실제 결과를 매칭하고 MAPE를 산출한다.

    Args:
        records: shadow 기록 리스트.
        actuals: {(타입, 회차, Lot): 낙찰가} 딕셔너리. None이면 record 내 actual 사용.

    Returns:
        DataFrame: 타입, 회차, Lot, predicted, actual, ape, scored.
    """
    # dedupe by record_id (같은 경매 건의 중복 기록 제거)
    seen_ids: set[str] = set()
    rows = []
    duplicates = 0

    for r in records:
        rid = r.get("record_id", "")
        if rid and rid in seen_ids:
            duplicates += 1
            continue
        if rid:
            seen_ids.add(rid)

        inp = r["input"]
        pred = r["prediction"]["predicted_calibrated"]

        actual = None
        if actuals:
            key = (inp["타입"], inp["회차"], inp["Lot"])
            actual = actuals.get(key)
        elif r.get("actual") is not None:
            actual = r["actual"]

        # actual ≤ 0은 scored=False 처리 (비정상 값)
        if actual is not None and actual <= 0:
            logger.warning("Invalid actual ≤ 0: %s 회차%d Lot%d", inp["타입"], inp["회차"], inp["Lot"])
            actual = None

        ape = abs(actual - pred) / actual * 100 if actual and actual > 0 else None

        rows.append({
            "record_id": rid,
            "타입": inp["타입"],
            "회차": inp["회차"],
            "Lot": inp["Lot"],
            "predicted": pred,
            "actual": actual,
            "ape": ape,
            "scored": actual is not None,
        })

    if duplicates > 0:
        logger.info("Deduplicated %d records", duplicates)

    return pd.DataFrame(rows)


def generate_shadow_report(scored_df: pd.DataFrame) -> str:
    """shadow scoring 리포트를 생성한다."""
    lines = ["=" * 60, "Shadow Mode Retrospective Report", "=" * 60]

    scored = scored_df[scored_df["scored"]]
    if len(scored) == 0:
        lines.append("\n아직 scoring된 기록이 없습니다.")
        return "\n".join(lines)

    y_true = scored["actual"].astype(float).values
    y_pred = scored["predicted"].astype(float).values
    m = compute_metrics(y_true, y_pred)

    lines.append(f"\n전체: MAPE={m.mape}%  MdAPE={m.mdape}%  ±20%={m.within_20pct}%  N={m.n}")

    # 타입별
    for atype in ["메이저", "프리미엄", "위클리"]:
        mask = scored["타입"] == atype
        if mask.sum() > 0:
            mt = compute_metrics(y_true[mask.values], y_pred[mask.values])
            lines.append(f"  {atype}: MAPE={mt.mape}%  N={mt.n}")

    pending = len(scored_df) - len(scored)
    lines.append(f"\n미scoring: {pending}건")

    return "\n".join(lines)
