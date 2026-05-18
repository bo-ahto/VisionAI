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
| T5-H10 | T5-G5 | 재료·지지체·크기 조합 피처는 단독 피처보다 가격 설명력을 높일 수 있다 | full_size 후보에 medium-size, support-size, large/3D/material rule flag를 추가해 Warm/Cold validation 성능 비교 | `track5_train`, validation split | 조합 피처 | T5-E006 full_size 후보 | median APE 또는 p95 APE 개선 시 후보 유지 | 부분 검증 | validation 1회 | 일부 개선 신호는 있으나 median과 p95를 동시에 개선한 단일 후보는 없음 | T5-E007 | 보조 후보로 두고 모델군 재비교에서 재확인 |
| T5-H11 | T5-G6, T5-G8 | 후보 피처셋이 정해지면 기준 모델만이 아니라 여러 모델군에서 다시 비교해야 최종 후보를 고를 수 있다 | Warm 후보 피처셋과 Cold 후보 피처셋을 Ridge/Quantile/Tree 계열로 재비교 | `track5_train`, validation split | 후보 피처셋 | E005~E007 기준 모델 | validation median APE와 p95 APE가 개선된 모델 후보 선정 | 검증 완료 | validation 모델군 비교 | Warm은 Huber+full_size, Cold는 Quantile+full_size를 1순위 후보로 선정 | T5-E008 | test 전 후보 목록 고정 |
| T5-H12 | T5-G8 | test를 보기 전에 최종 확인 후보와 판단 기준을 고정해야 test 과적합을 줄일 수 있다 | validation 결과를 근거로 Warm/Cold 1순위·보조 후보와 test 판단 기준을 문서로 고정 | T5-E002~E008 결과 | 최종 확인 후보 목록 | validation 결과 | 후보와 test 판단 기준이 고정되면 완료 | 검증 완료 | 문서 고정 | Warm/Cold 최종 확인 후보와 test 판단 기준 고정 완료 | T5-E009 | T5-E010에서 test 확인 |
| T5-H13 | T5-G8 | validation에서 고정한 최종 후보가 test에서도 유지되어야 Track5 운영 후보로 볼 수 있다 | T5-E009에서 고정한 후보만 test_warm/test_cold에서 최종 확인 | `track5_train`, `track5_test_warm`, `track5_test_cold` | 최종 후보 피처셋 | validation 성능 | test median APE와 p95 APE가 허용 가능한 수준이면 후보 유지 | 검증 완료 | test 1회 | Warm은 Huber 후보 유지, Cold는 Quantile+full_size 유지. 단 Cold test median APE `0.3918`, p95 `2.0152`로 신뢰도/가격 범위 정책 필요 | T5-E010 | Warm 수렴 재검증, Cold 위험 구간 정책 실험 |
| T5-H14 | T5-G6 | Warm Huber 후보는 수렴 설정을 바꿔도 성능 판단이 크게 흔들리지 않아야 한다 | Huber 반복 횟수를 늘려 validation/test 성능과 반복 횟수 도달 여부를 비교 | `track5_train`, `track5_val_warm`, `track5_test_warm` | Warm full_size 후보 | T5-E010 Warm 후보 | median APE 변화가 작고 수렴 경고가 해소되면 안정성 보완 | 검증 완료 | validation/test 설정 비교 | `max_iter=3000`에서 수렴 경고 해소, test median APE `0.1580`으로 판단 유지 | T5-E011 | 운영 학습 설정에 `max_iter=3000` 반영 |
| T5-H15 | T5-G7 | Cold는 위험 구간을 나누면 단일 가격 사용 가능 범위를 더 명확히 정할 수 있다 | Cold final 후보 예측 결과를 대형/3D/unknown/risk score 구간별로 나누어 오차 비교 | `track5_test_cold` | Cold risk flags | Cold 전체 성능 | 고위험 구간이 전체보다 높은 오차를 보이면 경고 정책 후보 | 부분 검증 | test slice 분석 | `support_unknown`은 median APE `0.5272`, p95 `4.4609`로 강한 위험 신호. 대형/3D 단독 기준은 약함 | T5-E012 | 가격 범위 커버리지 검증 필요 |
| T5-H16 | T5-G7, T5-G8 | validation 오차로 만든 가격 범위가 test에서 실제 가격을 충분히 포함해야 서비스 출력 정책으로 쓸 수 있다 | validation 절대 로그 오차 p50/p80/p90를 가격 범위 폭으로 정하고 test coverage 확인 | `track5_val_*`, `track5_test_*` | 최종 후보 예측값 | 단일 가격 출력 | 목표 coverage와 범위 폭이 실무적으로 허용 가능하면 범위 정책 후보 | 부분 검증 | validation calibration + test coverage | Warm p80 범위는 coverage `0.7828`, 폭 `2.14배`로 검토 가능. Cold p80은 coverage `0.7845`지만 폭 `4.63배`로 큼 | T5-E013 | Cold는 범위보다 경고/추가정보 정책 필요 |
| T5-H17 | T5-G3 | Warm 작가 가격 통계를 더 세분화하면 성능이 개선될 것이다 | 작가별 q10/q25/q75/q90, min/max/std/span/count bucket을 추가해 Warm validation 성능 비교 | `track5_train`, `track5_val_warm` | 확장 작가 가격 통계 | Warm full_size | median APE 또는 p95 APE 개선 | 부분 검증 | validation 1회 | 확장 통계 단독은 median `0.1516`으로 base `0.1500`보다 약함. 단 OOF 확장에서는 p95 개선 신호 있음 | T5-E014 | OOF 기준으로만 후속 검토 |
| T5-H18 | T5-G6 | Warm 작가 통계는 OOF 방식으로 만들어도 성능이 유지되어야 안정적인 피처로 볼 수 있다 | train row의 작가 통계를 KFold OOF로 만들고 기존 방식과 validation 성능 비교 | `track5_train`, `track5_val_warm` | OOF 작가 통계 | 기존 train 전체 통계 | 성능 급락이 없고 p95가 개선되면 안정성 후보 | 부분 검증 | validation 1회 | OOF base median `0.1516`, OOF extended p95 `0.6893`으로 tail 개선 신호 | T5-E015 | 최종 후보 전 OOF+max_iter3000 재검증 |
| T5-H19 | T5-G4, T5-G7 | Cold 결측/unknown 상태를 피처로 넣으면 위험 구간 오차가 줄어들 것이다 | medium_unknown, support_unknown, missing_info_count를 추가해 Cold validation 성능 비교 | `track5_train`, `track5_val_cold` | 결측 flag | Cold full_size | median APE 또는 p95 APE 개선 | 검증 완료 | validation 1회 | missing flag 추가는 median `0.3437`, p95 `1.8242`로 base보다 개선 없음 | T5-E016 | 단순 flag는 미채택 |
| T5-H20 | T5-G4, T5-G7 | Cold support_unknown 구간은 전용 fallback 모델로 보완할 수 있다 | support_unknown 작품에 별도 Quantile 모델을 적용해 전체/구간 성능 비교 | `track5_train`, `track5_val_cold` | support_unknown fallback | Cold full_size | 전체 median 또는 support_unknown p95 개선 | 부분 검증 | validation 1회 | 전체 median은 `0.3432`→`0.3401`로 소폭 개선, support_unknown p95는 `8.2886`으로 여전히 큼 | T5-E017 | fallback은 보류, 구간 정의 재검토 |
| T5-H21 | T5-G4, T5-G7 | Cold 예측 가격대별 보정은 전체 Cold 오차를 줄일 수 있다 | validation 예측 가격 구간별 residual 보정값을 만들고 test_cold에 적용 | `track5_val_cold`, `track5_test_cold` | 예측 가격대 보정 | Cold final 후보 | test median APE, Within-50 개선 | 부분 검증 | validation 보정 + test 확인 | test median `0.3918`→`0.3837`, Within-50 `0.5746`→`0.6008` 개선. p95는 개선 없음 | T5-E018 | Cold 후보 후처리로 유지 |
| T5-H22 | T5-G3, T5-G6 | Warm OOF extended 후보는 최종 학습 설정에서도 성능이 유지되어야 한다 | OOF extended 작가 통계와 Huber `max_iter=3000` 설정으로 validation/test 재검증 | `track5_train`, `track5_val_warm`, `track5_test_warm` | OOF extended artist stats | Warm full_size 후보 | p95 개선이 유지되고 median 악화가 제한적이면 challenger 유지 | 검증 완료 | validation/test 재검증 | test는 median `0.1570`, p95 `0.8471`로 양호하지만 val은 `0.1615`, p95 `0.7368`로 약하고 수렴 경고가 남아 1순위 교체는 보류 | T5-E019 | Warm full_size 1순위 유지 |
| T5-H23 | T5-G4, T5-G7 | Cold 가격대 보정과 위험 경고 정책을 함께 쓰면 서비스 해석 가능성이 높아질 것이다 | 가격대 보정 전후를 standard/caution 그룹으로 나누어 test 성능 비교 | `track5_test_cold` | price correction, risk policy | Cold final 후보 | standard 그룹이 caution보다 낮은 오차이고 보정 후 전체 median/Within 개선 | 검증 완료 | test 정책 검증 | hybrid 정책이 median `0.3764`, p95 `1.9047`, Within-50 `0.6046`으로 baseline보다 개선 | T5-E020 | Cold 운영 정책 후보로 유지 |
| T5-H24 | T5-G8 | 최종 후보 artifact 생성 전 데이터/결과/예측 파일이 재현 가능하게 묶여 있어야 한다 | 핵심 split, 결과, 예측 파일 존재 여부와 SHA256 manifest 생성 | Track5 artifacts | artifact manifest | 파일 누락 없음 | manifest status가 ready이면 완료 | 검증 완료 | manifest 점검 | manifest 상태 `ready_for_artifact_generation`, 누락 파일 없음 | T5-E021 | 실제 artifact 생성 단계 진행 가능 |
