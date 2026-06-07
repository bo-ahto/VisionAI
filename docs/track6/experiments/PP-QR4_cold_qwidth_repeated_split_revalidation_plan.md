# PP-QR4 Cold qwidth/guard 생존 후보 반복 split·artist holdout 재검증 (설계서)

- 작성일: 2026-06-07
- 작성 목적: PP-QR3에서 test까지 생존한 Cold 후보 2개가 **반복 split / artist holdout / bootstrap** 에서도 PP-Y18 기준선을 안정적으로 이기는지 확정한다. 이 결과가 Cold artifact 고정(PP-COLD-ARTIFACT1)의 전제 조건이다.
- 성격: 신규 모델 학습 실험이 아니라, 기존 후보의 **안정성 재검증** 실험이다.
- 상태: 설계 완료 / 실행 대기

## 1. 배경

- PP-QR3 결론(요약: `pp_qr3_cold_quantile_oof_holdout_revalidation_summary.md`):
  - 복잡한 prediction-level meta 보정(Ridge/QR/HGB residual)은 holdout에서 좋았으나 **test에서 PP-Y18보다 악화** → 후보에서 제외.
  - test까지 생존한 후보는 단순한 qwidth·q40/q50 gap 기반 guard/segment 보정 2개.
  - 명시적 잔여 과제: "이 후보들도 최종 교체 전에는 split 재학습 또는 별도 holdout에서 한 번 더 확인한다."
- 즉 PP-QR4는 PP-QR3가 남긴 잔여 과제를 닫는 실험이다.
- 방법론 기준점: Warm 쪽 PP-AMW6가 사용한 반복검증 프로토콜(validation 작가 단위 12회 × 5fold + test bootstrap 400회)을 Cold에 동일하게 적용해 트랙 내 일관성을 유지한다.

## 2. 단일 가설

- H(PP-QR4): "PP-QR3 생존 후보(segment / guard)는 반복 split·artist holdout·bootstrap에서 PP-Y18 qwidth_bin 기준선 대비 **MdAPE 개선확률 ≥ 0.7** 을 유지하며, p95_APE를 악화시키지 않는다."
- 변수는 **보정 후보 1개 축**만 비교한다(검증 프로토콜은 고정). 새 보정식·새 피처·새 모델군은 이 실험에서 추가하지 않는다.

## 3. 검증 대상 후보

| 역할 | 후보 | 정책 | PP-QR3 test (MdAPE/MAPE/p95) |
|---|---|---|---|
| 기준선(control) | `component_pp_y18_qwidth_bin` | control | 0.4247 / 0.9910 / 3.3053 |
| 보조 기준선 | `component_pp_y2_baseline` | control | 0.4421 / 1.0484 / 3.3537 |
| 대표 개선 후보 | `segment_y18_qwidth_pred_gap_min30_cap0p15_s0p50` | quantile_gap_segment_residual_correction | 0.4175 / 1.0029 / 3.0018 |
| 균형(MAPE/p95 방어) 후보 | `guard_y18_lgb_q40_qwidth67_gap50_down_w0p50` | validation_threshold_guarded_blend | 0.4178 / 0.9640 / 2.5377 |

- 후보 정의·예측 생성 함수는 PP-QR2/QR3 모듈(`run_pp_qr2_cold_quantile_final_candidate_blend.py`)을 재사용한다. **후보를 새로 정의하지 않는다.**

## 4. 데이터 / split

- Cold 전용 split만 사용한다([[track6_price_prediction_state]]).
  - 학습 feature: `data/track6_split/features/cold/track6_train_cold_features.csv`
  - validation feature: `data/track6_split/features/cold/track6_val_cold_cold_features.csv`
  - test feature: `data/track6_split/features/cold/track6_test_cold_cold_features.csv`
  - 정답 라벨: `data/track6_split/labels/track6_*_cold_labels.csv` (학습·평가 단계에서만 read)
- 작가 단위 holdout 그룹 컬럼: `artist_key` (Cold는 train ∩ test 작가 = 0 보장).

## 5. 방법 (검증 프로토콜, 고정)

