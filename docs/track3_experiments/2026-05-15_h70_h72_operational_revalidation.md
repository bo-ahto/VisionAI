# H70-H72 운영 전 재검증

- 날짜: 2026-05-15
- 실험 ID: `H70_H72_operational_revalidation`
- 목적: 2026-05-15 코드 감사에서 확인된 재검증 필요 지점을 운영 기준에 맞게 다시 확인
- 결과 파일: `data/track3_h70_h72_operational_revalidation_results.json`

## 재검증 대상

| ID | 재검증 질문 | 기존 문제 |
|---|---|---|
| H70 | 가격 범위 calibration을 test residual이 아니라 내부 calibration split으로 계산해도 유지되는가 | H69는 test residual 기반이라 운영 과적합 위험이 있음 |
| H71 | Cold 3D 중간 부피 예외를 cold test quantile이 아니라 train 기준 threshold로 정해도 유효한가 | H45/H49의 중간 부피 기준이 test 분포에서 계산됨 |
| H72 | H60 medium/support 조합 정리는 `min_count` grid에서도 여전히 미채택이 맞는가 | 기존 H60은 `min_count=100`만 확인 |

## 사용 데이터

| 구분 | 파일 | 행 수 |
|---|---|---:|
| 학습 | `track3_train.csv` | 34,629 |
| Warm 평가 | `track3_test_warm.csv` | 1,685 |
| Cold 평가 | `track3_test_cold.csv` | 3,823 |

## H70 가격 범위 Calibration

- Warm calibration 방식
- `track3_train.csv` 안에서 작가별로 1개 작품을 calibration으로 분리
- 나머지 train core로 Warm 모델 학습
- calibration residual로 등급별 80% 가격 범위 폭 계산
- 최종 full train 모델의 Warm test 예측에 이 폭을 적용해 coverage 확인

- Cold calibration 방식
- `track3_train.csv` 안에서 작가 200명을 통째로 holdout
- 남은 작가로 Cold 모델 학습
- holdout 작가를 내부 Cold calibration set으로 사용
- calibration residual로 Cold 조건별 80% 가격 범위 폭 계산
- 최종 full train Cold 모델의 Cold test 예측에 이 폭을 적용해 coverage 확인

### H70 Warm 결과

| 구간 | calibration 가격 배수 | test coverage | 해석 |
|---|---:|---:|---|
| 전체 | x1.52 | 0.821 | 목표 80% 충족 |
| A: 51건 이상 | x1.26 | 0.813 | 좁은 범위로도 충분 |
| B: 11-50건 | x1.31 | 0.826 | 좁은 범위로도 충분 |
| C: 4-10건 | x1.59 | 0.841 | 중간 범위 필요 |
| D: 1-3건 | x1.94 | 0.794 | 목표에 거의 근접, 넓은 범위와 신뢰도 경고 유지 |

### H70 Cold 결과

| 구간 | calibration 가격 배수 | test coverage | 해석 |
|---|---:|---:|---|
| 전체 | x2.27 | 0.855 | 목표 80% 초과 |
| 표준 3D | x2.06 | 0.887 | 안정적 |
| 표준 2D | x2.42 | 0.783 | 목표보다 약간 낮음, 넓은 범위 유지 |
| 대형/초대형 high-risk | x2.88 | 0.794 | 목표 근접, 넓은 범위 필요 |
| 대형 호수 | x3.11 | 0.826 | 넓은 범위 필요 |
| 초대형 호수 | x3.11 | 0.876 | 넓은 범위 필요 |
| 초대형 면적 | x2.88 | 0.794 | 목표 근접, 넓은 범위 필요 |

### H70 판단

- 내부 calibration split으로도 Warm/Cold 조건별 가격 범위 정책은 대체로 유지됨
- H69의 test residual 기반 결론은 방향성은 맞았음
- 다만 운영 최종 확정 전에는 calibration split을 고정하고 재학습 pipeline에 포함해야 함

## H71 Cold 3D 중간 부피 예외 재검증

- 기존 문제
- H45/H49는 Cold test 3D 작품의 `volume_log` quantile로 중간 부피 구간을 정함
- 운영에서는 test 분포를 미리 알 수 없으므로 부적절함

- 재검증 방식
- train 3D 작품의 `volume_log` 33%, 66% 지점으로 중간 부피 기준 설정
- 기준값: `q33 = 7.9014`, `q66 = 9.4846`
- 이 기준으로 Cold test의 중간 3D 작품 785건을 판별
- 해당 구간에만 3D fallback 대신 기본 Cold 모델을 적용

### H71 결과

| 비교 | 전체 Cold median APE | 전체 Cold p95 APE | 중간 3D median APE | 중간 3D p95 APE |
|---|---:|---:|---:|---:|
| H32 기본 | 0.2786 | 1.4860 | 0.2488 | 1.0778 |
| train 기준 중간 3D 예외 | 0.2798 | 1.6192 | 0.2414 | 1.6086 |

### H71 판단

- 중간 3D 구간 median APE는 `0.2488 -> 0.2414`로 조금 좋아짐
- 하지만 전체 Cold median APE는 `0.2786 -> 0.2798`로 악화됨
- 전체 p95 APE는 `1.4860 -> 1.6192`로 악화됨
- 중간 3D p95 APE도 `1.0778 -> 1.6086`로 크게 악화됨
- 결론: Cold 3D 중간 부피 예외는 미채택
- 운영 후보는 H32 조건부 fallback 유지

## H72 H60 조합 피처 Grid 재검증

- 기존 문제
- H60은 `medium_category + support_category` 조합 정리를 `min_count=100`만 확인함
- 조합 정리 기준을 바꾸면 결과가 달라질 수 있음

- 재검증 방식
- `min_count = 20 / 50 / 100 / 200 / 500` 비교
- 각 기준에서 희소 조합은 `other_combo`로 묶음
- Cold base + 3D fallback 구조로 H32와 비교

### H72 결과

| min_count | train 조합 수 | Cold median APE | Cold p95 APE | H32 대비 판단 |
|---:|---:|---:|---:|---|
| H32 기준 | - | 0.2786 | 1.4860 | 기준 |
| 20 | 44 | 0.2802 | 1.4637 | median 악화 |
| 50 | 36 | 0.2802 | 1.4639 | median 악화 |
| 100 | 32 | 0.2803 | 1.4635 | median 악화 |
| 200 | 23 | 0.2793 | 1.4488 | median 악화 |
| 500 | 13 | 0.2792 | 1.4489 | median 악화 |

### H72 판단

- 모든 `min_count` 기준에서 H32보다 median APE가 나빠짐
- p95 APE는 일부 개선되지만 핵심 지표인 median APE가 악화됨
- 결론: medium/support 조합 정리 피처는 미채택
- H60 기각 판단 유지

## 최종 결론

| 항목 | 결론 |
|---|---|
| H70 | 내부 calibration 기준에서도 가격 범위 정책 방향은 유지 가능 |
| H71 | Cold 3D 중간 부피 예외는 train 기준으로도 tail risk가 커져 미채택 |
| H72 | medium/support 조합 정리는 grid 재검증 후에도 미채택 |

## 다음 조치

- H69/H70 기준으로 가격 범위 정책은 “조건별 범위 제공” 방향 유지
- H32 Cold 3D 조건부 fallback은 유지
- H45/H49의 중간 부피 예외 후보는 중단
- H60 조합 정리 피처는 중단
- H16 temporal-safe 작가 이력 검증은 날짜 컬럼 확보 전까지 보류 유지
