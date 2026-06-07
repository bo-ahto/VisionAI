# Track6 A5 작품 유형만 실험 결과

- 실험 목적: 회화·판화·조각 등 작품 유형 정보만으로 가격 예측에 도움이 되는지 확인
- 학습 데이터 건수: `26,914`건
- Warm 테스트 건수: `607`건
- Cold 테스트 건수: `3,099`건
- Warm 최고: `유형 보완 전체 구분` / `Ridge` / MdAPE `0.7396`
- Cold 최고: `작품 유형 전체 구분` / `LightGBM` / MdAPE `0.6729`
- 사용 코드: `scripts/track6/fixed_variable_experiment_runner.py`
- 사용 설정: `experiments/track6/A5_artwork_type_only/experiment_config.json`
- 사용 프롬프트: `experiments/track6/A5_artwork_type_only/prompts/used_prompt.md`
- 복사한 원본 데이터 폴더: `source_data/`

## 코멘트

- 실험 목적: 작품 유형만으로 회화·판화·조각 차이가 가격 예측에 의미가 있는지 확인한다.
- 데이터 확인: 최신 Track6 피처에는 직접 유형 컬럼이 없어 원본 Artsy/Saatchi 유형값과 URL 패턴으로 artwork_type을 복원했다.
- 운영 기준: 모델 입력에는 artwork_type 계열 최종 구분값만 사용하고, 출처/매칭방법/원문값은 학습 피처에서 제외한다.
- 유형 보완: 원본 유형이 unknown인 경우 재료, 지지체, NANT 도구 값을 사용해 artwork_type_final을 만든 뒤 원본 unknown 유지 실험과 비교한다.
- 해석 기준: 같은 고정 모델군에서 MdAPE와 p95 APE가 낮아지면 작품 유형 정보가 가격대 구분에 도움이 된다고 본다.
- 주의: Warm test의 판화/조각 표본은 작아서 세부 유형별 결론은 보조적으로만 해석한다.
- purpose: 회화·판화·조각 등 작품 유형 정보만으로 가격 예측에 도움이 되는지 확인
- summary: Warm 최고는 유형 보완 전체 구분 + Ridge(MdAPE 0.7396), Cold 최고는 작품 유형 전체 구분 + LightGBM(MdAPE 0.6729)이다.

## 결과 파일

- `outputs/result_sheet.html`
- `outputs/result_sheet.csv`
- `outputs/metrics_long.csv`
- `outputs/experiment_manifest.json`
