# OPT-C1 Cold 최적 피처 조합 후보 실험 지시

- 목적: A1-D11 결과에서 Cold 성능이 좋았던 작품 변수 조합을 같은 split, 같은 공통 실행기로 다시 비교한다.
- 핵심 질문: 신규 작가 상황에서 작가명 없이 어떤 작품 피처 조합을 사용할 때 예측 정확도가 가장 높아지는가?
- 사용 데이터:
  - `data/track6_split_with_year_type_edition_size_artist_name`
- 사용 모델:
  - Warm: Huber, Linear Regression, Ridge
  - Cold: Huber, Quantile-LAD, LightGBM
- 판단 기준:
  - 1순위: Cold MdAPE
  - 2순위: Cold p95 APE
  - 3순위: Cold Within-30
- 주의:
  - Cold 운영을 가정하므로 `artist_name_ko`는 사용하지 않는다.
  - 숫자형 피처는 numeric feature로 처리하고 StandardScaler를 적용한다.
  - label은 학습 target 및 metric 계산에만 사용한다.
