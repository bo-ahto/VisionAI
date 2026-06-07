# Track6 A7 에디션 정보 실험 결과

- 실험 목적: 에디션/유니크 구분이 작품 가격 예측에 도움이 되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `에디션 여부` / `Huber` / MdAPE `0.7457`
- Cold 최고: `에디션 여부` / `LightGBM` / MdAPE `0.7009`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A7_edition_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A7_edition_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 에디션 작품과 유니크 작품의 가격대 차이가 예측에 도움이 되는지 확인한다.
- 데이터 확인: Artsy의 attribution_class와 Saatchi의 attribution/is_edition 값을 원본에서 복원했다.
- 사용 피처: 모델에는 edition_class와 에디션 파생 플래그만 사용한다.
- 제외 피처: edition_source는 출처 정보라 모델 입력에서 제외한다. signed는 구조화 컬럼이 없어 A7에서 제외한다.
- 처리 기준: 에디션 관련 피처는 범주형 또는 플래그로 처리한다.
- 해석 기준: 같은 고정 모델군에서 MdAPE와 p95 APE가 낮아지면 에디션 정보가 가격 예측에 도움이 된다고 본다.
- 표본 수 주의: 전체 학습/테스트 수가 적은 것이 아니라, 에디션 작품 자체가 적다. train 에디션 613건, Warm test 에디션 33건, Cold test 에디션 232건이다.
- 결과 해석 방식: 전체 성능과 함께 edition/non-edition 및 edition_class별 slice 성능을 별도 파일로 확인한다.
- 주의: Warm test의 에디션 표본은 33건으로 많지 않아 Warm edition slice 결론은 보조적으로 해석한다.
- purpose: 에디션/유니크 구분이 작품 가격 예측에 도움이 되는지 확인
- summary: Warm 최고는 에디션 여부 + Huber(MdAPE 0.7457), Cold 최고는 에디션 여부 + LightGBM(MdAPE 0.7009)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
