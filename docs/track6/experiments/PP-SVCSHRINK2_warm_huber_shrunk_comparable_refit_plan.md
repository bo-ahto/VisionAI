# PP-SVCSHRINK2 Warm Huber + shrunk 비교군 median 재학습 (설계서)

- 작성일: 2026-06-07
- 목적: PP-SVCSHRINK1이 raw prior 컴포넌트에서 검증한 shrinkage 효과가 Warm Huber **모델에 투입**됐을 때도 raw 비교군 median 대비 개선되는지 확인. svc_numeric 운영 후보 교체 가능성 검토.
- 성격: 검증(가설). svc1 Huber 파이프라인 재현 + 비교군 median을 raw↔shrunk로 교체.
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 산출물은 전용 폴더 `experiments/track6/PP-SVCSHRINK2_warm_huber_shrunk_comparable_refit/`.

## 1. 단일 가설

- H: "Warm Huber 입력의 비교군 median을 raw→shrunk로 바꾸면 고정 test_warm 비악화 + 0604(stale)에서 MAPE/p95 개선된다."

## 2. 설계

- base 피처(공통 9, 0604 호환): width/height/depth/area/log_area + medium_category/support_category/medium_support_bucket/artist_key. (0604에 없는 aspect_ratio/has_depth/is_3d/is_extreme 제외 — 두 변형 동일 base라 비교 유효)
- 비교군 median: PP-SVCSHRINK1 계층(artist→artist+size→artist+medium+support+size)에서 raw(most-specific n≥5) vs shrunk(EB k). train은 OOF(KFold5)로 누수 방지, val/test/0604는 full-train 그룹.
- 모델: svc1 huber_model 재현 — OneHotEncoder(min_frequency=10) + StandardScaler + HuberRegressor(epsilon=1.35, alpha=1e-4, max_iter=4000).
- 후보: `base`(비교군 없음) / `base+raw_median` / `base+shrunk_median`.
- k: PP-SVCSHRINK1 선택값(k=5) 사용(필요 시 validation 재선택).

## 3. 방법

1. OOF train median(raw/shrunk) + val/test/0604 median.
2. 후보별 Huber 학습(warm train) → val_warm/test_warm/0604 예측.
3. **반복 artist GroupKFold(train, 5fold×N seeds)**: fold마다 비교군 그룹+Huber 재학습, raw vs shrunk 개선확률.
4. 지표: MdAPE/MAPE/p95 + residual std.

## 4. 채택/중단 기준

- 채택: shrunk가 test_warm 비악화 + 0604 MAPE/p95 개선 + artist holdout에서 raw 대비 개선확률 ≥0.6.
- 부분: 0604만 개선 → 신규 작품용 권고.
- 중단: 모델 투입 시 shrinkage 이득 소실 → raw 유지.

## 5. 산출물

- `outputs/region_model_metrics.csv`, `outputs/artist_holdout_summary.csv`, `outputs/k_note.json`
- `reports/...md/.html`, `artifacts/run_config.json`, 요약 + INDEX/matrix 갱신

## 6. 한계

- base 피처가 svc1 svc_numeric의 전체 피처셋과 동일하지 않음(0604 호환 위해 4개 제외, 비교군 보조통계 일부 생략) → 절대 지표는 운영 svc_numeric과 다름. 본 실험은 **raw↔shrunk median 효과 격리**가 목적.
- 운영 교체는 svc1 전체 피처 + seed 평균으로 재현 후 PP-SVC4식 반복 holdout 추가 필요.

## 7. 다음 액션

- 채택 시 → svc1 svc_numeric 피처셋에 shrunk median 반영해 전체 재현 + 반복검증 → 운영 후보 교체.
