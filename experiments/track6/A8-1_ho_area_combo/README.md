# Track6 A8-1 호수 + 면적 조합 실험 결과

- 실험 목적: 호수와 면적을 함께 사용할 때 단일 크기 표현보다 가격 예측력이 개선되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `로그 호수 + 로그 면적 + 가로세로` / `Huber` / MdAPE `0.4936`
- Cold 최고: `로그 호수 + 로그 면적` / `Quantile-LAD` / MdAPE `0.4952`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A8-1_ho_area_combo/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A8-1_ho_area_combo/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 호수와 면적이 같은 크기 계열 변수이지만 서로 보완되는지 확인한다.
- 비교 기준: 호수만, 면적만, 호수+면적, 호수+가로세로 조합을 같은 고정 모델군에서 비교한다.
- 처리 기준: 모든 크기 피처는 숫자형으로 처리한다.
- 해석 기준: 조합 피처가 단독 피처보다 MdAPE와 p95 APE를 낮추면 크기 표현 조합을 유지 후보로 본다.
- 주의: 이 실험은 재료나 지지체를 포함하지 않고 크기 표현 내부의 중복/보완성만 확인한다.
- purpose: 호수와 면적을 함께 사용할 때 단일 크기 표현보다 가격 예측력이 개선되는지 확인
- summary: Warm 최고는 로그 호수 + 로그 면적 + 가로세로 + Huber(MdAPE 0.4936), Cold 최고는 로그 호수 + 로그 면적 + Quantile-LAD(MdAPE 0.4952)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
