# Track6 OPT-W3 Warm 핵심 후보 피처/모델 최종 축소 실험

- 실험 목적: A~J 및 OPT-W1 결과에서 Warm 최고권이었던 작가명+전체 크기 조합을 기준으로 계산 가능한 핵심 추가 조합만 비교한다.
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `W3-2: W3-1 + 작가명 x 면적` / `Huber` / MdAPE `0.1548`
- Cold 최고: `W3-3: W3-1 + 작가명 x 호수` / `LightGBM` / MdAPE `0.5073`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/OPT-W3_warm_compact_final_refinement/experiment_config.json`
- 사용 프롬프트: `experiments/track6/OPT-W3_warm_compact_final_refinement/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: Warm 최고 피처/모델 후보를 계산 가능한 범위에서 최종 축소 비교한다.
- 해석 중심: Warm MdAPE 1순위, p95 APE와 RMSE_log 보조 확인.
- 비교 기준: 기존 최고권인 작가명 + 전체 크기 조합을 기준으로 핵심 추가 피처의 개선 여부를 판단한다.
- 사용 모델: Warm: Huber / Linear Regression / Ridge, Cold: Huber / Quantile-LAD / LightGBM
- 공통 실행 코드: scripts/track6/fixed_variable_experiment_runner.py
- purpose: A~J 및 OPT-W1 결과에서 Warm 최고권이었던 작가명+전체 크기 조합을 기준으로 계산 가능한 핵심 추가 조합만 비교한다.
- summary: Warm 최고는 W3-2: W3-1 + 작가명 x 면적 + Huber(MdAPE 0.1548), Cold 최고는 W3-3: W3-1 + 작가명 x 호수 + LightGBM(MdAPE 0.5073)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
