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
- 남은 과제는 baseline 자체보다 약점 slice 보완임
- 현재 운영 판단
- `Cold = LAD`

### Warm

- 선형보다 트리 모델이 확실히 우세했음
- `LightGBM`가 가장 안정적이었고 `CatBoost`는 열세였음
- 현재 운영 판단
- `Warm = tuned LightGBM`

### production 평가

- Cold
- `med_APE 0.3207`
- `W30 0.4640`
- Warm
- `med_APE 0.2056`
- `W30 0.5988`

## 6. 현재까지 확인된 핵심 해석

### 이미 비교적 분명한 것

- Warm에서는 작가 정보가 중요함
- Warm에서는 `LightGBM` 계열이 강함
- Cold에서는 복잡한 비선형 모델보다 robust 선형 계열이 더 적합함
- `source_platform`은 운영 입력 변수로 쓰기 어려움

### 아직 더 봐야 하는 것

- Cold 약점 slice를 제한적으로 보완할 수 있는지
- 특히 `Cold 2D` 구간을 별도 fallback으로 다룰 가치가 있는지
- H13~H15처럼 재료 세분화, 크기-재료 조합, 결측 패턴 피처가 약점 slice를 줄이는지
- 이때 공통 피처는 Cold뿐 아니라 Warm에서도 같이 확인해야 함

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

- `Cold 2D` 한정 fallback 또는 expert 구조
- 이유
- `PR17`, `PR18`, `PR19`에서 전면 모델 교체 근거는 약했지만
- `Cold 2D`에서는 반복적으로 개선 신호가 있었음

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
- 가설 상태표
- [`docs/track3_hypothesis_table.md`](/Users/bo/VisionAI/docs/track3_hypothesis_table.md:1)
- 4
- 가설 결과 종합표
- [`docs/track3_hypothesis_result_summary.md`](/Users/bo/VisionAI/docs/track3_hypothesis_result_summary.md:1)
- 5
- 계획서
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 6
- 실험 결과 요약표 또는 개별 기록
- [`docs/track3_experiment_results_table.md`](/Users/bo/VisionAI/docs/track3_experiment_results_table.md:1)
- [`docs/track3_experiments/INDEX.md`](/Users/bo/VisionAI/docs/track3_experiments/INDEX.md:1)

### 상세 수치와 해석이 필요할 때

- 개별 실험 기록
- [`docs/track3_experiments/INDEX.md`](/Users/bo/VisionAI/docs/track3_experiments/INDEX.md:1)
- 재현 요약
- [`docs/track3_reproduction_summary_20260513.md`](/Users/bo/VisionAI/docs/track3_reproduction_summary_20260513.md:1)

## 10. 한 줄 정리

- Track 3는 현재 `Cold = LAD`, `Warm = tuned LightGBM`를 기본 운영안으로 두고 있으며, 다음 개선 우선순위는 `Cold 2D` 약점 구간을 제한적으로 보완할 수 있는지 확인하는 것임
