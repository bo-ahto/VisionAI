# PP-CIMG1 Cold 이미지 임베딩 residual 보정 요약

- 실험 ID: `PP-CIMG1` (Cold 로드맵 Phase 2-2)
- 실행일: 2026-06-10
- 목적: IMG-P4 결론(이미지는 기본 예측 대체가 아니라 고위험 구간 한정 보정 후보)을 Cold 로드맵 게이트 아래에서 검증 — CLIP ViT-B/32 임베딩 PCA(512→32) 저차원 Huber residual 보정을 CDIAG1 위험 구간/CCONF1 low tier 한정으로 적용.
- 스크립트: `scripts/track6/run_pp_cimg1_cold_image_residual_correction.py`
- 폴더: `experiments/track6/PP-CIMG1_cold_image_residual_correction/`
- 입력: PP-CBASE1 고정 base + PP-CCONF1 tier + `data/track6/image_multimodal/track6_clip_cold_full_saatchi_artsy_*` (커버리지 validation 92.1% / test 93.1%). 0604 미사용.

## 설계

- residual target = `actual_log − base_pred_log` (연구/운영 base 각각)
- PCA는 train-scope 임베딩으로 동결(라벨/validation 작가 무관), 보정 모델은 validation **artist-grouped 5-fold OOF** Huber
- 적용 정책 격자: 마스크(all / qwidth_extreme / qwidth_high_plus / low_tier / low_tier_or_qwx) × cap(0.05/0.10/0.20) × strength(0.25/0.5/1.0) = target당 36~45개
- 선택: validation OOF p95 비악화 + MAPE 개선 → 상위 후보만 artist 반복 holdout 게이트(80%/70% × 200회) → fixed test 1회

## 결과: 기각 — 게이트 진입 후보 0개

- 전체 격자에서 **validation OOF MAPE 개선 후보 1/72** (-0.000056, 사실상 0)이며 그 후보도 p95 악화(+0.0056). p95 비악화 후보 6개는 전부 MAPE 악화. 모든 델타가 1e-4 수준 = 노이즈.
- **신호 예측력 감사**: OOF 보정값 vs 실제 잔차 상관 = 연구 base **0.083**, 운영 base **0.060**. 보정값 자체 분산은 잔차 std의 ~0.4배 → **작가 경계를 넘으면 이미지 신호의 예측력이 사실상 0이고, 보정은 노이즈 증폭**.
- fixed test는 base 외 보고 대상 없음 (게이트 진입 후보 없음).

## 해석 — IMG-P4 관찰과의 차이

- IMG-P4의 "test MAPE/p95 개선 반복 관찰"은 이미지 피처를 base 모델(LightGBM)에 직접 투입하고 test 관찰로 본 결과였다. 이번에 artist-grouped OOF + 반복 holdout 게이트라는 Cold 표준 검증을 적용하자 신호가 사라졌다.
- 일관된 설명: CLIP 임베딩의 가격 신호는 주로 **같은 작가 내 시각 유사성**(작가 스타일 ↔ 가격대)을 타고 들어오며, unseen 작가에 대한 일반화 신호는 미미하다. Cold의 본질(작가 일반화)과 정확히 충돌하는 지점.
- Warm 35연속 기각과 같은 종류의 결론: 검증 체계가 강화되면 약한 신호는 살아남지 못한다. 이 기각은 로드맵 게이트가 의도대로 작동한다는 증거이기도 하다.

## 남는 선택지 (후속 후보로만 기록)

1. 비선형 모델(LightGBM residual)로 재시도 — 단 저차원 Huber에서 상관 0.06~0.08이면 기대값 낮음.
2. 이미지의 용도 전환: 점 예측 보정이 아니라 **신뢰도 tier 보조 신호**(예: 같은 매체/크기 비교군과의 시각 거리 → low tier 정밀화). CCONF1 정책 축과 결합.
3. 작가 단위 이미지 prior(작가 대표 이미지와의 거리)는 Warm 전용 후보로 이관.

## 산출물

- `outputs/oof_candidate_metrics.csv` (격자 전체), `outputs/gate_results.csv`(빈 결과), `outputs/fixed_test_metrics.csv`
- `artifacts/run_config.json` (동결 경계값 + 신호 감사 수치), `reports/result_report.md`

## 다음 실험

- **PP-CSRCH1 (Phase 2-3)**: 검색 delta 커버리지 확대. 수집 확대는 비용이 들어 cold 운영 트래픽 전망 확인 후 착수 결정(로드맵 §3). 선행 가능: 수집 없이 작가 메타/매체/가격대 그룹 단위로 검색 delta를 일반화해 미커버 작가에 전이하는 후보 검증.
