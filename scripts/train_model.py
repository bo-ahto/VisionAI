"""Sprint 1 모델 학습 실행 스크립트."""
from __future__ import annotations

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    """Baseline CatBoost 모델을 학습한다."""
    import pandas as pd

    from visionai.price_engine.models.trainer import train_catboost
    from visionai.price_engine.validation.metrics import compute_metrics
    from visionai.price_engine.models.predictor import predict

    df = pd.read_parquet(ROOT / "data" / "preprocessed_features.parquet")

    train = df[df["split"] == "train"]
    valid = df[df["split"] == "valid"]
    test = df[df["split"] == "test"]

    logging.info("Train: %d, Valid: %d, Test: %d", len(train), len(valid), len(test))

    # 학습
    model = train_catboost(
        train_df=train,
        valid_df=valid,
        save_path=ROOT / "model_test_results" / "trained_model.cbm",
    )

    # 평가
    import numpy as np
    y_pred = predict(model, test)
    y_true = test["낙찰가"].astype(float).values
    m = compute_metrics(y_true, y_pred)

    print(f"\n{'='*50}")
    print("학습 완료")
    print(f"{'='*50}")
    print(f"  MAPE:  {m.mape}%")
    print(f"  MdAPE: {m.mdape}%")
    print(f"  R²:    {m.r2}")
    print(f"  N:     {m.n}")


if __name__ == "__main__":
    main()
