# Track6 A8-2 재료 표현 방식 + 크기 조합 실험 결과

- 실험 목적: 크기 기준을 고정한 뒤 재료 표현 방식별 가격 예측 성능 차이를 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `A8-1 Warm 크기조합 + 수집 재료 원문 묶음` / `Huber` / MdAPE `0.4432`
- Cold 최고: `로그면적 + 수집 재료 대분류` / `Huber` / MdAPE `0.4919`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A8-2_material_representation_size_combo/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A8-2_material_representation_size_combo/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 크기 기준을 고정한 상태에서 수집 재료 표현과 NANT 재료 표현 중 어떤 방식이 더 안정적인지 확인한다.
- 재료 비교 기준: 수집 재료 대분류, 수집 재료 원문 묶음, NANT 재료 번호, NANT 도구명, NANT 재료 번호+도구명을 비교한다.
- 재료 변수 설명: medium_category는 수집 데이터에서 정리한 재료 대분류이고, collected_material_raw_bucket은 수집 원문 재료명(collected_material_raw)을 학습 데이터 빈도 기준으로 묶은 변수다. collected_material_raw_bucket은 상위 80개 원문 재료명은 그대로 유지하고, 나머지 드문 원문 재료명은 other_raw_material로 합친다.
- 크기 비교 기준: 공통 기준인 로그면적과 A8-1에서 좋았던 Warm/Cold 크기 조합을 함께 사용한다.
- 제외 피처: 지지체는 A9에서 별도 실험하므로 support_category와 nant_support는 제외한다.
- 처리 기준: 크기 피처는 숫자형으로 처리하고, 재료 피처는 범주형으로 처리한다.
- 해석 기준: 같은 크기 기준 안에서 재료 표현만 바꿔 MdAPE와 p95 APE가 낮아지는 조합을 후보로 본다.
- 주의: A8-2는 재료 표현 방식 비교 실험이며, 지지체와 재료+지지체 조합은 후속 실험에서 별도로 판단한다.
- purpose: 크기 기준을 고정한 뒤 재료 표현 방식별 가격 예측 성능 차이를 확인
- summary: Warm 최고는 A8-1 Warm 크기조합 + 수집 재료 원문 묶음 + Huber(MdAPE 0.4432), Cold 최고는 로그면적 + 수집 재료 대분류 + Huber(MdAPE 0.4919)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