1. **OOF 보정값 생성**: 보정 segment·threshold·가중치는 train+validation 내부 fold(OOF)에서만 산출한다. test는 보지 않는다.
2. **반복 row k-fold**: validation을 KFold 5분할 × seed 12회 반복 → 후보별 fold 성능 분포(평균·표준편차) 산출.
3. **반복 artist GroupKFold**: validation을 `artist_key` GroupKFold 5분할 × seed 12회 반복 → 작가 구성 변동에 대한 안정성 산출.
4. **개선확률 계산**: 각 반복에서 후보 MdAPE/MAPE/p95가 `component_pp_y18_qwidth_bin` 대비 개선된 비율.
5. **test bootstrap 400회**: 선택된 후보에 대해서만, test에서 row bootstrap 400회로 MdAPE/MAPE/p95 95% CI 산출 (test는 최종 확인 1회 용도 — 후보 재선택 금지).
6. seed 목록은 고정값으로 코드에 명시(재현성). `SEED`는 `run_pre_pp_experiments` 공유값을 기준으로 파생.

## 6. 채택 / 중단 기준

- 채택(artifact 고정 후보로 승급): 아래 **모두** 만족.
  - row-fold + artist-fold 양쪽에서 MdAPE 개선확률 ≥ 0.7.
  - p95_APE 개선확률 ≥ 0.5 (최소한 악화시키지 않음).
  - test bootstrap에서 MdAPE 95% CI 상한이 PP-Y18 점추정(0.4247) 이하.
- 보류: 개선확률이 row-fold에선 높으나 artist-fold에서 무너지는 경우 → 작가 구성 의존 후보로 분류, 운영 후보 제외.
- 중단: 두 후보 모두 기준 미달 → Cold 대표는 PP-Y18 유지, PP-COLD-ARTIFACT1은 PP-Y18 단독 고정으로 진행.

## 7. 산출물

- 실험 폴더: `experiments/track6/PP-QR4_cold_qwidth_repeated_split_revalidation/`
  - `outputs/repeated_row_fold_metrics.csv` — row k-fold 반복 성능 분포
  - `outputs/repeated_artist_fold_metrics.csv` — artist GroupKFold 반복 성능 분포
  - `outputs/improvement_probability_summary.csv` — 후보별 개선확률 종합
  - `outputs/test_bootstrap_ci.csv` — 선택 후보 test bootstrap 95% CI
  - `reports/result_report.md` — 9항목 결과(목적/데이터/변수/모델/변경요소/Warm=N/A/Cold결과/해석/다음액션)
- 요약 문서: `docs/track6/experiments/pp_qr4_cold_qwidth_repeated_split_revalidation_summary.md`
- 인덱스/매트릭스 갱신: `docs/track6/experiments/INDEX.md`, `postprocessing_experiment_matrix.md`

## 8. 실행 명령 (예정)

```bash
python3 scripts/track6/run_pp_qr4_cold_qwidth_repeated_split_revalidation.py
```

- 스크립트는 `run_pp_qr3_*`를 템플릿으로 하되, meta-모델 탐색부를 제거하고 §5 반복검증 루프로 대체한다.

## 9. 누수 방지 체크리스트

- [ ] 보정 segment/threshold/가중치는 OOF·validation fold에서만 산출했는가.
- [ ] test는 §5-5 최종 확인에서만 1회 사용했는가(후보 재선택에 사용 금지).
- [ ] 라벨 파일은 학습·평가에서만 read하고 예측 단계에서 read하지 않았는가.
- [ ] 운영 입력에서 알 수 없는 값(실제 가격 구간 등)을 보정 기준으로 쓰지 않았는가.
- [ ] artist holdout에서 train ∩ holdout 작가 = 0 을 확인했는가.

## 10. 다음 액션 연결

- 채택 시 → **PP-COLD-ARTIFACT1**: 승급 후보의 qwidth correction map + LightGBM Quantile 모델 + fallback 정책을 한 번에 artifact로 고정.
- 보류/중단 시 → Cold 대표 PP-Y18 유지 + 검색 보정(PP-H28)은 신뢰도 하향/검수 플래그로만 제한 적용.
