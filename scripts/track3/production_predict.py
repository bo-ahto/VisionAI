"""Track 3 Production — 예측 API.

운영 라우팅 (PR2 결과 반영):
  train_count >= 1 → Warm LGB (artist signal)
  train_count == 0 → Cold LAD (unseen artist)

Usage:
    from production_predict import Predictor

    p = Predictor()
    result = p.predict({
        "artist_name_ko": "황선태",
        "medium_category": "oil",
        "support_category": "canvas",
        "width_cm": 60.6, "height_cm": 50.0, "depth_cm": 0,
        "estimated_ho": 12.0,
        "orientation": "landscape",
        # source_platform 제거됨 (학습에 사용 안 함)
    })
    # result = {
    #     "predicted_price_krw": 2_500_000,
    #     "model_used": "warm",
    #     "confidence": "high",  # high / medium / low
    #     "warning": None,
    # }
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent.parent
PROD_DIR = REPO / "data" / "production"

COLD_FEATURES = ["medium_category", "support_category", "has_depth",
                 "log_area", "estimated_ho", "orientation",
                 "medium_ho_bucket",
                 "artist_works_log", "aspect_ratio"]
COLD_CAT = ["medium_category", "support_category", "orientation",
            "medium_ho_bucket"]
WARM_FEATURES = COLD_FEATURES + ["artist_name_ko"]
WARM_CAT = COLD_CAT + ["artist_name_ko"]

HIGH_PRICE_COLD_THRESHOLD = 30_000_000  # 예측 가격이 이 이상이면 Cold 예측 신뢰 낮음


class Predictor:
    """Track 3 production predictor — Cold/Warm 자동 라우팅."""

    def __init__(self, prod_dir: Path | None = None):
        prod_dir = prod_dir or PROD_DIR
        self.cold_model = joblib.load(prod_dir / "track3_cold_lad.joblib")
        self.warm_model = lgb.Booster(model_file=str(prod_dir / "track3_warm_lgb.txt"))
        self.artist_counts: dict = json.loads(
            (prod_dir / "track3_artist_counts.json").read_text()
        )
        self.metadata: dict = json.loads(
            (prod_dir / "track3_metadata.json").read_text()
        )
        logger.info(f"Loaded production models (v{self.metadata['version']})")
        logger.info(f"  Artists in training: {len(self.artist_counts):,}")

    def _enrich_features(self, row: dict) -> dict:
        """Raw input → feature engineered."""
        out = dict(row)
        out["log_area"] = float(np.log(max(row["width_cm"] * row["height_cm"], 1)))
        ho = float(row.get("estimated_ho", 0))
        bins = [-0.1, 5, 20, 50, 200]
        labels = ["0-5", "5-20", "20-50", "50+"]
        for i, b in enumerate(bins[1:], 1):
            if ho <= b:
                ho_bucket = labels[i-1]; break
        else:
            ho_bucket = "50+"
        out["medium_ho_bucket"] = f"{row['medium_category']}_{ho_bucket}"
        out["aspect_ratio"] = float(np.log(row["width_cm"] / max(row["height_cm"], 1)))
        artist = row.get("artist_name_ko")
        count = self.artist_counts.get(artist, 0) if artist else 0
        out["artist_works_log"] = float(np.log1p(count))
        out["_train_count"] = count
        out["has_depth"] = int(row.get("depth_cm", 0) > 0)
        return out

    def predict(self, row: dict) -> dict[str, Any]:
        """Single record 예측 → KRW 가격 + 라우팅 정보."""
        # 필수 input 검증
        required = ["medium_category", "support_category", "width_cm",
                    "height_cm", "estimated_ho", "orientation"]
        missing = [k for k in required if k not in row]
        if missing:
            return {"error": f"Missing required fields: {missing}"}

        # Feature engineering
        feat = self._enrich_features(row)
        train_count = feat["_train_count"]

        # 라우팅
        model_used = "warm" if train_count >= 1 else "cold"
        confidence = "high"
        warning = None

        # Build DataFrame
        if model_used == "warm":
            features = WARM_FEATURES
            df = pd.DataFrame([{k: feat.get(k) for k in features}])
            for c in WARM_CAT:
                df[c] = df[c].astype("category")
            pred_ln = float(self.warm_model.predict(df)[0])
            if train_count == 1:
                confidence = "medium"
                warning = "rare artist (1건만 학습)"
            elif train_count == 2:
                confidence = "medium-high"
        else:
            features = COLD_FEATURES
            df = pd.DataFrame([{k: feat.get(k) for k in features}])
            pred_ln = float(self.cold_model.predict(df)[0])
            confidence = "low" if np.exp(pred_ln) > HIGH_PRICE_COLD_THRESHOLD else "medium"
            warning = "unseen artist (cold-start, ±115% range)"

        predicted_price = float(np.exp(pred_ln))

        # 고가 caveat
        if predicted_price > 100_000_000:
            if model_used == "cold":
                warning = "🔴 >100M Cold 예측은 사실상 신뢰 불가 (운영 시 비공개 권장)"
                confidence = "very_low"
            else:
                warning = "⚠️ >100M Warm — Warm 2-stage 모델로 검증 권장"

        return {
            "predicted_price_krw": predicted_price,
            "predicted_ln_price": pred_ln,
            "model_used": model_used,
            "train_count": train_count,
            "confidence": confidence,
            "warning": warning,
        }

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Batch inference."""
        results = [self.predict(row.to_dict()) for _, row in df.iterrows()]
        return pd.DataFrame(results)


if __name__ == "__main__":
    # Demo
    predictor = Predictor()

    # Example 1: Warm (학습된 작가)
    print("\n[Example 1] Warm artist (학습된)")
    result = predictor.predict({
        "artist_name_ko": "황선태",
        "medium_category": "oil",
        "support_category": "canvas",
        "width_cm": 60.6, "height_cm": 50.0, "depth_cm": 0,
        "estimated_ho": 12.0,
        "orientation": "landscape",
        # source_platform 제거됨
    })
    for k, v in result.items():
        if k == "predicted_price_krw":
            print(f"  {k}: {v:,.0f} 원")
        else:
            print(f"  {k}: {v}")

    # Example 2: Cold (unseen 작가)
    print("\n[Example 2] Cold artist (신규)")
    result = predictor.predict({
        "artist_name_ko": "신규작가_홍길동",
        "medium_category": "acrylic",
        "support_category": "paper",
        "width_cm": 50, "height_cm": 70, "depth_cm": 0,
        "estimated_ho": 15.0,
        "orientation": "portrait",
        # source_platform 제거됨
    })
    for k, v in result.items():
        if k == "predicted_price_krw":
            print(f"  {k}: {v:,.0f} 원")
        else:
            print(f"  {k}: {v}")

    # Example 3: Missing source
    print("\n[Example 3] Missing required field")
    result = predictor.predict({
        "artist_name_ko": "테스트",
        "medium_category": "oil",
        "width_cm": 50, "height_cm": 50,
        "estimated_ho": 10, "orientation": "square",
        # 일부 필드 누락
    })
    print(f"  {result}")
