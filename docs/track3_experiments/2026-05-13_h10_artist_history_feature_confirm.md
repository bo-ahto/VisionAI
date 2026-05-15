# H10 작가 이력 기반 Warm 피처 실험 기록

- 실험 ID: `H10_artist_history_feature_confirm`
- 날짜: 2026-05-13
- 단계: 후속 Warm 작가 피처 실험
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 결과 파일:
- `data/track3_h10_artist_history_feature_results.json`
- 실행 스크립트:
- `scripts/track3/h10_artist_history_feature_confirm.py`

## 1. 목적

- Warm 예측에서 `artist_name_ko` 자체보다 구조화된 작가 이력 피처가 더 안정적인지 확인
- 작가명을 그대로 외우는 방식보다 작가별 과거 가격대와 거래 수를 쓰는 방식이 설명 가능한지 확인

## 2. 가설

- H10
- 작가명보다 거래 이력 기반 구조화 피처가 Warm에서 더 안정적일 것이다

## 3. 사용 데이터

- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- train: `34,629`
- test warm: `1,685`
- train 작가 수: `1,932`
- warm test 작가 수: `1,685`

## 4. 사용 피처

- 공통 작품 피처
- `medium_category`
- `support_category`
- `depth_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- `medium_ho_bucket`
- `aspect_ratio`
- 작가명 피처
- `artist_name_ko`
- 작가 이력 피처
- `artist_works_log`
- `artist_ln_price_median`
- `artist_ln_price_mean`
- `artist_ln_price_iqr`

## 5. 연구 방법

- V0: 작품 피처 + `artist_name_ko`
- V1: 작품 피처 + 작가 이력 피처
- V2: 작품 피처 + `artist_name_ko` + 작가 이력 피처
- 작가 이력 피처는 train split 안에서만 계산함
- test warm의 가격 정보는 작가 이력 피처 계산에 사용하지 않음
- 단, 현재 데이터에는 거래일이 없어 시간순 이력 검증은 아직 불가능함

## 6. 결과

- V0 artist_name
- Warm median APE: `0.2289`
- Within-30%: `0.5757`
- V1 history only
- Warm median APE: `0.1257`
- 개선폭: `-0.1033`
- Within-30%: `0.7371`
- V2 artist_name + history
- Warm median APE: `0.1204`
- 개선폭: `-0.1085`
- Within-30%: `0.7496`

## 7. 해석

- 작가 이력 피처만 사용해도 작가명 단독보다 성능이 크게 좋음
- 작가명과 작가 이력 피처를 함께 쓰는 V2가 가장 좋음
- 작가별 기본 가격대가 Warm 예측에서 매우 강한 신호로 작동함
- 단, 운영 적용 전에는 거래일 기준으로 `예측 시점 이전 이력만 사용`하도록 재계산해야 함
- 현재 결과는 release split 기준 검증이며 temporal leakage 검증은 아님

## 8. 결론

- 채택 / 보류 / 중단:
- 채택
- 이유:
- Warm median APE가 `0.2289 -> 0.1204`로 크게 개선됨
- 작가명 자체보다 설명 가능한 작가 이력 피처의 가치가 큼
- 참고 상태:
- H10 검증 완료
- 운영 반영 전 temporal-safe 이력 생성 필요

## 9. 다음 액션

- 작품 거래일 또는 등록일 기준으로 작가 이력 피처를 재계산할 수 있는지 데이터 확인
- 최종 운영 피처 후보에 `artist_ln_price_median`, `artist_ln_price_mean`, `artist_ln_price_iqr`, `artist_works_log`를 추가 검토
- H12 residual 구조와 연결해 작가 기본 가격대와 작품별 편차를 분리하는 실험으로 확장
