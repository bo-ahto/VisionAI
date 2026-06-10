# PP-CDIAG1 Cold base 잔차 진단 요약

- 실험 ID: `PP-CDIAG1` (Cold 로드맵 Phase 1)
- 실행일: 2026-06-10
- 목적: PP-CBASE1 고정 base(연구/운영)의 남은 오차를 validation 기준으로 구간 분해해, Phase 2~3 타겟 실험이 노릴 Cold 위험 구간을 확정한다 (Warm PP-HCOEF13/23 방법론 모방).
- 스크립트: `scripts/track6/run_pp_cdiag1_cold_residual_diagnosis.py`
- 폴더: `experiments/track6/PP-CDIAG1_cold_residual_diagnosis/`
- 0604 미사용 (Warm 시험 제출 전용). 위험 구간 선정은 validation만 사용, test는 확인 표기.

## 위험 구간 (validation, n≥80 & MAPE ratio≥1.3 또는 p95 ratio≥1.3)

| 구간 | 해당 base | val MAPE ratio | val p95 ratio | 잔차 방향 | 해석 |
| --- | --- | ---: | ---: | --- | --- |
| `gap_extreme` (y18 vs v0.2 의견차 상위 10%) | operational | **2.02** | 2.45 | -0.212 (과대예측) | search-free 운영 base는 두 모델 계열이 갈리는 곳에서 크게 무너짐 |
| `qwidth_extreme` (불확실성 폭 상위 10%) | 둘 다 | 1.77 | 2.29 | +0.284 (과소예측) | Warm의 qwidth_extreme과 동일한 병목. 신뢰도/범위 표시 1순위 구간 |
| `guard_on` (guard 발동 행, val 573행) | 둘 다 | 1.67 | 1.99 | +0.131 | guard가 위험을 정확히 짚고 있으나 발동 후에도 잔여 위험 큼 |
| `artist_rows_3_9` (split 내 저행수 작가) | 둘 다 | 1.37 | 2.08 | +0.166 | 저거래 작가 위험 — PP-PCOLD1의 pseudo-cold 난이도 상승과 일치 |
| `qwidth_high` | 둘 다 | 1.36 | 1.49 | ~0 | |
| `mixed_media` (매체) | 둘 다 | 1.31 | 1.31 | +0.054 | |
| `size_small` / `artist_rows_10_49` | operational | 1.16 | 1.35 | | 운영 base 한정 보조 위험 |

## 잔차 크기 상관 (validation, 연구 base APE)

| 신호 | 상관 | 해석 |
| --- | ---: | --- |
| `quantile_width_log` | **+0.215** | 불확실성 폭이 가장 강한 위험 신호 — Phase 4 신뢰도 tier의 핵심 축 |
| `search_delta_abs` | **-0.159** | 검색 delta가 큰(=검색 신호가 있는) 행일수록 오차 작음 — Phase 2 검색 커버리지 확대의 정합 근거 |
| `artist_rows_in_split` | -0.157 | 작가 행수 적을수록 오차 큼 — 신규/저거래 작가 위험 |
| `log_area` | -0.068 | 약함 |
| `model_gap_abs` | -0.002 | 연구 base에는 중립 (운영 base에서만 위험) |

## 정직한 한계: validation 위험 구간의 test 전이가 약함

- validation에서 선정한 위험 구간의 **test MAPE ratio(연구 base)는 0.60~0.94로 전이가 약하거나 역전**됨.
- 원인: ① 구간 경계를 validation 분위수로 고정했는데 test 분포가 더 넓어 bucket 구성이 달라짐, ② test 전체가 이미 어려워 상대 ratio가 희석, ③ Cold 고유의 작가 구성 의존.
- 결론: **위험 구간은 확정 사실이 아니라 가설로 취급**한다. 이를 입력으로 쓰는 Phase 2~3 후보는 반드시 artist 반복 holdout 게이트(PP-CBASE1)로 재검증하며, 구간 경계는 학습 fold 내부에서만 재산정한다.

## Phase 2~3에 주는 좌표

1. **운영 base의 최대 약점은 model gap 구간** (MAPE 2배) — 다만 y18은 서빙 불가 피처 의존이라 직접 라우팅 불가. 대안: qwidth+저행수 작가 조합으로 근사하는 보수 shrink 검증(PP-CCORR 후보).
2. **qwidth_extreme + artist_rows_3_9**가 공통 병목 — 이미지 임베딩(PP-CIMG)의 선택 적용 대상 구간으로 일치 (IMG-P4 결론과 동일 방향).
3. **검색 신호가 있는 곳이 더 정확** — 커버리지 확대(PP-CSRCH)가 점 예측 개선과 신규 작가 fallback 모두에 유효.
4. qwidth는 점 예측 이동보다 신뢰도/범위 표시(PP-CCONF)로 — Warm 결론과 동일.

## 산출물

- `outputs/segment_breakdown.csv` — 8개 차원 × split × base 전체 분해
- `outputs/risk_segments.csv` — 위험 구간 표 (test 확인 표기 포함)
- `artifacts/run_config.json`, `reports/result_report.md`
