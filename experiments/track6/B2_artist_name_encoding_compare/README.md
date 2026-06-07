# Track6 B2 작가명 처리 방식 비교 실험 결과

- 실험 목적: 같은 작가명 변수를 모델에 넣는 방식에 따라 Warm 가격 예측 성능이 달라지는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `one_hot` / `Huber` / MdAPE `0.4352` / RMSE(log) `0.8483`
- Cold 최고: `smoothed_target_mean_log` / `LightGBM` / MdAPE `0.7016` / RMSE(log) `1.3166`
- 사용 코드: `experiments/track6/B2_artist_name_encoding_compare/scripts/run_experiment.py`
- 사용 설정: `experiments/track6/B2_artist_name_encoding_compare/experiment_config.json`
- 사용 프롬프트: `experiments/track6/B2_artist_name_encoding_compare/prompts/used_prompt.md`

## 주의

- target encoding 계열은 train label만 사용해 계산했다.
- Warm 결과를 중심으로 판단한다.
- Cold 결과는 신규 작가명 상황의 한계 확인용 참고값이다.
