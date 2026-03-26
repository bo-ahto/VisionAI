"""Sprint 0 전처리 파이프라인 실행 스크립트."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# 프로젝트 루트 설정
ROOT = Path(__file__).resolve().parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    """전처리 파이프라인을 실행한다."""
    from visionai.price_engine.features.dataset_builder import build_dataset

    works_path = ROOT / "data" / "k-auction-works-20260325.csv"
    output_path = ROOT / "data" / "preprocessed_features.parquet"

    if not works_path.exists():
        logging.error("CSV not found: %s", works_path)
        sys.exit(1)

    df = build_dataset(works_path=works_path, output_path=output_path)

    # 완료 조건 검증
    total = len(df)
    dim_rate = df["surface_area"].notna().sum() / total * 100

    print(f"\n{'='*60}")
    print("Sprint 0 파이프라인 완료")
    print(f"{'='*60}")
    print(f"총 건수:          {total:,}")
    print(f"크기 파싱률:      {dim_rate:.1f}%")
    print(f"매체 분류:        {df['medium_category'].nunique()}종")
    print(f"지지체 분류:      {df['support_category'].nunique()}종")
    print(f"작가 수:          {df['artist_clean'].nunique()}")
    print(f"신규 작가(초회차): {df['is_new_artist'].sum():,}")
    print(f"split 분포:       {df['split'].value_counts().to_dict()}")
    print(f"출력:             {output_path}")

    # 게이트 체크
    assert total == 43866, f"Expected 43866 rows, got {total}"  # noqa: S101
    assert dim_rate >= 97.0, f"Dim parse rate {dim_rate:.1f}% < 97%"  # noqa: S101
    print("\n✅ Sprint 0 완료 조건 충족")


if __name__ == "__main__":
    main()
