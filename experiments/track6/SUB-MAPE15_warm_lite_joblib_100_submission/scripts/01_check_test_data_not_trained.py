#!/usr/bin/env python3
"""시험 데이터 100건이 모델 학습 이력에 포함되지 않았는지 확인한다.

이 스크립트는 가격 예측 성능 시험을 실행하기 전에 먼저 수행하는 사전 확인용이다.
시험 입력 데이터의 `_track6_row_id`와 모델 파일 안의 학습 이력 `track6_row_id`를 비교하여
겹치는 row id가 0건인지 확인한다.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd


# 제출 패키지 루트 폴더.
ROOT = Path(__file__).resolve().parents[1]

# 시험 입력 데이터와 모델 학습 이력이 들어 있는 파일 위치.
FEATURES = ROOT / "data" / "price_test_features_100.csv"
STORE = ROOT / "model_bundle" / "artifacts" / "runtime_store.joblib"
OUT = ROOT / "outputs" / "precheck_not_trained"


def main() -> None:
    # 결과 파일을 저장할 폴더를 만든다.
    OUT.mkdir(parents=True, exist_ok=True)

    # 시험 데이터 100건을 읽는다.
    # 여기의 _track6_row_id가 학습 이력에 있으면 안 된다.
    features = pd.read_csv(FEATURES, low_memory=False)
    test_ids = pd.to_numeric(features["_track6_row_id"], errors="coerce").dropna().astype(int)

    # 모델 파일 안에 동결되어 있는 학습 이력 테이블을 읽는다.
    # 이 테이블은 모델이 학습/운영 기준으로 참고하는 train-only 작품 이력이다.
    store = joblib.load(STORE)
    train_history = store["artist_train_history"].copy()
    train_ids = pd.to_numeric(train_history["track6_row_id"], errors="coerce").dropna().astype(int)

    # 시험 데이터 row id와 학습 이력 row id의 교집합을 계산한다.
    # 교집합이 0건이면 시험 데이터 100건이 학습 이력에 직접 포함되지 않았다는 뜻이다.
    overlap_ids = sorted(set(test_ids.tolist()) & set(train_ids.tolist()))
    overlap_rows = features[features["_track6_row_id"].isin(overlap_ids)].copy()

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "features": str(FEATURES.relative_to(ROOT)),
        "model_store": str(STORE.relative_to(ROOT)),
        "test_row_count": int(len(features)),
        "test_unique_row_id_count": int(test_ids.nunique()),
        "train_history_row_count": int(len(train_history)),
        "train_history_unique_track6_row_id_count": int(train_ids.nunique()),
        "train_history_duplicate_track6_row_id_count": int(train_ids.duplicated().sum()),
        "overlap_row_id_count": int(len(overlap_ids)),
        "overlap_track6_row_ids": overlap_ids,
        "passes_not_trained_100_check": len(features) == 100
        and test_ids.nunique() == 100
        and len(overlap_ids) == 0,
    }

    # 상세 결과를 파일로 저장한다.
    overlap_rows.to_csv(OUT / "overlap_rows.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 사전 확인에 실패하면 종료 코드를 1로 반환하여 다음 시험을 진행하지 않도록 한다.
    if not summary["passes_not_trained_100_check"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
