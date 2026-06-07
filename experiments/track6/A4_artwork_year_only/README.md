# Track6 A4 제작연도만 실험 결과

- 실험 목적: 제작연도 정보만으로 가격 예측에 도움이 되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `제작연도 + 작품 연한` / `Huber` / MdAPE `0.7491`
- Cold 최고: `작품 연한` / `LightGBM` / MdAPE `0.7119`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A4_artwork_year_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A4_artwork_year_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 운영에서 입력 가능한 제작연도 정보만으로 가격 예측에 도움이 되는지 확인했다.
- 결과 요약: Warm/Cold 각각에서 MdAPE가 가장 낮은 제작연도 표현과 모델을 확인한다.
- 해석: 운영에서 알 수 없는 제작연도 출처와 결측 플래그는 제외하고, 제작연도 원값과 작품 연한만 비교한다.
- 결론: 제작연도 단독 채택 여부보다, 이후 작품 기본 피처 묶음에 넣을 때 도움이 되는지 확인하는 후보로 사용한다.
- 다음 실험: 작품 기본 피처 묶음에 제작연도 또는 작품 연한을 추가했을 때 추가 설명력이 있는지 확인한다.
- purpose: 제작연도 정보만으로 가격 예측에 도움이 되는지 확인
- summary: Warm 최고는 제작연도 + 작품 연한 + Huber(MdAPE 0.7491), Cold 최고는 작품 연한 + LightGBM(MdAPE 0.7119)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
