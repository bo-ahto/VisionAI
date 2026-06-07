# Track6 C9 C8 + 깊이/입체성 정보 실험 결과

- 실험 목적: C8 누적 피처에 깊이와 입체성 정보를 추가했을 때 가격 예측 성능이 개선되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `C8 + 깊이 존재 여부` / `Huber` / MdAPE `0.1852`
- Cold 최고: `C8 + 깊이 존재 여부` / `LightGBM` / MdAPE `0.4745`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/C9_c8_plus_depth/experiment_config.json`
- 사용 프롬프트: `experiments/track6/C9_c8_plus_depth/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: C8 누적 피처를 기준으로 깊이와 입체성 정보가 추가 예측력을 주는지 확인한다.
- 실험군: Group C: 작가명 + 작품 변수 누적
- 기준선: C8 기준: artist_name_ko + 작품 기본 피처 묶음 + artwork_year/artwork_age + artwork_type
- 학습 피처: C8 기준 피처에 depth_cm, has_depth, is_3d_candidate를 하나씩 또는 묶음으로 추가
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 전처리: depth_cm은 숫자형으로 처리하고 StandardScaler를 적용한다. has_depth와 is_3d_candidate는 범주형으로 처리한다.
- 해석 중심: C9는 작가명이 학습에 있는 Warm 상황에서 의미가 크므로 Warm 결과를 중심으로 판단한다.
- Cold 해석 주의: Cold는 신규 작가명이라 artist_name_ko가 학습에 없는 카테고리로 처리되므로 참고값으로만 본다.
- 표본 주의: is_3d_candidate는 표본이 작아 전체 성능보다 3D slice 해석이 중요할 수 있다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE를 확인한다.
- 결론 기준: C8 기준선보다 Warm MdAPE 또는 RMSE(log)가 낮아지고 p95 APE가 악화되지 않으면 깊이/입체성 정보의 추가 설명력이 있다고 판단한다.
- purpose: C8 누적 피처에 깊이와 입체성 정보를 추가했을 때 가격 예측 성능이 개선되는지 확인
- summary: Warm 최고는 C8 + 깊이 존재 여부 + Huber(MdAPE 0.1852), Cold 최고는 C8 + 깊이 존재 여부 + LightGBM(MdAPE 0.4745)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
