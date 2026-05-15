# 2026-05-12 PR2 ~ PR5 기초 검증 기록

- 실험 ID: `PR2_PR5_foundation_checks`
- 날짜: 2026-05-12
- 단계: 기초 검증 / 탐색
- 상태: 종결
- 기록 유형:
- 묶음 실험
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 결과 파일:
- [`data/track3_pr2_blend_results.json`](/Users/bo/VisionAI/data/track3_pr2_blend_results.json)
- [`data/track3_pr3_conformal_results.json`](/Users/bo/VisionAI/data/track3_pr3_conformal_results.json)
- [`data/track3_pr4_multiseed_results.json`](/Users/bo/VisionAI/data/track3_pr4_multiseed_results.json)
- [`data/track3_pr5_source_bias_results.json`](/Users/bo/VisionAI/data/track3_pr5_source_bias_results.json)

## 1. 목적

- Cold / Warm 혼합 전략, 불확실성 구간, 재현성, source 편향을 초기 탐색

## 2. 연결 가설

- H2
- H4
- H6

## 3. 사용 데이터

- 데이터 버전:
- `track3_unified / pre-release exploratory set`
- 학습 데이터:
- Track 3 학습용 내부 데이터
- 검증 데이터:
- 각 실험 스크립트의 내부 hold-out / multi-seed split
- 최종 확인 데이터:
- 없음
- 데이터 나누기 기준:
- release split 고정 전 탐색용 내부 분할

## 4. 사용 변수

- 핵심 변수:
- `medium_category`
- `support_category`
- `width_cm`
- `height_cm`
- `log_area`
- `estimated_ho`
- `depth_cm`
- 추가 변수:
- `artist_count` 계열
- `source_platform`
- conformal용 예측 잔차
- 제외 변수:
- 최종 운영 입력으로 불가능한 source 직접 활용은 운영 채택 제외

## 5. 사용 모델

- baseline:
- Cold LAD baseline
- Warm LightGBM baseline
- variant:
- rare/unseen blend
- conformal prediction
- multi-seed Cold LAD
- source bias audit
- 주요 설정값:
- PR2는 `best_w_cold` 탐색
- PR3은 `80% / 90% coverage`
- PR4는 multi-seed 반복

## 6. 변경된 요소

- rare/unseen 구간에서 Warm/Cold 혼합 비율 탐색
- conformal interval 폭과 coverage 확인
- Cold LAD 재현성 확인
- source 편향 정량화

## 7. 성공 기준

- Warm:
- uncertainty 분석이 과도한 폭 증가 없이 coverage 확보
- Cold:
- LAD baseline 재현성 확인
- 보조 기준:
- source 편향 존재 여부를 정량적으로 확인

## 8. 실행 내용

- `pr2_rare_artist_blend.py`
- `pr3_conformal_prediction.py`
- `pr4_multiseed_cold_lad.py`
- `pr5_source_bias_audit.py`
- 산출물:
- `data/track3_pr2_blend_results.json`
- `data/track3_pr3_conformal_results.json`
- `data/track3_pr4_multiseed_results.json`
- `data/track3_pr5_source_bias_results.json`

## 9. 결과

### PR2 rare / unseen blend

- 전체와 Warm 구간에서는 `best_w_cold = 0.0`
- `rare 1건`, `rare 1-2건`에서는 `0.2`
- `unseen (0건)`에서는 `0.5`
- 해석
- Cold blend는 일부 희소 작가 / unseen 구간에서만 신호가 있었고
- 전체 구조로는 채택 근거가 약했음

### PR3 conformal prediction

- Warm LGB 80%
- coverage `0.8158`
- median width `88.49%`
- Warm LGB 90%
- coverage `0.9143`
- median width `156.41%`
- Cold LAD 80%
- coverage `0.8064`
- median width `231.36%`
- Cold LAD 90%
- coverage `0.9033`
- median width `385.13%`
- 해석
- 전체 coverage는 목표에 근접했지만
- Cold 고가 구간에서는 coverage 저하와 구간 폭 확대가 큼
- point prediction 주력 구조를 바꿀 근거보다는 보조 uncertainty 분석에 가까움

### PR4 multiseed cold LAD

- `median_ape_mean 0.4309`
- `median_ape_std 0.0281`
- `w30_mean 0.3646`
- 해석
- Cold LAD baseline이 seed 변화에도 일정 수준 재현된다는 근거를 제공

### PR5 source bias audit

- source median price
- `artsy 4.14M`
- `artue 2.62M`
- `saatchi 2.34M`
- 같은 작가 cross-source pair
- `artsy vs saatchi median_ratio 1.39`
- 회귀 기준
- `artsy_pct_vs_saatchi +45.5%`
- 해석
- source 편향은 실제로 강하게 존재
- 다만 운영 입력에서는 `source_platform`을 안정적으로 알기 어렵기 때문에
- 최종 운영 피처에서 제외하는 판단 근거로 사용

### Warm 요약

- 사용 변수 요약:
- Warm baseline + conformal residual 분석
- 핵심 결과:
- conformal coverage는 목표에 근접했지만 구간 폭이 큼
- 해석:
- Warm 구조를 바꾸기보다 uncertainty 보조 활용에 가까움

### Cold 요약

- 사용 변수 요약:
- 구조 변수 + rare/unseen blend 후보 + LAD baseline 재현성
- 핵심 결과:
- Cold LAD 재현성 확보
- rare/unseen blend는 전체 채택 근거 약함
- 해석:
- Cold baseline은 유지 가치가 있고, blend는 제한 구간 신호만 있음

## 10. 해석

- source 편향과 Cold baseline 재현성은 분명히 확인됨
- 다만 source를 최종 운영 입력으로 쓰기 어려워 direct 활용은 보류
- rare/unseen blend는 일부 slice 신호만 있고 전체 운영 개선 근거는 부족
- conformal은 point prediction 교체안이 아니라 불확실성 보조 수단으로 해석하는 것이 적절

## 11. 결론

- 상태:
- 종결
- 핵심 결론:
- source 편향은 분명하지만 운영 입력 변수로 채택하기는 어려움
- Cold baseline은 multi-seed에서 재현성 신호가 있음
- rare / unseen blend는 일부 신호만 있었고 전체 채택 근거는 약함
- 채택 / 보류 / 중단:
- 중단
- 이유:
- 기초 탐색 목적은 달성했고, 후속 confirm 실험으로 연결할 항목만 남김
- 참고 상태:
- 종결

## 12. 다음 액션

- source 의존 개선안은 운영 입력 제약 때문에 confirm 단계에서 엄격히 필터링
- rare/unseen blend 가설은 이후 `PR25`, `PR29` confirm 결과와 함께 종결 판단
