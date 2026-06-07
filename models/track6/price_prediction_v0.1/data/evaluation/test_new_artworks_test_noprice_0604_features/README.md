# v0.1 가격 예측 피처 추출 결과

- 생성일: 2026-06-04T16:46:14
- 입력 파일: `/Users/bo/VisionAI/data/test_new_artworks_test_noprice_0604.csv`
- 모델 기준 폴더: `/Users/bo/VisionAI/models/track6/price_prediction_v0.1`
- 출력 폴더: `/Users/bo/VisionAI/models/track6/price_prediction_v0.1/data/evaluation/test_new_artworks_test_noprice_0604_features`
- 전체 행: 6,873
- Warm 행: 6,873
- Cold 행: 0

## 기본 실행 명령

```bash
python3 scripts/track6/extract_price_prediction_v0_1_features.py
```

## 다른 입력 파일 실행 예시

```bash
python3 scripts/track6/extract_price_prediction_v0_1_features.py \
  --input data/new_artworks.csv \
  --output-dir models/track6/price_prediction_v0.1/data/evaluation/new_artworks_features
```

## 생성 파일

| 파일 | 설명 |
|---|---|
| `features_all_v0_1.csv` | 전체 입력 행 + v0.1 기본 피처 + Warm 비교군 피처 |
| `warm_features_v0_1.csv` | Warm route 행만 따로 저장한 파일 |
| `cold_features_v0_1.csv` | Cold route 행만 따로 저장한 파일 |
| `routing_v0_1.csv` | Warm/Cold 구분과 artist_key 매칭 상태 |
| `feature_quality_report.csv` | 변환 품질 요약 |
| `feature_issue_sample.csv` | 확인이 필요한 행 샘플 |
| `feature_schema_v0_1.json` | 컬럼 구성과 v0.1 정책 설명 |

## 품질 요약

| metric | value |
| --- | --- |
| total_rows | 6873.0 |
| warm_rows | 6873.0 |
| cold_rows | 0.0 |
| artist_matched_rows | 6873.0 |
| dimension_parsed_rows | 6800.0 |
| dimension_problem_rows | 73.0 |
| medium_other_rows | 921.0 |
| support_other_rows | 906.0 |
| svc_artist_level_rows | 4719.0 |
| svc_global_fallback_rows | 252.0 |
| median_svc_group_n | 15.0 |

## 사용 순서

1. `feature_quality_report.csv`에서 `dimension_problem_rows`, `medium_other_rows`, `svc_global_fallback_rows` 확인
2. 문제가 있는 경우 `feature_issue_sample.csv`에서 원본 row 확인
3. Warm 예측 테스트에는 `warm_features_v0_1.csv` 사용
4. Cold 예측 테스트에는 `cold_features_v0_1.csv` 사용

## 주의

- 이 스크립트는 피처 추출만 수행하고 가격 예측값은 만들지 않음
- Warm v0.1의 정확한 가격 예측은 `PP-SVC3` component chain artifact가 준비된 뒤 수행
- Cold v0.1 reference는 외부/검색 피처와 qwidth 보정 artifact가 필요하므로, 이 출력은 Cold 기본 작품 피처 추출 결과로 해석
