# H12 작가 기본 가격대 + 작품별 잔차 모델 실험 기록

- 실험 ID: `H12_artist_residual_confirm`
- 날짜: 2026-05-13
- 단계: 후속 Warm 구조 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 결과 파일:
- `data/track3_h12_artist_residual_results.json`
- 실행 스크립트:
- `scripts/track3/h12_artist_residual_confirm.py`

## 1. 목적

- 작가의 기본 가격대와 작품별 편차를 분리하면 Warm 예측을 더 설명 가능하게 만들 수 있는지 확인
- H10에서 확인된 작가 이력 피처를 2단계 구조로 바꿔도 성능이 유지되는지 확인

## 2. 가설

- H12
- 작가 기본 가격대와 작품별 편차를 분리한 2단계 구조가 일부 Warm에서 설명력 있을 것이다

## 3. 사용 데이터

- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- train: `34,629`
- test warm: `1,685`

## 4. 사용 피처

- 작품 피처
- `medium_category`
- `support_category`
- `depth_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- `medium_ho_bucket`
- `aspect_ratio`
- 작가 이력 피처
- `artist_works_log`
- `artist_ln_price_median`
- `artist_ln_price_mean`
- `artist_ln_price_iqr`
- 직접 모델 추가 피처
- `artist_name_ko`

## 5. 연구 방법

- V0: 작가 중앙 가격만 사용
- V1: 작가명 + 작가 이력 + 작품 피처를 직접 학습
- V2: 작가 중앙 가격을 기본값으로 두고, 작품별 잔차만 별도 모델로 예측
- 작가 이력은 train split에서만 계산함
- 현재 데이터에는 거래일이 없어 temporal-safe 검증은 아직 아님

## 6. 결과

- V0 artist median only
- Warm median APE: `0.3660`
- Within-30%: `0.4534`
- V1 direct artist history model
- Warm median APE: `0.1204`
- Within-30%: `0.7496`
- V2 artist baseline + residual
- Warm median APE: `0.1228`
- Within-30%: `0.7472`

## 7. 해석

- 작가 중앙 가격만으로는 충분하지 않음
- 작품 정보와 작가 이력 피처를 함께 쓰면 성능이 크게 좋아짐
- 잔차 구조는 직접 모델과 거의 비슷한 성능을 냄
- 다만 최종 성능만 보면 직접 모델이 `0.1204`, 잔차 모델이 `0.1228`로 직접 모델이 약간 우세함
- 잔차 구조는 “작가 기본 가격대 + 작품별 가감 요인”으로 설명하기 쉬운 장점이 있음

## 8. 결론

- 채택 / 보류 / 중단:
- 보류
- 이유:
- 성능은 직접 모델과 거의 비슷하지만 직접 모델을 이기지는 못함
- 설명 가능성이 필요한 보고용 구조로는 가치가 있음
- 참고 상태:
- H12 검증 완료
- 운영 반영 전 temporal-safe 작가 기준가격 생성 필요

## 9. 다음 액션

- 최종 성능 모델은 H10의 직접 작가 이력 모델을 우선 후보로 둠
- 설명용 또는 보조 모델로 H12 잔차 구조를 유지 검토함
- 거래일 기준 작가 이력 계산이 가능해지면 H10/H12를 함께 재검증함
