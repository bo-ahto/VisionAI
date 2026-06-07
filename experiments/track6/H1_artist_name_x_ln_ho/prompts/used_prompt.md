# H1 실험 프롬프트

- 실험 목적: 같은 호수라도 작가명에 따라 가격대가 다른지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리
- 교차항은 설정 파일에 명시한 방식으로만 생성

## 사용 피처
- H1 기준: 작가명 + 호수: `artist_name_ko, ln_estimated_ho` - 작가명과 호수의 개별 효과만 사용
- H1 교차항: 작가명 x 호수: `artist_name_ko, ln_estimated_ho` - 작가별 호수 프리미엄 교차항 추가

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
