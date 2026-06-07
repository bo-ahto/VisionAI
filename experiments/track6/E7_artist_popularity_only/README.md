# Track6 E7 작가 인지도 단독 실험 결과

- 실험 목적: 팔로워 수와 주요 작가 여부가 가격 예측에 도움 되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `인지도 묶음 + 결측` / `Huber` / MdAPE `0.7441`
- Cold 최고: `주요 작가 여부` / `LightGBM` / MdAPE `0.7028`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/E7_artist_popularity_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/E7_artist_popularity_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 팔로워 수와 주요 작가 여부가 가격 예측에 도움 되는지 확인
- 학습 피처: artist_meta_followers / artist_meta_is_p1 / artist_meta_followers, artist_meta_is_p1, artist_meta_followers_is_missing, artist_meta_is_p1_is_missing
- 테스트 피처: 학습 피처와 동일
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 데이터 기준: 작가 메타가 보강된 최신 Track6 split. label은 _track6_row_id로만 결합한다.
- 평가 지표: R2, RMSE(log), MdAPE, p95 APE, Within-30, Within-50, MAPE
- 실험군: Group E: 작가 변수만
- 해석 중심: 플랫폼 인지도 정보가 가격대 예측에 도움 되는지 확인한다.
- 주의: 네이버 검색량은 현재 데이터셋에 없으므로 이번 실험에서는 제외한다.
- purpose: 팔로워 수와 주요 작가 여부가 가격 예측에 도움 되는지 확인
- summary: Warm 최고는 인지도 묶음 + 결측 + Huber(MdAPE 0.7441), Cold 최고는 주요 작가 여부 + LightGBM(MdAPE 0.7028)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
