# Track 4 문서 체계

- 목적: Track 4 모델 실험을 대시보드와 문서만 보고 추적할 수 있게 관리 기준을 고정
- 기준일: 2026-05-17
- 작성 방식: 개조식

## 1. 기본 방향

- Track 4는 데이터셋 검증과 모델 실험을 분리해서 관리함
- 데이터셋 검증은 `T4-D` 체크포인트로 관리함
- 모델 실험은 `T4-H` 가설과 `T4-E` 실험 기록으로 관리함
- 대시보드는 Markdown 기준 문서를 읽어 자동 생성함
- 수동으로 HTML을 직접 수정하지 않음

## 2. 문서 역할

| 문서 | 역할 | 수정 주체 |
|---|---|---|
| `docs/track4/planning/overview_guide.md` | Track 4 전체 입구 문서 | 필요 시 |
| `docs/track4/planning/experiment_plan_v1.md` | 실험 원칙, 평가 지표, 진행 순서 | 기준 변경 시 |
| `docs/track4/dataset/cleaning_pipeline.md` | 데이터 추가/클렌징/검증 파이프라인 | 데이터 기준 변경 시 |
| `docs/track4/dataset/final_quality_review_2026-05-17.md` | 현재 데이터셋 최종 품질 검토 | 파이프라인 재실행 시 |
| `docs/track4/planning/warm_cold_process.md` | Warm / Cold 분리 실험 절차 | 라우팅 기준 변경 시 |
| `docs/track4/tables/hypothesis_table.md` | 가설 상태 요약표 | 가설 추가/상태 변경 시 |
| `docs/track4/tables/experiment_results_table.md` | 실험 결과 요약표 | 실험 실행 후 |
| `docs/track4/experiments/` | 개별 실험 상세 기록 | 실험 실행 후 |
| `docs/track4/dashboard/experiment_dashboard.html` | 자동 생성 대시보드 | 스크립트로 생성 |

## 2.1 산출물 폴더 역할

| 폴더 | 역할 |
|---|---|
| `scripts/track4/` | Track 4 전용 실행 스크립트 |
| `docs/track4/` | Track 4 문서, 표, 대시보드 |
| `docs/track4/experiments/` | 개별 실험 문서 기록 |
| `data/track4/results/` | 실험별 성능 결과 JSON/CSV |
| `data/track4/predictions/` | 실험별 예측 결과 CSV |
| `experiments/track4/` | 실행 로그, 임시 분석 산출물, 실험별 작업 폴더 |

## 3. 실험 진행 순서

- 1단계: 가설 등록
- `docs/track4/tables/hypothesis_table.md`에 가설 ID, 목표, 연구 방법, 성공 기준을 먼저 작성함
- 2단계: 실험 방법 확정
- 사용할 데이터, 피처, 모델, 비교군, 평가 지표를 정함
- 3단계: 실험 실행
- 스크립트는 `scripts/track4/`에 둠
- 모델 실험 결과 파일은 `data/track4/results/` 아래에 저장함
- 예측 결과는 `data/track4/predictions/` 아래에 저장함
- 실행 단위 산출물은 `experiments/track4/` 아래에 저장함
- 4단계: 개별 기록 작성
- `docs/track4/experiments/YYYY-MM-DD_T4-E###_name.md` 형식으로 작성함
- 5단계: 결과표 업데이트
- `docs/track4/tables/experiment_results_table.md`에 핵심 성능과 결론을 추가함
- 6단계: 가설 상태 업데이트
- `docs/track4/tables/hypothesis_table.md`의 상태, 현재 판단, 후속 필요를 수정함
- 7단계: 대시보드 재생성
- `python3 scripts/track4/generate_experiment_dashboard.py`

## 4. ID 규칙

- 데이터 준비 체크포인트
- 형식: `T4-D0`, `T4-D1`, `T4-D2`
- 의미: 모델 성능 가설이 아니라 데이터셋 준비 상태 확인

- 모델 실험 가설
- 형식: `T4-H1`, `T4-H2`, `T4-H3`
- 의미: 가격 예측 성능, 운영 가능성, 신뢰도 정책을 검증하는 질문

- 실험 기록
- 형식: `T4-E001`, `T4-E002`, `T4-E003`
- 의미: 실제 실행 단위
- 하나의 실험은 여러 가설과 연결될 수 있음

## 5. 대시보드 운영 방식

- 대시보드는 아래 문서를 읽어 자동 생성함
- `docs/track4/tables/hypothesis_table.md`
- `docs/track4/tables/experiment_results_table.md`
- `docs/track4/dataset/final_quality_review_2026-05-17.md`
- `docs/track4/dataset/split_report.md`
- HTML은 결과물로만 관리함
- 대시보드에서 직접 내용을 고치지 않음
- 가설 상태나 실험 결과를 바꾸려면 Markdown 표를 먼저 수정함

## 6. 대시보드에서 봐야 할 핵심 정보

- 데이터셋 상태
- 학습 후보 수
- Warm / Cold split row 수
- Cold/train 작가 겹침 여부
- `artist_works_log` 누수 여부
- 크기 파싱 보완 상태

- 가설 상태
- 예정
- 진행 중
- 부분 검증
- 검증 완료
- 보류
- 중단

- 모델 결과
- Warm median APE
- Cold median APE
- p95 APE
- Within-30%
- 가격 범위 coverage
- 가격 범위 폭

## 7. 실험 전 체크리스트

- 데이터셋 품질 검토 문서가 최신인지 확인함
- split report에서 Cold/train overlap이 0인지 확인함
- 가설표에 해당 가설이 먼저 등록되어 있는지 확인함
- 실험 결과를 기록할 개별 문서 이름을 미리 정함
- 사용 피처에 `track4_source`, URL, gallery tier가 들어가지 않았는지 확인함
- test set은 최종 확인용으로만 사용하고, 후보 선택에는 validation을 사용함

## 8. Track 3 대비 개선점

- 데이터 준비와 모델 가설을 분리함
- HTML은 자동 생성만 허용함
- 대시보드 상단에 데이터셋 검증 상태를 함께 표시함
- Warm / Cold 결과를 항상 분리해서 보여줌
- test 결과를 후보 선택에 쓰지 않는 원칙을 명시함
