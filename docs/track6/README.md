# Track 6 문서 인덱스

- 목적: 최종 보고용 기준 split을 새로 구성하고, Warm / Cold 가격 예측 모델을 재실험
- 핵심 방향: Track5에서 발견한 평가 리스크를 split 단계에서 먼저 제거
- 작성 방식: 개조식
- 상태: 작가 한글명 보정 입력 생성, split/컬럼 품질/feature-label 검증 완료

## 1. 주요 문서

- 실험 계획서: `docs/track6/planning/experiment_plan_v1.md`
- 상사 보고용 실험 계획서: `docs/track6/planning/experiment_plan_for_report.md`
- 이전 트랙 방법 반영 기준: `docs/track6/planning/prior_track_method_reference.md`
- 클렌징 계획서: `docs/track6/dataset/cleaning_plan_v1.md`
- 작가 한글명 개선 보고서: `docs/track6/dataset/artist_name_ko_improvement_report.md`
- split 정책서: `docs/track6/dataset/split_policy_v1.md`
- split 생성 보고서: `docs/track6/dataset/split_report.md`
- 컬럼 품질 검증 보고서: `docs/track6/dataset/column_quality_report.md`
- feature/label 분리 보고서: `docs/track6/dataset/feature_label_pipeline_report.md`
- 데이터 검증/누수 방지 프로세스: `docs/track6/dataset/leakage_prevention_validation_process.md`
- 학습/평가 라벨 사용 흐름: `docs/track6/dataset/train_eval_label_flow.md`
- 실험 인덱스: `docs/track6/experiments/INDEX.md`
- 가설 상태표: `docs/track6/tables/hypothesis_table.md`
- 실험 결과표: `docs/track6/tables/experiment_results_table.md`
- 대시보드: `docs/track6/dashboard/experiment_dashboard.html`

## 2. 주요 데이터 위치

- 원본 후보 데이터: `data/track4_primary_market_feature_candidates_v1.csv`
- Track6 보정 후보 데이터: `data/track6/track6_feature_candidates_name_corrected.csv`
- Track6 split 출력 위치: `data/track6_split/`
- Track6 결과 위치: `data/track6/results/`
- Track6 예측값 위치: `data/track6/predictions/`
- Track6 모델 위치: `data/track6/models/`
- Track6 manifest 위치: `data/track6/manifests/`
- Track6 품질 검증 결과 위치: `data/track6/quality/`
- Track6 Warm feature 위치: `data/track6_split/features/warm/`
- Track6 Cold feature 위치: `data/track6_split/features/cold/`
- Track6 label 위치: `data/track6_split/labels/`

## 3. 진행 원칙

- Track5 결과는 참고만 함
- Track3의 작가명 Warm/Cold 기준, Track4의 동명이인/클렌징 검증, Track5의 split/감사 방식을 반영함
- 클렌징 기준을 먼저 고정한 뒤 validation/test 우선 split을 생성함
- Track6 split을 새로 고정한 뒤 실험을 다시 실행함
- 데이터 검증은 split 검증 → 컬럼 품질 검증 → feature/label 분리 → feature 누수 검사 순서로 진행함
- 모델 학습/예측은 full split이 아니라 feature 파일만 읽음
- 정답 가격은 평가 단계에서 labels 파일로만 읽음
- 라벨 파일은 학습과 평가 단계에서만 읽고, validation/test 예측 단계에서는 읽지 않음
- Warm / Cold는 합치지 않고 분리 평가함
- validation에서 후보를 고르고 test는 최종 확인에만 사용함
- 운영에서 만들 수 없는 피처는 최종 후보에서 제외함

## 4. 재생성 명령

- 대시보드 재생성:
  - `python3 scripts/track6/generate_experiment_dashboard.py`
