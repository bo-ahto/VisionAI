# G10 실험 프롬프트

- 실험 목적: 학습 작품 수가 적은 Warm 작가에서 Warm 작가명 모델과 Cold 방식 모델 중 어느 쪽이 안정적인지 확인한다.
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- label은 `_track6_row_id` 기준으로만 결합하고, 모델 입력에는 사용하지 않는다.
- Warm 전략 모델: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_name_ko, artist_works_log`
- Cold 방식 모델: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support`
- Warm test를 `artist_works_count_train` 구간별로 나누어 MdAPE, p95 APE, Within-30/50을 비교한다.
- 공식 Warm test는 Stable Warm 기준이므로 5개 미만 구간이 없으면 그 한계를 결과에 명시한다.
