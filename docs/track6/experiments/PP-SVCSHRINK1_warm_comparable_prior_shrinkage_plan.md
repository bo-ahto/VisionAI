# PP-SVCSHRINK1 Warm 비교군 prior shrinkage 갱신 (설계서)

- 작성일: 2026-06-07
- 목적: PP-SVC8이 진단한 svc 비교군 prior staleness(거친/작은 그룹에서 분산 폭증)를, 거래 시점 데이터 없이 **Empirical Bayes 계층 shrinkage**로 완화한다. 작은 그룹을 상위 레벨로 수축해 분산을 줄인다.
- 배경: literal "최근 거래 갱신"은 Track6에 거래 시점(date) 컬럼이 전무해 불가능(0604는 eval set→leakage). PP-SVC8은 악화 원인이 편향이 아니라 분산(매칭이동 53%+그룹내 분산 47%)임을 확인 → shrinkage가 실현 가능한 해법.
- 성격: 검증(가설). 자체완결(비교군 median + shrinkage, 외부/모델 의존 없음).
- 상태: 설계 완료 / 실행 대기
- 재현 규칙: 산출물은 전용 폴더 `experiments/track6/PP-SVCSHRINK1_warm_comparable_prior_shrinkage/`.

## 1. 단일 가설

- H: "비교군 prior를 EB 계층 shrinkage로 재구축하면, 거친 매칭이 지배하는 0604(신규)에서 prior residual 분산과 MAPE/p95가 raw prior 대비 줄어든다(MdAPE 비악화)."

## 2. 비교군 계층 (nested)

- L0 global → L1 artist_key → L2 artist_key+size_bin → L3 artist_key+medium_category+support_category+size_bin
- size_bin: train area_cm2 분위수(5분위) 경계로 정의, train/test/0604에 동일 적용.
- source pool = warm train (26914).

## 3. 후보

- `raw_prior`(baseline=stale): 각 행에서 n≥5 인 가장 구체적 그룹의 median, 없으면 상위 fallback. (기존 svc prior의 most-specific 동작 모사)
- `shrunk_prior`: 일반→구체 레벨로 `est = (n/(n+k))*group_median + (k/(n+k))*parent_est` 재귀 blend. k는 validation에서 선택.

## 4. 방법

1. train에서 레벨별 group median/count 산출.
2. raw/shrunk prior를 val_warm/test_warm/0604에 적용.
3. k grid {5,20,50,100}를 **val_warm MdAPE**로 선택(test/0604는 확인 전용).
4. 지표: MdAPE/MAPE/p95 + residual_log std(staleness 분산). 영역별(test vs 0604) raw vs shrunk 비교.

## 5. 채택/중단 기준

- 채택: 0604에서 shrunk가 raw 대비 residual std↓ + MAPE/p95 개선, MdAPE 비악화. test_warm 비악화.
- 부분: 0604만 개선 → 신규 작품용 prior로 shrinkage 권고.
- 중단: 개선 없음/악화 → shrinkage 무효, prior staleness는 분산 외 요인.

## 6. 산출물

- `outputs/region_prior_metrics.csv`(raw vs shrunk × test/0604 + std), `outputs/k_validation_selection.csv`, `outputs/level_coverage.csv`
- `reports/...md/.html`, `artifacts/run_config.json`, 요약 + INDEX/matrix 갱신

## 7. 한계 / 정직성

- 이 실험은 **raw 비교군 prior 컴포넌트**를 다룸(svc_numeric Huber 모델 전체 아님). prior가 staleness 원천이므로 컴포넌트 수준 검증이 타당하나, 운영 svc 후보 교체는 Huber 재학습 + 반복검증 후속 필요.
- 거래 시점 데이터 확보 시 recency-weight 갱신이 본래 해법 — 별도 데이터 과제.

## 8. 다음 액션

- shrinkage 유효 → svc 비교군 feature를 shrunk median으로 교체해 Warm Huber 재학습 + 반복검증(PP-SVC 계열) 후 운영 후보 검토.
