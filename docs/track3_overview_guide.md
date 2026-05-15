# Track 3 종합 안내 문서

- 목적: Track 3 실험을 처음 보거나 다시 시작할 때, 이 문서 하나만 먼저 읽어도 전체 흐름을 이해할 수 있도록 정리한 문서
- 권장 사용 방식:
- 먼저 이 문서를 읽음
- 그다음 필요할 때만 세부 문서로 들어감
- 문서 구조를 그림으로 설명해야 할 때는 아래 문서를 함께 사용함
- [`docs/track3_document_flowchart.md`](/Users/bo/VisionAI/docs/track3_document_flowchart.md:1)

## 1. Track 3를 왜 하는가

- Track 3의 목표는 작품 가격 예측 모델을 만드는 것임
- 다만 단순히 잘 맞는 모델 하나를 찾는 것이 목적이 아님
- `재현 가능하고 비교 가능한 실험 체계` 안에서 모델을 개선하는 것이 핵심임

## 2. Track 3에서 가장 중요한 원칙

- 데이터를 먼저 고정하고 실험을 시작함
- Warm과 Cold를 반드시 분리해서 봄
- 운영에서 다시 만들 수 있는 변수만 최종 후보로 사용함
- 실험은 `가설 -> 실험 방법 결정 -> 실험 -> 검증 -> 결론` 순서로 진행함
- 실험 1건마다 기록을 남김
- 상위 가설과 후속 가설을 연결해서 관리함
- 예시
- H2는 Cold 예측 가능성을 보는 상위 가설
- H13~H15는 H2 이후 Cold 약점 보완을 위한 후속 가설
- Warm / Cold 공통으로 만들 수 있는 피처는 두 평가셋 모두에서 확인함

## 3. Warm / Cold는 무엇이 다른가

### Warm

- 학습 데이터에 이미 등장한 작가의 새 작품을 예측하는 상황
- 작가 정보 활용 가능
- 현재 주력 모델
- `tuned LightGBM`

### Cold

- 학습 데이터에 한 번도 등장하지 않은 신규 작가의 작품을 예측하는 상황
- 작가 정보에 직접 의존하기 어려움
- 작품 자체 구조 정보 중심으로 예측해야 함
- 현재 주력 모델
- `LAD / Quantile / Huber` 계열

## 4. 현재 고정된 데이터 기준

- 공식 학습 데이터
- [`data/release_split/track3_train.csv`](/Users/bo/VisionAI/data/release_split/track3_train.csv)
- 공식 Warm 평가 데이터
- [`data/release_split/track3_test_warm.csv`](/Users/bo/VisionAI/data/release_split/track3_test_warm.csv)
- 공식 Cold 평가 데이터
- [`data/release_split/track3_test_cold.csv`](/Users/bo/VisionAI/data/release_split/track3_test_cold.csv)

### 현재 split 규모

- train
- 34,629개 작품
- 1,932명 작가
- test_warm
- 1,685개 작품
- 1,685명 작가
- test_cold
- 3,823개 작품
- 200명 작가

## 5. 현재 실험 결과 기준 결론

### Cold

- 트리 모델보다 robust 선형 계열이 더 안정적이었음
- `LightGBM`, `XGBoost`, `CatBoost`, Optuna 튜닝 모두 운영 채택 근거 부족
- 작가 정보 없이도 작품 구조 변수만으로 baseline은 성립함
- 3D 작품은 3D 피처를 조건부 적용할 때 개선됨
- 현재 운영 판단
- `Cold = H32 조건부 fallback`
- 2D / 일반 작품은 기본 LAD 계열
- 3D 작품은 3D 피처 포함 LAD 계열

### Warm

- 선형보다 트리 모델이 확실히 우세했음
- `LightGBM`가 가장 안정적이었고 `CatBoost`는 열세였음
- 현재 운영 판단
- `Warm = H66 larger-low-lr LightGBM`

### 현재 후보 성능

- Cold
- H32 median APE `0.2786`
- Warm
- H66 mean median APE `0.1051`
- 가격 범위
- H70 내부 calibration 기준 Warm 전체 범위 `x1.52`, Cold 전체 범위 `x2.27`
- Warm coverage `0.821`, Cold coverage `0.855`는 목표 80%에 근접하지만 서비스 확정 지표는 아님
- 가격 범위는 폭과 사용자 해석 가능성을 함께 검토해야 하므로 현재는 운영 검토 후보로 봄
- Cold 위험도 추가 검증
- H73-H80 기준, 가장 안정적인 Cold 후보도 표준 3D `x2.06`, 선택적 서비스 후보 `x2.10` 수준임
- 따라서 Cold는 정확한 단일 가격보다 참고 추정가와 낮은 신뢰도 경고 중심으로 봐야 함
- Cold tail risk 추가 검증
- H81-H86 기준 high-risk shrink로 p95는 `1.4860 -> 1.2961` 수준까지 줄일 수 있음
- 다만 q80 가격 배수는 `x2.00 -> x2.08`로 줄지 않아 가격 범위 개선은 아님

## 6. 현재까지 확인된 핵심 해석

