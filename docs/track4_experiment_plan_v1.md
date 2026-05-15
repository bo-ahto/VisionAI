# Track 4 실험 계획서 v1

- 목적: Track 3 결과를 보존한 상태에서 운영 적용 가능성을 검증하기 위한 Track 4 실험 기준 문서
- 기준일: 2026-05-15
- 작성 방식: 개조식

## 1. Track 4의 목적

- 작품 1건의 정보를 보고 가격을 예측하는 모델을 실제 서비스에 적용할 수 있는지 검증함
- Track 3에서 찾은 모델 후보를 그대로 믿지 않고, 운영 조건에서 다시 확인함
- Track 4는 Track 3 데이터셋을 그대로 재사용하지 않고, 기존에 수집된 1차 시장 데이터를 다시 통합/클렌징하는 단계부터 시작함
- 성능뿐 아니라 아래 항목을 함께 판단함
- 입력값 재현 가능성
- 데이터 누수 가능성
- Warm / Cold 라우팅 기준
- 가격 범위 폭
- 신뢰도 경고 기준
- 배포 및 재학습 가능성
- Warm / Cold 분리 프로세스 상세 문서
- `docs/track4_warm_cold_process.md`

## 2. Track 3 보존 원칙

- Track 3 문서와 결과는 확정된 실험 기록으로 보존함
- Track 4에서는 Track 3 파일을 직접 수정하지 않음
- Track 3 결과는 baseline으로만 참조함
- Track 4에서 생성되는 문서, 스크립트, 결과는 모두 `track4` 이름을 사용함

## 3. Track 4 기준 baseline

- Warm baseline
- Track 3 H66 larger-low-lr LightGBM
- 주요 기준 성능: mean median APE `0.1051`
- Cold baseline
- Track 3 H32 조건부 fallback
- 주요 기준 성능: median APE `0.2786`
- 가격 범위 baseline
- Track 3 H70 내부 calibration 기반 조건별 가격 범위
- Warm 전체 `x1.52`
- Cold 전체 `x2.27`

## 4. Track 4 핵심 질문

- Q0. 파편화된 1차 시장 데이터를 실험 가능한 기준 데이터셋으로 준비했는가
- Q1. Track 3 Warm 후보는 예측 시점 기준으로도 안전한가
- Q2. Track 3 Cold 후보는 실제 서비스에서 어느 구간까지 쓸 수 있는가
- Q3. Warm / Cold 라우팅 기준은 작가 작품 수 기준으로 조정할 필요가 있는가
- Q4. 가격 범위는 너무 넓지 않은가
- Q5. 신뢰도 경고 기준은 실험 근거로 설명 가능한가
- Q6. 최종 모델은 재현 가능한 pipeline으로 만들 수 있는가

## 5. Track 4 가설 관리 방식

- 데이터 통합/클렌징은 모델 실험 가설이 아니라 실험 준비 체크포인트로 관리함
- 실험 준비 체크포인트는 `T4-D번호` 형식으로 관리함
- 예시
- `T4-D0`
- `T4-D1`
- `T4-D2`
- 가설 ID는 `T4-H번호` 형식으로 관리함
- 예시
- `T4-H1`
- `T4-H2`
- `T4-H3`
- 각 가설은 아래 항목을 반드시 포함함
- 세부 목표
- 가설 요약
- 왜 필요한지
- 사용 데이터
- 사용 피처
- 비교 기준
- 성공 기준
- 검증 강도
- 현재 판단
- 후속 필요

## 6. 실험 준비 체크포인트

- 아래 항목은 모델 성능을 검증하는 가설이 아님
- 모델 실험을 시작하기 전에 데이터 기준이 믿을 수 있는지 확인하는 준비 단계임
- 상세 실행 방법과 추가 데이터 반영 방법은 별도 문서에서 관리함
- 상세 문서: `docs/track4_cleaning_pipeline.md`
- 실행 스크립트: `scripts/track4/run_cleaning_pipeline.py`

