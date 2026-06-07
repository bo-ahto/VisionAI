# 가격 예측 모델 v0.1

- 목적: 중간 리포트 기준 후보를 신규 테스트와 서비스 API 검증의 기준 버전으로 고정
- 상태: 중간 확정 테스트 기준
- 최종 배포 여부: 아님
- 생성일: 2026-06-04 16:27

## 1. 버전 정의

- `price_prediction_v0.1`은 모델 정책, 학습 데이터, 실험 근거, 재현 스크립트를 한 폴더에 묶은 재현용 번들
- Warm 기준 후보: `PP-SVC3 blend_svcnum_ppv8_wsvc_0.70`
- Cold 기준 후보: `PP-Y18 qwidth_bin_oof_min30_cap0.25`
- 기존 `data/track6/artifacts` 모델은 baseline smoke test 용도이며 v0.1 현재 후보가 아님

## 2. 폴더 구조

| 경로 | 내용 |
|---|---|
| `config/model_policy_v0.1.json` | v0.1 모델 정책 |
| `data/training/track6_split/` | 학습/검증/테스트 split 스냅샷 |
| `data/evaluation/` | 2026-06-04 신규 테스트 데이터와 Warm/Cold 라우팅 결과 |
| `evidence/experiments/` | v0.1 선정 근거 실험 산출물 |
| `evidence/reports/` | 중간 리포트와 서비스 적용 문서 |
| `legacy_artifacts/` | 이전 baseline artifact |
| `reproduction/scripts/` | 근거 실험 재현에 필요한 스크립트 |
| `manifest/files_manifest.csv` | 파일별 크기/checksum |
| `manifest/MANIFEST.sha256` | 재현성 확인용 checksum |

## 3. Warm v0.1

- 예측식: `pred_log = 0.70 * svc_numeric_seed_mean + 0.30 * pp_v8_compact_blend_mape_guarded`
- test MdAPE: `0.1405`
- test MAPE: `0.2748`
- test p95_APE: `0.8331`
- 해석: 같은 작가의 과거 가격 기준과 오차 안정화 후보를 함께 사용

## 4. Cold reference v0.1

- 기준 후보: `LightGBM Quantile + qwidth 구간 보정`
- test MdAPE: `0.4247`
- test MAPE: `0.9910`
- test p95_APE: `3.3053`
- 해석: Cold는 확정 가격보다 참고 예측가와 넓은 범위 표시 중심

## 5. 재현 기준

- 학습 데이터는 이 폴더의 `data/training/track6_split/` 스냅샷 사용
- 실험 근거는 `evidence/experiments/`의 metrics/predictions/config 사용
- 파일 무결성은 `manifest/MANIFEST.sha256`로 확인

## 6. 신규 무가격 CSV 피처 추출

- 기본 입력: `data/test_new_artworks_test_noprice_0604.csv`
- v0.1 폴더 내 입력 사본: `data/evaluation/test_new_artworks_test_noprice_0604.csv`
- 실행 스크립트: `reproduction/scripts/extract_price_prediction_v0_1_features.py`
- 기본 실행:

```bash
python3 models/track6/price_prediction_v0.1/reproduction/scripts/extract_price_prediction_v0_1_features.py
```

- 다른 입력 파일 실행:

```bash
python3 scripts/track6/extract_price_prediction_v0_1_features.py \
  --input data/new_artworks.csv \
  --output-dir models/track6/price_prediction_v0.1/data/evaluation/new_artworks_features
```

- 주요 출력: `features_all_v0_1.csv`, `warm_features_v0_1.csv`, `cold_features_v0_1.csv`, `routing_v0_1.csv`, `feature_quality_report.csv`
- 주의: 이 단계는 가격 예측 전 입력 변환 단계이며, 가격 예측값 생성은 별도 추론 스크립트에서 수행

## 7. 주의

- 이 버전은 중간 리포트 기준을 고정한 테스트용 버전
- PP-SVC3는 현재 단일 inference artifact가 아니라 실험 예측값 결합 정책
- 신규 데이터 직접 추론을 위해서는 다음 단계에서 PP-SVC3 component chain을 artifact화해야 함
