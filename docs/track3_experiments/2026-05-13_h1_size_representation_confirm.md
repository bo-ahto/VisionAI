# H1 크기 표현 대표화 재확인 기록

- 실험 ID: `H1_size_representation_confirm`
- 날짜: 2026-05-13
- 단계: 가설 종결 확인
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 결과 파일:
- `data/track3_pr20_size_redundancy_results.json`
- `data/track3_pr21_size_confirm_results.json`
- 기록 유형:
- 묶음 실험

## 1. 목적

- H1을 `검증 완료`로 정리할 수 있는지 확인
- 크기 정보를 여러 표현으로 모두 쓰는 방식과 대표 표현으로 줄이는 방식을 비교
- Warm / Cold 모두에서 대표 표현이 안정적인지 확인

## 2. 가설

- H1
- 크기 정보는 여러 원본 값을 모두 쓰기보다 대표 표현으로 정리하는 것이 더 안정적일 것이다

## 3. 사용 데이터

- 데이터 버전:
- `release_split regenerated on 2026-05-13`
- 학습 데이터:
- `data/release_split/track3_train.csv`
- 검증 데이터:
- `PR20`: train 내부 5-seed mini hold-out
- 최종 확인 데이터:
- `PR21`: `data/release_split/track3_test_warm.csv`
- `PR21`: `data/release_split/track3_test_cold.csv`
- 데이터 나누기 기준:
- mini 검증 후 release split confirm

## 4. 사용 변수

- 핵심 변수:
- `medium_category`
- `support_category`
- `orientation`
- `depth_cm`
- 크기 표현 후보:
- `width_cm`
- `height_cm`
- `log_area`
- `estimated_ho`
- 추가 변수:
- `aspect_ratio`
- `medium_ho_bucket`
- `artist_works_log`
- Warm 전용:
- `artist_name_ko`
- 제외 변수:
- `source_platform`

## 5. 사용 모델

- baseline:
- Cold: LAD
- Warm: tuned LightGBM
- variant:
- `V0_all`: `width_cm`, `height_cm`, `log_area`, `estimated_ho` 모두 사용
- `V1_log_ho`: `log_area`, `estimated_ho` 중심 대표 표현
- 기타 PR20 variants:
- `V2_log_only`
- `V3_wh_only`
- `V4_ho_only`
- 주요 설정값:
- PR20: 5-seed mini hold-out
- PR21: release split paired confirm

## 6. 변경된 요소

- 크기 정보 표현 방식
- 전체 크기 변수 유지 vs 대표 표현으로 축소

## 7. 성공 기준

- Warm:
- 대표 표현이 기존 `V0_all` 대비 악화되지 않아야 함
- Cold:
- 대표 표현이 기존 `V0_all` 대비 악화되지 않아야 함
- 보조 기준:
- 크게 틀리는 작품이 늘어나지 않아야 함
- Warm / Cold 중 한쪽이라도 뚜렷하게 악화되면 전면 채택하지 않음

## 8. 실행 내용

- 실행 스크립트:
- `scripts/track3/pr20_size_redundancy.py`
- `scripts/track3/pr21_size_v0_v1_confirm.py`
- 실행 일시:
- 2026-05-13
- 산출물:
- `data/track3_pr20_size_redundancy_results.json`
- `data/track3_pr21_size_confirm_results.json`

## 9. 결과

- 기록 원칙:
- `Warm 결과`, `Cold 결과`, `해석`, `결론`은 반드시 작성
- 숫자가 적더라도 핵심 지표는 남김

### Warm

- PR20 mini 5-seed
- `V0_all`: `median APE 0.2012 ± 0.0056`
- `V1_log_ho`: `median APE 0.2156 ± 0.0145`
- PR21 release confirm
- `V0_all`: `median APE 0.2055`
- `V1_log_ho`: `median APE 0.2277`
- 차이
- `V1_log_ho`가 `+0.0222` 악화
- `Within-30%`: `0.6053 -> 0.5852`
- `10x errors`: `137 -> 147`
- 판단
- Warm에서는 대표 표현으로 줄이면 성능이 명확히 나빠짐

### Cold

- PR20 mini 5-seed
- `V0_all`: `median APE 0.4743 ± 0.1029`
- `V1_log_ho`: `median APE 0.4736 ± 0.1048`
- PR21 release confirm
- `V0_all`: `median APE 0.3237`
- `V1_log_ho`: `median APE 0.3217`
- 차이
- `V1_log_ho`가 `-0.0021`로 아주 작게 개선
- `Within-30%`: `0.4609 -> 0.4617`
- `Within-50%`: `0.6832 -> 0.6819`
- `10x errors`: `522 -> 525`
- paired 비교
- `win_rate_variant`: `0.4677`
- `v1_acceptable`: `False`
- 판단
- Cold에서는 거의 비슷하지만, 전면 채택할 만큼 안정적인 우위는 아님

## 10. 해석

- 크기 정보는 `하나의 의미 축`으로 볼 수 있음
- 다만 실제 모델 입력에서는 `width_cm`, `height_cm`, `log_area`, `estimated_ho`를 모두 유지하는 쪽이 더 안전함
- `log_area + estimated_ho` 대표 표현은 Cold에서는 거의 비슷했지만 Warm에서 성능이 떨어짐
- Warm / Cold 중 한쪽이라도 뚜렷하게 악화되면 전면 채택하지 않는다는 기준에 따라 H1의 대표 표현 채택은 기각함
- 따라서 현재 운영 후보는 `V0_all` 유지가 맞음

## 11. 결론

- 채택 / 보류 / 중단:
- 중단
- 이유:
- 대표 표현 단순화는 Warm confirm에서 악화됨
- Cold에서도 전면 채택할 만큼 확실한 우위가 아님
- 최종 판단은 `V0_all` 유지
- 참고 상태:
- H1 검증 완료

## 12. 다음 액션

- H1은 추가 실험 없이 종결
- 크기 변수는 현재 기준으로 `V0_all` 유지
- 후속 실험은 H2 또는 H7/H8처럼 아직 부분 검증 상태인 가설로 이동