### 이미 비교적 분명한 것

- Warm에서는 작가 정보가 중요함
- Warm에서는 `LightGBM` 계열이 강함
- Cold에서는 복잡한 비선형 모델보다 robust 선형 계열이 더 적합함
- `source_platform`은 운영 입력 변수로 쓰기 어려움
- Cold는 저위험/고위험 구분이 가능하지만, 저위험도 가격 범위가 넓어 단일 가격 서비스 수준은 아님
- Cold tail 보정은 extreme error 완화에는 도움되지만 가격 범위 폭을 줄이지는 못함

### 아직 더 봐야 하는 것

- 작가 이력 피처를 거래일/등록일 기준으로 temporal-safe하게 다시 계산할 수 있는지
- release split 반복 사용에 따른 의사결정 과적합 가능성을 최종 출시 전 새 holdout 또는 내부 CV로 줄일 수 있는지
- H70 calibration split 방식을 production 학습 pipeline에 고정할 수 있는지
- 운영 입력 결측 데이터가 확보될 때 H15/H9 결측 대응을 다시 검증할지

## 7. 지금 바로 실험을 시작한다면 어떤 순서로 하면 되는가

- 1
- 현재 가설 확인
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- 2
- 가설별 근거 실험 확인
- [`docs/track3_hypothesis_result_summary.md`](/Users/bo/VisionAI/docs/track3_hypothesis_result_summary.md:1)
- 3
- 기준 원칙 확인
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 4
- 개별 실험 기록 파일 초안 작성
- [`docs/track3_experiments/TEMPLATE.md`](/Users/bo/VisionAI/docs/track3_experiments/TEMPLATE.md:1)
- 5
- 스크립트 실행
- 6
- 결과 JSON 확인
- 7
- 개별 기록 / 결과 요약표 / 인덱스 업데이트

## 8. 지금 가장 유력한 다음 실험

- `작가 이력 피처 temporal-safe 재검증`
- 이유
- 현재 Warm 최적 후보는 작가 가격 통계에 크게 의존함
- 하지만 현재 release split에는 날짜 컬럼이 없어 예측 시점 이후 정보가 섞이지 않는지 아직 확정할 수 없음
- 거래일/등록일 컬럼 확보 후 예측 시점 이전 데이터만으로 H10/H17/H66을 다시 확인해야 함

## 9. 어떤 문서를 언제 보면 되는가

### 이 문서만 먼저 보면 되는 경우

- 전체 흐름을 빠르게 이해하고 싶을 때
- 지금 어떤 방향으로 가고 있는지 알고 싶을 때

### 계획서를 추가로 보면 좋은 경우

- 데이터 기준
- 변수 원칙
- 평가 지표
- 실험 순서를 정확히 확인하고 싶을 때
- 문서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)

### 가설 설명 문서를 보면 좋은 경우

- 왜 그 가설을 보는지 배경까지 알고 싶을 때
- 문서
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)

### 결과를 한눈에 보고 싶을 때

- 가설 상태
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- 가설별 근거와 현재 결론
- [`docs/track3_hypothesis_result_summary.md`](/Users/bo/VisionAI/docs/track3_hypothesis_result_summary.md:1)
- 실험 결과 요약
- [`docs/track3_experiment_results_table.md`](/Users/bo/VisionAI/docs/track3_experiment_results_table.md:1)

### 추천 보는 순서

- 1
- 이 문서
- [`docs/track3_overview_guide.md`](/Users/bo/VisionAI/docs/track3_overview_guide.md:1)
- 2
- 문서 구조 순서도
- [`docs/track3_document_flowchart.md`](/Users/bo/VisionAI/docs/track3_document_flowchart.md:1)
- 3
- 현재 의사결정 요약
- [`docs/track3_current_decision_summary.md`](/Users/bo/VisionAI/docs/track3_current_decision_summary.md:1)
- 4
- 가설 상태표
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- 5
- 가설 결과 종합표
- [`docs/track3_hypothesis_result_summary.md`](/Users/bo/VisionAI/docs/track3_hypothesis_result_summary.md:1)
- 6
- 계획서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 7
- 실험 결과 요약표 또는 개별 기록
- [`docs/track3_experiment_results_table.md`](/Users/bo/VisionAI/docs/track3_experiment_results_table.md:1)
- [`docs/track3_experiments/INDEX.md`](/Users/bo/VisionAI/docs/track3_experiments/INDEX.md:1)

### 상세 수치와 해석이 필요할 때

- 개별 실험 기록
- [`docs/track3_experiments/INDEX.md`](/Users/bo/VisionAI/docs/track3_experiments/INDEX.md:1)
- 재현 요약
- [`docs/track3_reproduction_summary_20260513.md`](/Users/bo/VisionAI/docs/track3_reproduction_summary_20260513.md:1)

## 10. 한 줄 정리

- Track 3는 현재 `Warm = H66 LightGBM`, `Cold = H32 조건부 fallback`을 최우선 후보로 두고 있으며, 운영 확정 전 핵심 과제는 작가 이력 피처의 temporal-safe 재검증과 calibration pipeline 고정임
