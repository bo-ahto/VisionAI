# Track6 E5-2 국적별 가격 차이와 오차 차이 확인

- 학습 데이터: `26,914`건
- Warm 테스트: `607`건
- Cold 테스트: `3,099`건
- 기준 모델: `ln_estimated_ho + nant_material_idx + nant_tool + nant_support`
- 비교 모델: 기준 모델 + `artist_meta_nationality_norm + artist_meta_nationality_is_missing`
- 국적 처리: `South Korean`, `Korean`, `Korea`, `Republic of Korea` 등은 `Korea`로 정규화
- Warm 모델: `Huber`
- Cold 모델: `Quantile-LAD`
- 결과 HTML: `outputs/result_sheet.html`
- 국적별 요약 CSV: `outputs/nationality_group_summary.csv`
- 같은 조건 국적별 요약 CSV: `outputs/controlled_condition_nationality_summary.csv`

## 해석 기준

- `MdAPE_improvement`가 양수면 국적 추가 후 대표 오차가 줄어든 것이다.
- 국적별 표본 수가 작으면 참고용으로만 본다.
- 국적은 원인으로 단정하지 않고 후속 후보 피처로 판단한다.

## 결과 요약

- Cold 전체 MdAPE는 `0.5128`에서 `0.5000`으로 개선됐다.
- Cold p95_APE는 `3.2103`에서 `3.0305`로 개선됐다.
- Cold는 국적 정보가 큰 오차 완화에도 일부 도움이 됐다.
- Warm 전체 MdAPE는 `0.4962`에서 `0.4969`로 소폭 악화됐다.
- Warm p95_APE는 `2.9236`에서 `2.9013`으로 소폭 개선됐다.
- Warm은 대표 오차 기준으로 국적 추가 효과가 뚜렷하지 않다.
- 국적별로 보면 Cold의 `Korea` 그룹은 MdAPE가 `0.5312`에서 `0.5093`으로 개선됐다.
- 국적별로 보면 Warm의 `Korea` 그룹은 MdAPE가 `0.4624`에서 `0.4945`로 악화됐다.
- 결론적으로 국적 정보는 Cold 보조 피처 후보로는 유지할 수 있지만, Warm 핵심 피처로 채택하기에는 근거가 약하다.
