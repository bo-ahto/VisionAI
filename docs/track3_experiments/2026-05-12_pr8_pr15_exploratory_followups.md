# 2026-05-12 PR8 ~ PR15 탐색 후속 기록

- 실험 ID: `PR8_PR15_exploratory_followups`
- 날짜: 2026-05-12
- 단계: 탐색 후속
- 상태: 종결
- 기록 유형:
- 묶음 실험
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 결과 파일:
- [`data/track3_pr8_conditional_results.json`](/Users/bo/VisionAI/data/track3_pr8_conditional_results.json)
- [`data/track3_pr9_quantile_results.json`](/Users/bo/VisionAI/data/track3_pr9_quantile_results.json)
- [`data/track3_pr11_depth_results.json`](/Users/bo/VisionAI/data/track3_pr11_depth_results.json)
- [`data/track3_pr13_homonym_results.json`](/Users/bo/VisionAI/data/track3_pr13_homonym_results.json)
- [`data/track3_pr14_exclude_results.json`](/Users/bo/VisionAI/data/track3_pr14_exclude_results.json)
- [`data/track3_pr15_depth_results.json`](/Users/bo/VisionAI/data/track3_pr15_depth_results.json)

## 1. 목적

- source conditional, quantile reweight, depth 표현, 동명이인 처리 등 후속 아이디어를 탐색

## 2. 연결 가설

- H2
- H4
- H6
- H7

## 3. 사용 데이터

- 데이터 버전:
- `track3 exploratory / pre-release split`
- 학습 데이터:
- Track 3 학습용 내부 데이터
- 검증 데이터:
- 내부 split 및 release split 일부 확인
- 최종 확인 데이터:
- `PR15`에서 release split 사용
- 데이터 나누기 기준:
- 탐색 단계 내부 split
- depth confirm은 release split

## 4. 사용 변수

- 핵심 변수:
- `medium_category`
- `support_category`
- `width_cm`
- `height_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- `depth_cm`
- 추가 변수:
- `has_depth`
- `source_platform`
- quantile/reweight용 weight 계열
- 동명이인 분리 규칙
- 제외 변수:
- 최종 운영 입력으로 불가능한 source 직접 활용은 운영 채택 제외

## 5. 사용 모델

- baseline:
- Cold LAD baseline
- variant:
- conditional expert
- quantile objective / sample reweight
- depth ablation
- homonym split / exclude
- 주요 설정값:
- depth 비교는 `none / has / cm / both`
- homonym 처리 비교는 `full split / conservative split / exclude`

## 6. 변경된 요소

- source conditional expert 적용
- quantile objective와 sample reweight 비교
- depth 표현 방식 비교
- 동명이인 작가 처리 방식 비교

## 7. 성공 기준

- Warm:
- conditional 또는 depth 조정이 Warm을 악화시키지 않을 것
- Cold:
- baseline 대비 median APE 개선
- 보조 기준:
- 운영 복잡도 증가 대비 개선 근거 확보

## 8. 실행 내용

- `pr8_conditional_expert.py`
- `pr9_quantile_reweight.py`
- `pr11_depth_ablation.py`
- `pr13_homonym_split.py`
- `pr14_homonym_exclude.py`
- `pr15_depth_ablation.py`
- 산출물:
- `data/track3_pr8_conditional_results.json`
- `data/track3_pr9_quantile_results.json`
- `data/track3_pr11_depth_results.json`
- `data/track3_pr13_homonym_results.json`
- `data/track3_pr14_exclude_results.json`
- `data/track3_pr15_depth_results.json`

## 9. 결과

### PR8 conditional expert

- baseline PR7 all
- `median_ape 0.3907`
- source conditional
- `0.4323`
- source × ho cell
- `0.4618`
- soft price band
- `0.4403`
- 해석
- source 기반 conditional expert는 baseline보다 악화
- 운영 입력 제약을 고려하면 더더욱 채택 근거 부족

### PR9 quantile / reweight

- baseline LAD
- `0.3907`
- LGB quantile
- `0.4192`
- + price weight
- `0.4312`
- + source weight
- `0.4285`
- + combined
- `0.4393`
- 해석
- quantile objective나 sample reweighting은 baseline LAD보다 일관되게 나쁨

### PR11 / PR15 depth 계열

- PR11
- `depth_cm only`가 `has_depth only`보다 낫고
- `both`가 가장 나은 방향 신호가 있었음
- PR15 release split 기준
- `D_none`
- Cold `0.3277`
- Warm `0.2291`
- `A_has`
- Cold `0.3177`
- Warm `0.2173`
- `B_cm`
- Cold `0.3207`
- Warm `0.2056`
- `C_both`
- Cold `0.2925`
- Warm `0.2056`
- 해석
- depth 정보는 빼는 것보다 유지하는 쪽이 유리
- 특히 `both`가 좋은 신호를 보여 이후 `PR17~PR19` depth / branch 후속 실험으로 이어짐

### PR13 / PR14 homonym 처리

- PR13
- homonym artist `38명`
- baseline `V1 median_ape 0.4066`
- full split `V2 0.4356`
- conservative split `V3 0.4374`
- 해석
- 동명이인 작가를 과하게 분리하면 오히려 성능 악화
- PR14
- 제외 작품 수 `1,596`
- full `V1 0.4066`
- exclude `V4_A 0.4299`
- paired `delta_median_ape +0.0022`
- 해석
- 동명이인 관련 작품을 제거하는 것도 성능 개선 근거가 없음

### Warm 요약

- 사용 변수 요약:
- 작품 기본 변수 + depth 변형 + source conditional 후보
- 핵심 결과:
- `PR15` 기준 `B_cm`, `C_both`가 Warm `0.2056`
- 해석:
- Warm에서는 depth 정보를 유지하는 것이 유리하고
- source conditional / quantile reweight / homonym 처리 개선안은 채택 근거 부족

### Cold 요약

- 사용 변수 요약:
- 작품 기본 변수 + depth 변형 + conditional / reweight / homonym 변형
- 핵심 결과:
- `PR15` 기준 `C_both`가 Cold `0.2925`로 가장 좋음
- 해석:
- depth 정보는 유지 가치가 있고, 나머지 탐색안은 운영 구조 개선으로 이어지지 않음

## 10. 해석

- source conditional, quantile reweight, homonym split/exclude는 일관되게 열세
- depth 정보는 제거보다 유지가 유리하고, 이후 branch 실험으로 이어질 근거를 제공
- 이 묶음에서 운영 가치가 남은 것은 사실상 depth 계열뿐임

## 11. 결론

- 상태:
- 종결
- 핵심 결론:
- source conditional, quantile reweight, homonym split/exclude는 채택 근거가 약함
- depth 정보는 유지 가치가 있어 이후 `PR17~PR19` 후속 실험으로 연결됨
- 채택 / 보류 / 중단:
- 보류
- 이유:
- depth 계열만 후속 가치가 남아 있고, 나머지 아이디어는 사실상 중단 판단
- 참고 상태:
- 종결

## 12. 다음 액션

- source / reweight 계열은 현 시점 기준 우선순위 낮음
- depth / branch 계열만 slice 보완 관점에서 후속 검증
