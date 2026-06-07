# Track6 A9-6 Warm/Cold 작품 피처 묶음 분리 실험 결과

- 실험 목적: Warm과 Cold에서 같은 작품 피처 묶음을 써도 되는지, 분리 후보가 필요한지 확인한다.
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `Warm 후보: 전체 크기 + 원문 재료 묶음 + NANT 지지체` / `Huber` / MdAPE `0.4277`
- Cold 최고: `Cold 후보: 로그면적 + 수집 재료 대분류 + 수집 지지체 대분류` / `Huber` / MdAPE `0.4795`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A9-6_warm_cold_feature_set_split/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A9-6_warm_cold_feature_set_split/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: Warm과 Cold에서 같은 작품 피처 묶음을 써도 되는지, 분리 후보가 필요한지 확인한다.
- 실험 위치: Group A의 A9 세부 실험 중 A9-6에 해당한다.
- 공통 실행 코드: scripts/track6/fixed_variable_experiment_runner.py
- 숫자형 처리: 숫자형 피처는 중앙값 결측 보정 후 StandardScaler를 적용한다.
- 범주형 처리: 범주형 피처는 one-hot encoding으로 처리한다.
- 판단 기준: Warm/Cold를 분리해 MdAPE, p95 APE, R2를 비교한다.
- 재현성 확인: 동일 설정으로 재실행해 주요 지표가 같은지 비교한다.
- purpose: Warm과 Cold에서 같은 작품 피처 묶음을 써도 되는지, 분리 후보가 필요한지 확인한다.
- summary: Warm 최고는 Warm 후보: 전체 크기 + 원문 재료 묶음 + NANT 지지체 + Huber(MdAPE 0.4277), Cold 최고는 Cold 후보: 로그면적 + 수집 재료 대분류 + 수집 지지체 대분류 + Huber(MdAPE 0.4795)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
