# Track6 A3 지지체만 실험 결과

- 실험 목적: 지지체 정보만으로 가격 예측에 도움이 되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `수집 지지체 대분류` / `Huber` / MdAPE `0.7317`
- Cold 최고: `수집 지지체 대분류 + NANT 지지체` / `LightGBM` / MdAPE `0.6843`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A3_support_only_collected_vs_nant/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A3_support_only_collected_vs_nant/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 지지체 정보만으로 가격 예측에 도움이 되는지, 수집 지지체 표현과 NANT 지지체 표현 중 어느 쪽이 더 안정적인지 확인했다.
- 결과 요약: Warm/Cold 각각에서 MdAPE가 가장 낮은 지지체 표현과 모델을 확인한다.
- 해석: 지지체만 사용한 경우 단독 예측력이 있는지, NANT 지지체가 수집 지지체 대분류보다 안정적인지 비교한다.
- 결론: 지지체 단독 피처로 최종 모델을 만들 수 있는지보다, 이후 크기/재료/작가명 조합에 넣을 지지체 표현 후보를 고르는 데 사용한다.
- 다음 실험: 크기 + NANT 지지체, 작가명 + NANT 지지체 조합에서 지지체가 추가 설명력을 갖는지 확인한다.
- purpose: 지지체 정보만으로 가격 예측에 도움이 되는지 확인
- summary: Warm 최고는 수집 지지체 대분류 + Huber(MdAPE 0.7317), Cold 최고는 수집 지지체 대분류 + NANT 지지체 + LightGBM(MdAPE 0.6843)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
