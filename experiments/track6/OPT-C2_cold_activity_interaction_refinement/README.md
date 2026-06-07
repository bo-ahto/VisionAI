# Track6 OPT-C2 Cold 활동량/인지도 상호작용 최적화 실험

- 실험 목적: A~J 실험에서 Cold 성능이 좋았던 작품 기본 피처, 활동량/인지도, 면적/호수 상호작용을 결합해 신규 작가 예측 성능의 최대치를 확인한다.
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `C2-6: C2-5 + 기본 작가 프로필/전시` / `Huber` / MdAPE `0.3096`
- Cold 최고: `C2-4: C2-2 + 활동량/인지도 x 호수` / `LightGBM` / MdAPE `0.4579`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/OPT-C2_cold_activity_interaction_refinement/experiment_config.json`
- 사용 프롬프트: `experiments/track6/OPT-C2_cold_activity_interaction_refinement/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: A~J 결과 기반 Cold 최고 피처/모델 후보를 좁힌다.
- 해석 중심: Cold MdAPE를 1순위로 보되 p95 APE가 크게 커지면 운영 후보에서 제외한다.
- 비교 기준: 기존 최고권인 G6/J4/J5 계열을 결합해 추가 개선 가능성을 확인한다.
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 공통 실행 코드: scripts/track6/fixed_variable_experiment_runner.py
- purpose: A~J 실험에서 Cold 성능이 좋았던 작품 기본 피처, 활동량/인지도, 면적/호수 상호작용을 결합해 신규 작가 예측 성능의 최대치를 확인한다.
- summary: Warm 최고는 C2-6: C2-5 + 기본 작가 프로필/전시 + Huber(MdAPE 0.3096), Cold 최고는 C2-4: C2-2 + 활동량/인지도 x 호수 + LightGBM(MdAPE 0.4579)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
