# H16 temporal-safe 작가 이력 피처 가능 여부 감사 기록

- 실험 ID: `H16_temporal_safe_feature_audit`
- 날짜: 2026-05-13
- 단계: 후속 재검증 사전 감사
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 실행 스크립트:
- `scripts/track3/h16_temporal_safe_feature_audit.py`
- 결과 파일:
- `data/track3_h16_temporal_safe_feature_audit.json`

## 1. 목적

- H10/H12의 작가 이력 피처를 운영 가능한 방식으로 다시 만들 수 있는지 확인
- 작가 이력 피처가 예측 시점 이후 정보를 쓰는지 검증하려면 거래일 또는 등록일이 필요함

## 2. 가설

- H16
- 작가 이력 피처는 거래일 기준으로 다시 계산할 수 있어야 운영 피처로 채택 가능하다

## 3. 사용 데이터

- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- `data/release_split/track3_test_cold.csv`

## 4. 점검 항목

- 거래일 후보 컬럼
- `sale_date`
- `sold_date`
- `transaction_date`
- `auction_date`
- `created_at`
- `registered_at`
- `listed_at`
- `year`
- `creation_year`
- 작가 이력 계산 필수 컬럼
- `artist_name_ko`
- `ln_price_krw_unified`
- `price_krw_unified`

## 5. 결과

- `track3_train.csv`
- 날짜 후보 컬럼: 없음
- 시간순 작가 이력 계산 가능 여부: `False`
- `track3_test_warm.csv`
- 날짜 후보 컬럼: 없음
- 시간순 작가 이력 계산 가능 여부: `False`
- `track3_test_cold.csv`
- 날짜 후보 컬럼: 없음
- 시간순 작가 이력 계산 가능 여부: `False`
- 최종 판단:
- `can_run=False`

## 6. 해석

- 현재 release split에는 거래일 또는 등록일 역할을 하는 컬럼이 없음
- 따라서 H10/H12의 작가 이력 피처를 temporal-safe 방식으로 재검증할 수 없음
- H10의 성능 개선은 강하지만, 운영 피처로 확정하려면 날짜 기준 이력 생성이 필요함

## 7. 결론

- 채택 / 보류 / 중단:
- 보류
- 이유:
- 날짜 컬럼이 없어 예측 시점 이전 정보만 사용했다는 검증이 불가능함
- 참고 상태:
- H16 감사 완료

## 8. 다음 액션

- 원천 데이터에 거래일, 판매일, 경매일, 등록일 중 하나를 추가할 수 있는지 확인
- 날짜 컬럼 확보 후 H10/H12를 temporal-safe 방식으로 재실험함
