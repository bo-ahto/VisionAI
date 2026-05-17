# Track 5 가설 상태표

- 목적: Track 5 모델 실험 가설을 세부 목표별로 관리
- 기준일: 2026-05-18
- 작성 방식: 개조식
- 원칙: 데이터셋 split 기준을 먼저 고정하고, 이후 모델/피처 실험만 가설로 관리

## 1. 세부 목표

| 목표 ID | 세부 목표 | 설명 |
|---|---|---|
| T5-G1 | 데이터셋 기준 고정 | Warm / Cold split이 최종 실험에 충분한지 확인 |
| T5-G2 | 기본 예측 가능성 확인 | 구조-only baseline으로 새 split에서 기본 예측 가능성 확인 |
| T5-G3 | Warm 성능 개선 | 작가 이력 정보가 있는 상황에서 Warm 성능 개선 |
| T5-G4 | Cold 성능 개선 | 신규 작가 상황에서 작가 정보 없이 Cold 성능 개선 |
| T5-G5 | 운영 가능 피처 선정 | 실제 입력에서 만들 수 있는 피처만 최종 후보로 유지 |
| T5-G6 | 모델 안정성 확인 | validation/test 및 seed 변화에도 성능이 유지되는지 확인 |
| T5-G7 | 가격 범위/신뢰도 대응 | 단일 가격만으로 부족한 구간을 식별하고 범위/경고 정책 설계 |
| T5-G8 | 최종 운영 후보 확정 | Warm / Cold 모델, 피처, 라우팅, 출력 정책을 최종 정리 |

## 2. 가설 상태표

| 가설 ID | 세부 목표 | 가설 요약 | 연구 방법 | 사용 데이터 | 핵심 피처 | 비교 기준 | 성공 기준 | 현재 상태 | 검증 강도 | 현재 판단 | 관련 실험 | 후속 필요 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T5-H1 | T5-G1 | Track5 split은 Track4보다 Warm 최종 평가에 더 적합할 것이다 | Track4 split과 Track5 split의 Warm/Cold rows, 작가 수, 누수 검증 결과 비교 | `track5_split` | split metadata | Track4 split | Warm test rows 증가, Cold/train 작가 겹침 0, Warm 작가 train 존재 | 검증 완료 | split 생성 검증 | Warm test `511`건, Cold/train 작가 겹침 `0`, Warm 평가 작가 train 존재 확인 | T5-E001 | 모델 실험 기준 split으로 사용 |
| T5-H2 | T5-G2 | 새 split에서도 작품 구조 정보만으로 Warm / Cold 기본 예측이 가능할 것이다 | 작가 피처 없이 구조-only baseline을 학습하고 Warm/Cold validation 성능 비교 | `track5_train`, `track5_val_warm`, `track5_val_cold` | 구조 피처 | 단순 중앙값 baseline | median APE가 단순 baseline보다 개선 | 검증 완료 | validation 1회 | Huber 기준 Warm median APE `0.4662`, Cold median APE `0.3718`로 단순 중앙값보다 개선 | T5-E002 | Warm 작가 피처 실험으로 진행 |
| T5-H3 | T5-G3 | Warm에서는 작가 key와 train 기준 작가 이력 피처가 성능을 개선할 것이다 | 구조-only Warm 모델과 작가 피처 포함 모델 비교 | `track5_train`, `track5_val_warm`, `track5_test_warm` | `artist_key`, `artist_works_log`, 작가 통계 후보 | T5-H2 Warm baseline | Warm median APE 개선, p95 악화 제한 | 검증 완료 | validation 1회 | 작가 key+이력+train 가격 통계가 Warm median APE `0.2279`, p95 `0.9083`으로 최선 | T5-E003 | 최종 후보 전 비선형 모델 비교 필요 |
| T5-H4 | T5-G4 | Cold에서는 robust 선형 계열이 복잡한 트리 모델보다 안정적일 것이다 | Quantile/Huber/Ridge와 트리 모델을 같은 Cold 피처셋으로 비교 | `track5_train`, `track5_val_cold`, `track5_test_cold` | Cold 구조 피처 | T5-H2 Cold baseline | Cold median APE 또는 p95 개선 | 검증 완료 | validation 1회 | Quantile median APE `0.3564`, p95 `1.8218`로 최선 | T5-E004 | 피처 실험 기준 Cold 모델로 사용 |
| T5-H5 | T5-G5 | Track4에서 미채택된 생성 조합 피처는 Track5 새 split에서도 최종 피처로 부적합할 가능성이 높다 | baseline 피처와 조합 피처 추가 모델을 Track5 validation/test에서 비교 | `track5_split` | medium-size, support-size, rule flag | 기본 피처셋 | test median APE 개선 없으면 미채택 | 예정 | 미실행 | 아직 미실행 | - | 피처 조합 재검증 |
| T5-H6 | T5-G6 | Track5 최종 후보는 fixed test와 반복 split에서 모두 안정적이어야 한다 | 후보 모델 확정 후 반복 Warm/Cold split 또는 seed 반복으로 평균/표준편차 확인 | `track5_split`, 반복 holdout | 최종 후보 피처 | 단일 test 결과 | 평균 성능 유지, 표준편차 과대 아님 | 예정 | 미실행 | 아직 미실행 | - | 후보 확정 후 진행 |
| T5-H7 | T5-G7 | Cold는 위험 구간을 나누면 단일 가격 사용 가능 범위를 더 명확히 정할 수 있다 | 3D, 대형, unknown, low/high risk별 오차와 범위 폭 비교 | `track5_val_cold`, `track5_test_cold` | risk flags | Cold 전체 정책 | low-risk와 high-risk 오차 차이 확인 | 예정 | 미실행 | 아직 미실행 | - | Cold 정책 실험 |
| T5-H8 | T5-G5, T5-G8 | 피처 실험 전에 Warm/Cold 기준 모델과 기준 피처셋을 고정해야 이후 실험 해석이 가능하다 | T5-E002~E004 결과를 종합해 Warm/Cold 기준 모델과 기준 피처셋을 문서로 고정 | `track5_split` | Warm 기준 피처, Cold 기준 피처 | E002~E004 결과 | 기준 모델/피처가 명확히 정리되면 완료 | 검증 완료 | 결과 종합 | Warm은 Ridge+작가 key/이력/가격통계, Cold는 Quantile+구조 피처를 기준으로 고정 | T5-E005 | 이후 피처 실험은 이 기준선 대비 비교 |
| T5-H9 | T5-G5 | 크기/지지체/3D 피처는 Warm과 Cold에서 같은 효과를 내지 않을 수 있으므로 기준 모델별로 따로 검증해야 한다 | 기준 Warm Ridge와 기준 Cold Quantile에서 size/support/3D 피처 제거·추가 조합을 비교 | `track5_train`, validation split | size/support/3D 피처 조합 | T5-E005 기준선 | validation median APE 또는 p95 개선 시 후보 유지 | 부분 검증 | validation 1회 | Warm/Cold 모두 full_size 후보가 안정적이며, Cold full_size median APE `0.3432`로 기준선 개선 | T5-E006 | 생성 조합 피처 추가 검증 |
