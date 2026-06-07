# D8 artist_name x log_area 숫자형 교차항 실험 프롬프트

- 실험 목적: 작가별로 대형 작품 프리미엄이 달라지는지 확인한다.
- 실험 변수: `artist_name_ko`, `log_area`
- 교차항 처리: `log_area`를 문자열로 바꾸지 않고 숫자형으로 유지한다.
- 교차항 생성: 학습 데이터 작품 수 상위 작가에 대해 `log_area * 해당 작가 여부` 숫자형 컬럼을 만든다.
- 비교 기준: `artist_name_ko + log_area` 기준 모델과 `artist_name_ko + log_area + 숫자형 교차항` 모델을 비교한다.
- 해석 중심: Warm 결과를 중심으로 판단하고 Cold 결과는 참고값으로만 둔다.
- 모델: Warm은 Huber / Linear Regression / Ridge, Cold는 Huber / Quantile-LAD / LightGBM을 사용한다.
- 데이터: Track6 고정 split 전체를 사용하고 샘플링하지 않는다.
- 라벨 사용: label은 학습 target과 평가 지표 계산에만 사용한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE.
