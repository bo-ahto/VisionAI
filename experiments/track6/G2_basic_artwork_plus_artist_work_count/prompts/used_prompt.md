# G2 실험 프롬프트

- 실험 목적: 작품 조건을 통제한 후 작가별 데이터 보유량이 예측 안정성에 도움 되는지 확인
- 공통 실행기: `scripts/track6/fixed_variable_experiment_runner.py`
- split: `data/track6_split_with_year_type_edition_size_artist_name`
- sampling 없음, 전체 split 사용
- feature와 label은 `_track6_row_id` 기준으로 결합
- label은 학습 target과 평가 지표 계산에만 사용
- 가격/출처/URL 컬럼은 모델 입력 금지
- 숫자형 변수는 `numeric_features`로 명시하고 StandardScaler를 적용
- 범주형 변수는 OneHotEncoder(handle_unknown='ignore')로 처리

## 사용 피처
- 작품 기본 피처: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support` - 호수, 난트 재료, 난트 도구, 난트 지지체
- 작품 기본 피처 + 작가별 학습 작품 수: `ln_estimated_ho, nant_material_idx, nant_tool, nant_support, artist_works_log` - 작품 조건 통제 후 작가별 학습량 추가

## 모델
- Warm: Huber / Linear Regression / Ridge
- Cold: Huber / Quantile-LAD / LightGBM

## 평가 지표
- R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
