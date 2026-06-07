# Track6 E6 작가 활동량/판매 노출량 단독 실험 결과

- 실험 목적: 등록 작품 수와 판매 중 작품 수가 가격 예측에 도움 되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `활동량 + 판매 노출량 + 결측` / `Linear Regression` / MdAPE `0.7263`
- Cold 최고: `활동량 + 판매 노출량 + 결측` / `Quantile-LAD` / MdAPE `0.6961`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/E6_artist_activity_sale_exposure_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/E6_artist_activity_sale_exposure_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 등록 작품 수와 판매 중 작품 수가 가격 예측에 도움 되는지 확인
- 학습 피처: artist_meta_total_works / artist_meta_for_sale_works / artist_meta_total_works, artist_meta_for_sale_works, artist_meta_total_works_is_missing, artist_meta_for_sale_works_is_missing
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group E: 작가 변수만
- 해석 중심: 작가의 시장 노출량이 가격대 예측에 도움 되는지 확인한다.
- 주의: 플랫폼별 수집 시점 차이가 있으므로 성능이 좋아도 운영 재현성을 별도로 확인한다.
- purpose: 등록 작품 수와 판매 중 작품 수가 가격 예측에 도움 되는지 확인
- summary: Warm 최고는 활동량 + 판매 노출량 + 결측 + Linear Regression(MdAPE 0.7263), Cold 최고는 활동량 + 판매 노출량 + 결측 + Quantile-LAD(MdAPE 0.6961)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
