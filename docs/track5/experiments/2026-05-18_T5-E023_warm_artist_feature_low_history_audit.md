# T5-E023 Warm 작가 피처 영향 및 저이력 구간 검증

- 날짜: 2026-05-18
- 관련 가설: T5-H26
- 목적: Warm 성능이 작가명 때문에만 좋아진 것인지, 저이력 작가에서도 유지되는지 확인
- 사용 데이터: `track5_train.csv`, `track5_test_warm.csv`
- 사용 스크립트: `scripts/track5/run_t5_e022_e025_audit_closure.py`
- 결과 파일: `data/track5/results/t5_e022_e025_audit_closure_metrics.json`

## 실험 방법

- 같은 Warm test에서 피처 구성을 단계별로 비교
- 비교 피처셋:
- `structure_only`: 재료, 지지체, 크기, 3D 여부만 사용
- `plus_artist_key`: 구조 피처에 작가 key 추가
- `plus_artist_history`: 작가 key와 작가 작품 수 추가
- `warm_full_size`: 작가 key, 작품 수, train 기준 작가 가격 통계 추가
- `no_artist_key_stats_only`: 작가 key 없이 작가 통계만 사용
- 작가별 train 작품 수 기준으로 `5개 이하`, `6~20개`, `20개 초과` 구간도 따로 확인

## 주요 결과

- 구조-only median APE: `0.4517`
- 작가 key 추가 median APE: `0.1601`
- 작가 key + 작품 수 median APE: `0.1612`
- full_size median APE: `0.1617`
- 작가 key 없이 통계만 사용 median APE: `0.3166`
- train 작품 수 5개 이하 구간의 full_size median APE: `0.1772`

## 해석

- Warm 성능 개선의 가장 큰 원인은 작가 식별 정보임
- 작가 통계만으로는 작가 key를 대체하지 못함
- 저이력 작가에서도 full_size median APE가 `0.1772`로 급격히 무너지지는 않음
- 다만 작가 key 의존이 크므로 운영에서는 작가명 매칭 품질이 중요함

## 결론

- 상태: 검증 완료
- Warm 모델은 작가 식별 정보를 쓰는 구조가 맞음
- 단, 작가명 매칭 실패 또는 동명이인 처리 실패 시 성능이 크게 떨어질 수 있으므로 운영 전처리 검증이 필수임
