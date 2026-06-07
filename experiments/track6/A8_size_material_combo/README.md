# Track6 A8 크기 + 재료 조합 실험 결과

- 실험 목적: 크기 정보와 재료 정보를 함께 사용할 때 가격 예측력이 개선되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `로그면적 + NANT 재료 번호` / `Huber` / MdAPE `0.4764`
- Cold 최고: `로그면적 + 수집 재료 대분류` / `Huber` / MdAPE `0.4919`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A8_size_material_combo/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A8_size_material_combo/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 크기와 재료를 함께 썼을 때 크기만 또는 재료만 쓸 때보다 예측력이 좋아지는지 확인한다.
- 재료 비교 기준: NANT 재료 번호만 보지 않고 기존 수집 재료 대분류, NANT 재료 번호, NANT 도구명을 함께 비교한다.
- 크기 비교 기준: A1에서 유효했던 ln호, 로그면적, 가로/세로 실측값을 재료와 조합해 비교한다.
- 제외 피처: 지지체는 A9에서 별도 실험하므로 support_category와 nant_support는 제외한다.
- 처리 기준: 크기 피처는 숫자형으로 처리하고, 재료 피처는 범주형으로 처리한다.
- 해석 기준: 같은 고정 모델군에서 MdAPE와 p95 APE가 낮아지는 조합을 후보로 본다.
- 주의: A8은 조합 효과를 보는 실험이므로 최종 채택은 A9 이후 작품 기본 피처 묶음 실험에서 다시 확인한다.
- purpose: 크기 정보와 재료 정보를 함께 사용할 때 가격 예측력이 개선되는지 확인
- summary: Warm 최고는 로그면적 + NANT 재료 번호 + Huber(MdAPE 0.4764), Cold 최고는 로그면적 + 수집 재료 대분류 + Huber(MdAPE 0.4919)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
