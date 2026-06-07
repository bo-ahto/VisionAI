# OPT-W3 Warm 핵심 후보 피처/모델 최종 축소 실험 프롬프트

- 목적: Warm 최고권 조합인 `작가명 + 전체 크기`를 기준으로 핵심 추가 조합만 비교한다.
- 원본 OPT-W2/OPT-W2L은 작가 상호작용과 전체 메타 조합에서 계산 비용이 과도했으므로, 상위 10명 작가 상호작용과 작가 학습량만 우선 검증한다.
- 데이터: `data/track6_split_with_year_type_edition_size_artist_name` 고정 split 전체 사용.
- 학습/평가 연결 키: `_track6_row_id`.
- 라벨은 학습 target 및 평가 지표 계산에만 사용한다.
- 공통 코드: `scripts/track6/fixed_variable_experiment_runner.py`.
- 숫자형 피처는 중앙값 결측 보정 후 `StandardScaler`를 적용한다.
- 주요 판단 지표: Warm `MdAPE`, 보조 지표 `p95_APE`, `Within_30`, `RMSE_log`, `R2`.
