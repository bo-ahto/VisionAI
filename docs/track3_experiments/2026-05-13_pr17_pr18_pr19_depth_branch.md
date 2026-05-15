# PR17 / PR18 / PR19 기록

- 실험 ID: `PR17_PR18_PR19_depth_branch`
- 날짜: 2026-05-13
- 단계: 후속 개선 실험
- 상태: 종결
- 기록 유형:
- 묶음 실험
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 결과 파일:
- [`data/track3_pr17_branch_results.json`](/Users/bo/VisionAI/data/track3_pr17_branch_results.json)
- [`data/track3_pr18_matrix_results.json`](/Users/bo/VisionAI/data/track3_pr18_matrix_results.json)
- [`data/track3_pr19_cold_depth_signif.json`](/Users/bo/VisionAI/data/track3_pr19_cold_depth_signif.json)

## 1. 목적

- `source` 없이도 Cold 약점 구간을 보완할 수 있는지 확인
- `2D / 3D` 분기와 `depth` 표현이 실제 개선으로 이어지는지 검증

## 2. 가설

- `PR17`
- `2D / 3D` 분기로 Cold 성능을 줄일 수 있을 것이다
- `PR18`
- 분기 구조와 depth 표현 조합을 함께 조정하면 더 안정적인 후보를 찾을 수 있을 것이다
- `PR19`
- `depth_cm`를 제거하거나 단순화해도 성능 손실이 크지 않을 수 있다

## 3. 사용 데이터

- 데이터 버전:
- `release_split regenerated on 2026-05-13`
- 학습 데이터:
- `data/release_split/track3_train.csv`
- 검증 데이터:
- train 내부 mini hold-out
- 최종 확인 데이터:
- 없음
- 데이터 나누기 기준:
- train 내부 mini hold-out multi-seed

## 4. 사용 변수

- 핵심 변수:
- `medium_category`
- `support_category`
- `log_area`
- `estimated_ho`
- `orientation`
- `depth_cm`
- 추가 변수:
- `has_depth`
- `artist_works_log`
- `artist_works_log_branch`

## 5. 사용 모델

- Cold:
- LAD
- Warm:
- LightGBM
- 주요 설정값:
- 분기 구조 `V0 / V1 / V2 / V3`
- depth 표현 `cm_only / has_only / both`

## 6. 변경된 요소

- `PR17`
- Warm / Cold 각각의 `2D / 3D` 분기 여부
- `PR18`
- `cm_only`, `has_only`, `both`
- `PR19`
- `depth_cm` 유지 vs 제거 방향 검정

## 7. 성공 기준

- Warm:
- 기존 대비 악화가 없어야 함
- Cold:
- median APE 개선이 반복되어야 함
- 보조 기준:
- slice 기준 개선이 특정 구간에만 과도하게 치우치지 않아야 함

## 8. 실행 내용

- 실행 스크립트:
- `scripts/track3/pr17_branch_models.py`
- `scripts/track3/pr18_branch_depth_matrix.py`
- `scripts/track3/pr19_cold_depth_signif.py`
- 산출물:
- `data/track3_pr17_branch_results.json`
- `data/track3_pr18_matrix_results.json`
- `data/track3_pr19_cold_depth_signif.json`

## 9. 결과

### Warm

- 사용 변수 요약:
- 기본 작품 변수 + depth 변형 + branch variant
- `PR17`
- `V0 0.2036`
- `V1 / V3 0.2022`
- `PR18`
- `V2_cm_only 0.2071 ± 0.0089`
- Warm 전반 개선 근거 약함

### Cold

- 사용 변수 요약:
- 기본 작품 변수 + depth 변형 + `2D / 3D` branch variant
- `PR17`
- `V0 0.4448`
- `V2 / V3 0.4141`
- `PR18`
- 기준 `V0_cm_only 0.4770 ± 0.1038`
- 후보 `V2_cm_only 0.4636 ± 0.0904`
- `PR19`
- overall 기준 `depth_cm` 제거 근거 없음

## 10. 해석

- `Cold 2D`는 반복적으로 개선 가능성이 보임
- `Cold 3D`는 개선이 약하거나 악화
- `Warm`은 전반적으로 유지 또는 미세 악화
- `depth_cm`를 전역 제거하는 방향은 맞지 않음

## 11. 결론

- 채택 / 보류 / 중단:
- 중단
- 이유:
- 전면 채택할 만큼 일관된 개선은 아님
- `Cold 2D` 한정 fallback 후보 정도로만 가치가 있음
- 이후 H8 release split fallback 실험에서 전체 Cold와 Cold 2D 모두 악화되어 최종 중단함
- 참고 상태:
- H8에서 후속 검증 완료

## 12. 다음 액션

- 추가 액션 없음
- H8 결과에 따라 2D / 3D 분기와 Cold 2D fallback은 운영 후보에서 제외함
