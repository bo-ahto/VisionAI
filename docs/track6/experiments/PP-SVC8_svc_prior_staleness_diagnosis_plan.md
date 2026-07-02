# PP-SVC8 svc 비교가격 prior의 0604 악화 원인 분해 (설계서)

- 작성일: 2026-06-07
- 작성 목적: PP-SVC7이 보인 "svc 비중↑일수록 0604 단조 악화"의 원인을 (A) 시간적 편향, (B) 그룹내 분산 증가, (C) 비교군 매칭 레벨 이동(coverage mix shift)으로 분해한다.
- 성격: 진단(분석) 실험. 새 운영 후보를 만들지 않는다. oracle 보정은 상한 진단용이며 배포 후보가 아니다.
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 모든 산출물은 전용 폴더 `experiments/track6/PP-SVC8_svc_prior_staleness_diagnosis/` 아래에만 저장.

## 1. 배경 (PP-SVC7 + 예비 분석)

- PP-SVC7 결론: 70:30 vs pp_v8 차이는 라우팅 불가한 distribution shift. svc weight↑일수록 0604 MdAPE 단조 악화.
- 예비 residual_log 분석:

| 지표 | 고정 test | 0604 |
|---|---:|---:|
| svc bias(median) | -0.003 | +0.083 |
| svc 분산(std) | 0.418 | 1.641 |
| pp_v8 분산(std) | 0.403 | 0.692 |
| svc+전역bias MdAPE | 0.1524 | 0.3399(악화) |
| svc MdAPE | 0.1520 | 0.3072 |

- 1차 시사점: 편향(B 가설) 아님 — bias 작고 전역 보정은 오히려 악화. 분산 폭증(B') + 매칭 레벨 이동(C)이 유력.

## 2. 분석 질문 (가설)

- Q1(편향): svc 0604 악화가 전역/레벨별 systematic bias로 설명되는가? → oracle bias 제거 후 잔여로 검증.
- Q2(분산): 같은 매칭 레벨 안에서도 0604 svc residual 분산이 고정 대비 커지는가? (intrinsic staleness)
- Q3(매칭 이동): 0604가 더 거친 svc_group_level/coverage_tier로 매칭되어 악화되는가? (coverage mix shift)
- Q4(분해): 0604 svc MdAPE 악화 중 매칭 이동(C) 몫 vs 그룹내 분산(B') 몫은 각각 얼마인가?

## 3. 분석 방법 (모두 재현 가능)

1. **영역 residual 요약**: svc, pp_v8의 residual_log median(bias)/IQR/std + MdAPE/MAPE/p95를 고정 test vs 0604로 비교.
2. **편향 제거 oracle(상한 진단, 비배포)**: `svc + region_median_bias`, `svc + per(group_level)_median_bias`의 MdAPE/MAPE. 0604에서 개선이 작거나 악화면 편향 가설 기각.
3. **매칭 이동 표**: svc_group_level, svc_coverage_tier 분포를 고정 test vs 0604로 비교(신규 등장 레벨 표시).
4. **레벨 통제 분산**: 두 영역에 모두 존재하는 group_level별 svc residual IQR/std + MdAPE를 영역별로 비교(매칭 이동 통제 후 intrinsic staleness 측정).
5. **mix vs within 분해**: 0604 행을 고정 test의 group_level 비율로 재표본(고정 seed)해 "0604 within-error @ 고정 mix" MdAPE/MAPE 산출. 실제 0604와의 차이 = 매칭 이동(C) 몫, 재표본 후 잔여 악화 = 그룹내 분산(B') 몫.
6. **svc vs pp_v8 강건성**: group_level별 svc/pp_v8 residual std 비율로 pp_v8이 어디서 더 강건한지 표시.

## 4. 산출물 (전용 폴더)

- `experiments/track6/PP-SVC8_svc_prior_staleness_diagnosis/`
  - `outputs/region_residual_summary.csv`
  - `outputs/bias_removal_oracle.csv`
  - `outputs/coverage_mix_shift.csv`
  - `outputs/level_controlled_dispersion.csv`
  - `outputs/mix_within_decomposition.csv`
  - `outputs/svc_vs_ppv8_robustness_by_level.csv`
  - `reports/PP-SVC8_svc_prior_staleness_diagnosis.md` / `.html`
  - `artifacts/run_config.json`
- 요약 문서: `docs/track6/experiments/pp_svc8_svc_prior_staleness_diagnosis_summary.md`
- INDEX/매트릭스 갱신.

## 5. 데이터 소스 (PP-SVC7과 동일)

- 고정 split: `experiments/track6/PP-SVC2_warm_comparable_stats_stability/outputs/predictions.csv`
- 0604: `models/track6/price_prediction_v0.1/operational/outputs/0604_evaluation/operational_predictions_with_actual.csv` (`actual_price_usd_equiv >= 50` 필터)

## 6. 누수/해석 주의

- [ ] oracle bias 보정은 해당 영역 라벨을 사용하므로 **상한 진단 전용**이며 운영 후보가 아님을 명시.
- [ ] 재표본 seed는 코드에 고정.
- [ ] 결론은 원인 귀속까지만. 배포 가능한 보정 제안은 별도 후속 실험으로 분리(검증용 최근-라벨 holdout 필요).

## 7. 예상 결론 분기 / 다음 액션

- 분산·매칭 이동 주도(예상): svc prior는 신규 작품에서 거친 매칭+고분산 → 점예측 직접 반영 위험. 다음 액션 = svc를 신뢰도 기반으로 약화하거나 비교군 prior 갱신(최근 거래 반영) 후속 실험. 운영 기본값 pp_v8 유지.
- 편향 주도(기각 예상): 전역/레벨 보정으로 fixable → 최근-라벨 holdout 검증 가능한 보정 실험 설계.
