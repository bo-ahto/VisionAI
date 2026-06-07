# T6-E049 작품 제목 키워드 피처 실험

- 상태: 예정
- 상위 일지: `T6-E038 작품 변수 선정 실험 일지`
- 가설 ID: `H11`
- 가설: 작품 제목에는 에디션, 세트, 포스터 등 가격 차이를 설명하는 정보가 있을 수 있다.
- 확인할 작품 피처: `title_raw`
- 테스트 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 기준 피처: Warm 기준: artist_name_ko + ln_estimated_ho / Cold 기준: ln_estimated_ho
- 추가 피처: Warm/Cold 추가: title_raw 기반 keyword flags
- 학습 정답값: `ln_price_krw`
- 비교 기준: 제목에서 edition/print/set/study/poster 등 키워드 flag 생성 후 비교
- 유의미함 기준: 전체 성능 또는 해당 키워드 slice 오차가 개선되면 후보 유지

## 초기 실험 데이터

- 기준 원천 파일: `data/track6/track6_feature_candidates_name_corrected.csv`
- 입력 피처와 정답 가격은 분리해서 생성
- Cold에서는 `artist_name_ko` 제외

## 결과 기록 파일

- `outputs/metrics.csv`
- `outputs/predictions.csv`
- `outputs/slice_metrics.csv`
- `outputs/summary.md`
- `logs/run.log`
