# Track 6 문서 인덱스

- 목적: 최종 보고용 기준 split을 새로 구성하고, Warm / Cold 가격 예측 모델을 재실험
- 핵심 방향: Track5에서 발견한 평가 리스크를 split 단계에서 먼저 제거
- 작성 방식: 개조식
- 상태: 세팅 완료, split 생성 전

## 1. 주요 문서

- 실험 계획서: `docs/track6/planning/experiment_plan_v1.md`
- 이전 트랙 방법 반영 기준: `docs/track6/planning/prior_track_method_reference.md`
- split 정책서: `docs/track6/dataset/split_policy_v1.md`
- split 생성 보고서: `docs/track6/dataset/split_report.md`
- 실험 인덱스: `docs/track6/experiments/INDEX.md`
- 가설 상태표: `docs/track6/tables/hypothesis_table.md`
- 실험 결과표: `docs/track6/tables/experiment_results_table.md`
- 대시보드: `docs/track6/dashboard/experiment_dashboard.html`

## 2. 주요 데이터 위치

- 원본 후보 데이터: `data/track4_primary_market_feature_candidates_v1.csv`
- Track6 split 출력 위치: `data/track6_split/`
- Track6 결과 위치: `data/track6/results/`
- Track6 예측값 위치: `data/track6/predictions/`
- Track6 모델 위치: `data/track6/models/`
- Track6 manifest 위치: `data/track6/manifests/`

## 3. 진행 원칙

- Track5 결과는 참고만 함
- Track3의 작가명 Warm/Cold 기준, Track4의 동명이인/클렌징 검증, Track5의 split/감사 방식을 반영함
- Track6 split을 새로 고정한 뒤 실험을 다시 실행함
- Warm / Cold는 합치지 않고 분리 평가함
- validation에서 후보를 고르고 test는 최종 확인에만 사용함
- 운영에서 만들 수 없는 피처는 최종 후보에서 제외함

## 4. 재생성 명령

- 대시보드 재생성:
  - `python3 scripts/track6/generate_experiment_dashboard.py`