| 체크포인트 ID | 영역 | 확인 내용 | 주요 산출물 | 상태 |
|---|---|---|---|---|
| T4-D0 | raw 데이터 통합 | 파편화된 1차 시장 원본을 출처별 원본 컬럼 보존 방식으로 통합 | `track4_primary_market_raw_collected.csv` | 완료 |
| T4-D1 | 가격 정합성 | 가격 결측, 문의가, 통화, 하한/상한, 원화 가격 사용 가능 여부 확인 | `track4_price_consistency_audit.csv` | 완료 |
| T4-D2 | 크기 정합성 | 가로/세로/깊이, 면적, 극단 크기, 비율 이상값 확인 | `track4_size_consistency_audit.csv` | 완료 |
| T4-D3 | 작가명 정합성 | 작가명 표준화, 한글명 매핑, 작가 key 생성, 식별 불가 row 확인 | `track4_artist_consistency_audit.csv` | 완료 |
| T4-D4 | 재료/지지체 정합성 | 원문 재료 기준 대표 재료/지지체 분류와 unknown 비율 확인 | `track4_medium_support_consistency_audit.csv` | 완료 |
| T4-D5 | 중복 정합성 | 같은 작품 중복 후보와 대표 row 여부를 flag로 관리 | `track4_duplicate_consistency_audit.csv` | 완료 |
| T4-D6 | 출처/갤러리 메타 점검 | 출처는 피처 제외, 갤러리 티어는 보조 메타로만 관리 | `track4_source_bias_audit.md`, `track4_gallery_metadata_audit.csv` | 완료 |
| T4-D7 | feature 후보 생성 | 모델 입력 후보와 학습 후보 flag 생성 | `track4_primary_market_feature_candidates_v1.csv` | 완료 |
| T4-D8 | Warm/Cold split 생성 | train, val_warm, val_cold, test_warm, test_cold 생성 및 작가 overlap 검증 | `data/track4_split/*.csv` | 완료 |
| T4-D9 | 컬럼별 값 재점검 | 전체 컬럼의 타입, 결측, 범위, 파생값 계산 일치 여부 확인 | `track4_column_value_consistency_audit.csv` | 완료 |

## 7. 우선 모델 실험 가설 후보

| 가설 ID | 세부 목표 | 가설 요약 | 우선순위 | 상태 |
|---|---|---|---:|---|
| T4-H1 | temporal-safe 검증 | Warm 작가 이력 피처는 예측 시점 이전 정보만으로 다시 계산해도 성능이 유지될 것이다 | 1 | 예정 |
| T4-H2 | Warm / Cold 라우팅 | 작가 작품 수 기준을 1건보다 높이면 일부 저이력 Warm의 안정성이 개선될 수 있다 | 2 | 예정 |
| T4-H3 | Cold 서비스 가능 구간 | Cold는 전체 서비스보다 저위험 구간에 제한할 때 더 실용적인 가격 범위를 제공할 것이다 | 3 | 예정 |
| T4-H4 | 가격 범위 UX | 단일 가격보다 가격 범위와 신뢰도 등급을 함께 제공하는 방식이 운영상 더 안전할 것이다 | 4 | 예정 |
| T4-H5 | 배포 재현성 | Track 3 후보 모델은 동일 입력 schema와 고정 pipeline으로 재학습 가능해야 한다 | 5 | 예정 |

## 8. 실험 진행 순서

- 0단계: 1차 시장 데이터 통합/클렌징
- 파편화된 원천 파일을 공통 schema로 모음
- 가격, 크기, 재료, 작가명 기준을 정리함
- 이 단계가 끝나기 전에는 Track 4 split을 공식 확정하지 않음
- 1단계: Track 3 baseline 고정
- 어떤 결과를 비교 기준으로 볼지 먼저 고정함
- 2단계: Track 4 데이터 기준 정의
- 기존 release split을 그대로 쓸지, 추가 holdout을 만들지 결정함
- Track 4에서는 `track4_train.csv`를 공통 학습 데이터로 사용하되, Warm / Cold 평가는 분리함
- Warm / Cold 프로세스는 `docs/track4_warm_cold_process.md` 기준으로 진행함
- 3단계: 가설별 연구 방법 작성
- 바로 실험하지 않고 먼저 방법을 문서화함
- 4단계: 실험 실행
- 스크립트와 결과 파일은 `track4` 이름으로 저장함
- 5단계: 결과 검증
- Warm / Cold를 분리해서 판단함
- Warm은 작가 정보 활용 모델, Cold는 작가 정보 제외 모델을 별도 후보로 관리함
- 6단계: 운영 판단 정리
- 채택, 보류, 중단으로 결론을 남김

