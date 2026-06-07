# Track6 C4 작가명 + 제작연도 실험 결과

- 실험 목적: 작가명을 넣은 뒤에도 제작연도 또는 작품 연한이 가격 예측 성능을 추가로 개선하는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `작가명 + 제작연도` / `Huber` / MdAPE `0.4300`
- Cold 최고: `B1 기준: 작가명 only` / `LightGBM` / MdAPE `0.7018`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/C4_artist_name_plus_year/experiment_config.json`
- 사용 프롬프트: `experiments/track6/C4_artist_name_plus_year/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작가명만으로 설명되는 가격 효과를 기준으로 두고, 제작연도 관련 정보가 추가 예측력을 주는지 확인한다.
- 실험군: Group C: 작가명 + 작품 변수
- 기준선: B1 기준: artist_name_ko only
- 학습 피처: artist_name_ko에 artwork_year, artwork_age를 하나씩 또는 묶음으로 추가
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 숫자형 처리: artwork_year와 artwork_age는 숫자형으로 처리하고 StandardScaler를 적용한다.
- 제외 피처: 제작연도 출처, 결측 플래그, 보강 source 컬럼은 운영 입력값이 아니므로 사용하지 않는다.
- 해석 중심: C4는 작가명이 학습에 있는 Warm 상황에서 의미가 크므로 Warm 결과를 중심으로 판단한다.
- Cold 해석 주의: Cold는 신규 작가명이라 artist_name_ko가 학습에 없는 카테고리로 처리되므로 참고값으로만 본다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE를 확인한다.
- 결론 기준: B1 기준선보다 Warm MdAPE 또는 RMSE(log)가 낮아지고 p95 APE가 악화되지 않으면 제작연도 정보의 추가 설명력이 있다고 판단한다.
- purpose: 작가명을 넣은 뒤에도 제작연도 또는 작품 연한이 가격 예측 성능을 추가로 개선하는지 확인
- summary: Warm 최고는 작가명 + 제작연도 + Huber(MdAPE 0.4300), Cold 최고는 B1 기준: 작가명 only + LightGBM(MdAPE 0.7018)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
