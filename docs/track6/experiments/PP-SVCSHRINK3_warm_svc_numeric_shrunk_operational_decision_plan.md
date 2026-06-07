# PP-SVCSHRINK3 svc_numeric 전체 재현 + shrunk median 운영 교체 결정 (설계서)

- 작성일: 2026-06-07
- 목적: SVCSHRINK1/2가 검증한 shrunk 비교군 median을 **svc1 svc_numeric 전체 피처셋**에 반영해, raw 대비 운영 교체 가치가 있는지 PP-SVC4식 반복 holdout + 고정 test_warm + 0604로 결정한다.
- 성격: 운영 결정(검증). svc1 full 파이프라인 재현.
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 전용 폴더 `experiments/track6/PP-SVCSHRINK3_warm_svc_numeric_shrunk_operational_decision/`.

## 1. 단일 가설

- H: "svc_numeric 전체 피처에서 비교군 median을 raw→EB-shrunk로 교체하면, 고정 test_warm 비악화 + 0604 개선 + validation 반복 holdout에서 raw 대비 개선확률 높음 → 운영 svc_numeric 교체 가치."

## 2. 설계

- 피처: svc1 `candidate_features["svc_numeric"]` = warm base(13) + SVC_NUMERIC(median/q25/q75/iqr/unit_area_median/unit_area_iqr/n_log). 모델: svc1 huber_model(OneHotEncoder min_freq=10, Huber eps=1.35).
- 비교군 stats: svc1 `add_service_features`(train OOF crossfit + val/test train-only), 0604은 `apply_comparable_stats(train, 0604)`.
- raw 후보: svc1 그대로.
- shrunk 후보: `svc_group_log_price_median`만 SVCSHRINK1 EB-shrunk median(계층 artist→artist+size→artist+medium+support+size, k=5)으로 교체. train은 OOF, eval은 full-train. 나머지 svc stats는 raw 유지(median-shrinkage 효과 격리).
- 데이터: warm train 26914 / val 519 / test_warm 607 / 0604 837(warm_features_v0_1 + 라벨 조인, <$50 제외).

## 3. 방법

1. raw/shrunk svc_numeric feature frame 생성, Huber 각각 1회 학습(+baseline 참고).
2. val/test_warm/0604 예측.
3. **PP-SVC4식 반복 holdout**: validation 고정 예측을 row 5fold×8 + artist 5fold×8 subsample → shrunk vs raw 개선확률(refit 없음, fast).
4. test_warm + 0604 점 확인.
5. 지표: MdAPE/MAPE/p95 + residual std.

## 4. 채택/중단 기준

- 교체 권고: validation 반복 holdout에서 shrunk가 raw 대비 MAPE 또는 p95 개선확률 ≥0.6 + test_warm 비악화 + 0604 MAPE/p95 개선.
- 부분: 0604만 개선 → 신규작품 경로 한정 적용.
- 중단: 전체 모델에서 이득 소실 → raw 유지.
- test로 후보 선택 금지(반복 holdout=validation).

## 5. 산출물

- `outputs/region_metrics.csv`, `outputs/repeated_holdout_summary.csv`, `artifacts/run_config.json`
- `reports/...md/.html`, 요약 + INDEX/matrix 갱신

## 6. 한계

- shrunk는 median feature만 교체(다른 svc stats raw 유지) — median-shrinkage 효과 격리가 목적.
- crossfit single-seed(svc1 SEED). 완전한 svc_numeric_seed_mean(다중 seed 평균)은 최종 운영 동결 시 추가.
- 채택 시 운영 반영은 svc1/svc2/svc3 seed_mean 파이프라인에 shrunk median 통합 + artifact 동결(별도).

## 7. 다음 액션

- 채택 → svc_numeric_seed_mean에 shrunk median 통합 → Warm 운영 후보(PP-SVC3 70:30 등) 재계산 + cold_prediction과 동급 artifact 동결.