### 8.1 Warm / Cold 분리 실행 순서

| 순서 | Warm | Cold | 공통 판단 |
|---:|---|---|---|
| 1 | Warm split 작가가 train에 존재하는지 확인 | Cold split 작가가 train에 없는지 확인 | split 검증 실패 시 모델 실험 중단 |
| 2 | 작품 구조 only baseline 생성 | 작품 구조 only baseline 생성 | 같은 기본 피처에서 출발 |
| 3 | 작가명/작가 이력 피처 추가 | 작가 피처 제외 유지 | Warm/Cold 정보 차이 명확화 |
| 4 | LightGBM/CatBoost/XGBoost/선형 비교 | LAD/Quantile/Huber/Ridge/Tree 비교 | 모델군을 분리해서 비교 |
| 5 | 저이력 Warm 오차와 가격 범위 확인 | 2D/3D/대형/unknown 구간 오차와 가격 범위 확인 | 신뢰도 정책 분리 |
| 6 | Warm 최종 후보 test 확인 | Cold 최종 후보 test 확인 | validation 선택, test 최종 확인 |

## 9. 평가 지표

- 기본 지표
- median APE
- MAPE
- RMSE(log)
- Within-30%
- Within-50%
- 가격 범위 지표
- coverage
- price range multiplier
- 구간별 coverage
- 운영 지표
- 입력값 결측률
- 예측 가능 비율
- 신뢰도 경고 비율
- 재학습 재현 가능 여부

## 10. 판단 원칙

- 성능이 좋아도 운영에서 만들 수 없는 피처는 최종 후보에서 제외함
- `source`, `source_file`, `track4_source`는 운영 입력 피처로 사용하지 않음
- 출처 정보는 데이터 품질 감사, 분포 확인, 원본 추적, 중복 처리에만 사용함
- 출처별 가격대 차이가 있더라도 모델에 출처를 직접 넣어 보정하지 않음
- Warm과 Cold를 합친 평균 성능으로 판단하지 않음
- 가격 범위는 coverage만 보지 않고 폭도 함께 봄
- test 결과를 보고 정책을 정하지 않음
- 정책 선택은 train/internal calibration에서 하고, test는 검증에만 사용함
- Track 3보다 성능이 좋아도 재현성이 낮으면 보류함

## 11. 출처 정보 사용 원칙

- 기본 결론
- 출처는 학습용 입력 변수에서 제외함
- 이유
- 실제 서비스에서는 작품 1건 입력 시 Saatchi/Artsy/Artue 같은 수집 출처가 존재하지 않음
- 출처를 모델에 넣으면 출처별 가격대 차이를 외워서 성능이 좋아 보일 수 있음
- 이런 성능은 운영에서 재현할 수 없으므로 데이터 오염으로 판단함
- 허용되는 사용 범위
- 원본 row 추적
- 출처별 결측률 확인
- 출처별 가격/크기/재료 분포 확인
- 중복 처리 기준 확인
- 특정 출처의 크롤링 오류 탐지
- 금지되는 사용 범위
- 모델 입력 피처
- Warm / Cold 라우팅 기준
- 가격 보정 계수
- 최종 서비스 신뢰도 산정 기준

## 12. 첫 번째 작업 제안

- Track 4 첫 작업은 `T4-H1 temporal-safe Warm 피처 검증`으로 시작하는 것을 권장함
- 이유
- Track 3 Warm 최적 후보는 작가 이력/가격 통계 피처의 영향이 큼
- 이 피처가 예측 시점 이후 정보를 포함하면 운영에서 사용할 수 없음
- 이 문제가 닫혀야 Warm 모델을 운영 후보로 확정할 수 있음
