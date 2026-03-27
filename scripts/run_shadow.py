"""Shadow deployment 실행 스크립트.

1단계: 최신 경매 데이터에 대해 예측 기록 (shadow_recorder)
2단계: 결과 확정 후 scoring (shadow_scorer)
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
ROOT = Path(__file__).resolve().parent.parent


def cmd_record(args: argparse.Namespace) -> None:
    """새 경매 데이터에 대해 shadow 예측을 기록한다."""
    import pandas as pd

    from visionai.price_engine.models.predictor import load_model
    from visionai.price_engine.models.segment_calibrator import fit_calibration
    from visionai.price_engine.models.target_transform import predict_transform
    from visionai.price_engine.experiments.shadow_recorder import batch_record

    df = pd.read_parquet(ROOT / "data" / "preprocessed_features.parquet")
    model = load_model(ROOT / "model_test_results" / "target_transform_v1.cbm")

    # Calibration from validation set
    valid = df[df["split"] == "valid"]
    y_pred_v = predict_transform(model, valid)
    y_true_v = valid["낙찰가"].astype(float).values
    est_v = ((valid["추정가(최저)"].astype(float) + valid["추정가(최고)"].astype(float)) / 2).values
    factors = fit_calibration(y_true_v, y_pred_v, valid["타입"].values, est_v)

    # test set을 "새 경매"로 간주하여 shadow 기록
    target = df[df["split"] == "test"]
    if args.limit:
        target = target.head(args.limit)

    count = batch_record(model, target, factors)
    print(f"\n✅ Shadow 기록 완료: {count}건")


def cmd_score(args: argparse.Namespace) -> None:
    """shadow 기록에 실제 결과를 매칭하고 리포트를 생성한다."""
    import pandas as pd

    from visionai.price_engine.experiments.shadow_scorer import (
        generate_shadow_report,
        load_shadow_logs,
        score_shadow_logs,
    )

    records = load_shadow_logs()

    # 실제 결과: test set에서 가져옴
    df = pd.read_parquet(ROOT / "data" / "preprocessed_features.parquet")
    test = df[df["split"] == "test"]

    actuals = {}
    for _, row in test.iterrows():
        key = (row["타입"], int(row["회차"]), int(row["Lot"]))
        actuals[key] = int(row["낙찰가"])

    scored_df = score_shadow_logs(records, actuals)
    report = generate_shadow_report(scored_df)
    print(report)

    # 결과 저장
    out_path = ROOT / "data" / "shadow_logs" / "scored_results.parquet"
    scored_df.to_parquet(out_path, index=False)
    print(f"\nScoring 결과 저장: {out_path}")


def main() -> None:
    """Shadow deployment CLI."""
    parser = argparse.ArgumentParser(description="Shadow deployment")
    sub = parser.add_subparsers(dest="command")

    rec = sub.add_parser("record", help="새 경매 예측 기록")
    rec.add_argument("--limit", type=int, default=None, help="기록 건수 제한")

    sub.add_parser("score", help="실제 결과 매칭 + 리포트")

    args = parser.parse_args()
    if args.command == "record":
        cmd_record(args)
    elif args.command == "score":
        cmd_score(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
