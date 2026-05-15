# Track 3 현재 의사결정 요약

- 목적: 지금까지의 실험 결과를 기준으로 현재 운영 후보, 채택/미채택 판단, 남은 리스크를 한 장으로 정리
- 기준일: 2026-05-15
- 기준 데이터:
- `data/release_split/track3_train.csv`
- `data/release_split/track3_test_warm.csv`
- `data/release_split/track3_test_cold.csv`

## 1. 현재 운영 후보

| 구분 | 현재 후보 | 핵심 성능 | 판단 |
|---|---|---:|---|
| Warm | H66 larger-low-lr LightGBM | mean median APE `0.1051` | 현재 Warm 최우선 후보 |
| Cold | H32 조건부 fallback | median APE `0.2786` | 현재 Cold 최우선 후보 |
| Cold 3D | H32 3D 전용 피처 모델 조건부 적용 | Cold 3D 개선 | 3D 작품에만 적용 |
| 가격 범위 | H70 내부 calibration 기반 조건별 범위 | Warm coverage `0.821`, Cold coverage `0.855` | 운영 후보, pipeline 고정 필요 |

## 2. Warm 운영안

- 적용 기준
- 예측 대상 작가가 `track3_train` 기준 학습 데이터에 1건 이상 있으면 Warm으로 봄
- H68에서 `3건 이상`, `5건 이상`으로 기준을 높이면 전체 Warm 성능이 악화됨
- 저이력 작가도 Cold fallback보다 Warm 모델이 우세함

- 사용 후보 모델
- `LightGBM`
- H66 `larger_low_lr`
- 3개 seed 평균 기준으로 H31 current-like보다 개선

- 주요 피처
- 작품 구조 피처
- `medium_category`
- `support_category`
- `depth_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- `medium_ho_bucket`
- `aspect_ratio`
- 작가 피처
- `artist_name_ko`
- `artist_works_log`
- `artist_ln_price_median`
- `artist_ln_price_mean`
- `artist_ln_price_iqr`
- 호수/3D 보강 피처
- `ho_bucket_refined`
- `is_large_ho`
- `is_extra_large_ho`
- `area_per_ho_log`
- `ho_per_area_log`
- `ho_area_gap_abs`
- `log_ho`
- `is_3d_work`
- `volume_log`
- `max_side_log`
- `min_side_log`

- 남은 조건
- 작가 가격 통계는 날짜 컬럼 확보 후 temporal-safe 방식으로 재검증해야 함
- 이 조건이 해결되기 전에는 “성능 후보”로는 채택 가능하지만 “운영 확정”은 보류함

## 3. Cold 운영안

- 적용 기준
- 예측 대상 작가가 학습 데이터에 없으면 Cold로 봄
- 작가명과 작가별 과거 가격 통계는 사용하지 않음

- 사용 후보 모델
- 기본 Cold: LAD / Quantile 회귀 계열
- 3D 작품: 3D 피처를 포함한 LAD / Quantile 회귀 계열
- 최종 예측 정책
- 2D 또는 일반 작품은 기본 Cold 모델 사용
- 3D 작품은 3D 피처 모델로 대체

- 주요 피처
- `medium_category`
- `support_category`
- `orientation`
- `medium_ho_bucket`
- `artist_works_log`
- `depth_cm`
- `log_area`
- `estimated_ho`
- `aspect_ratio`
- `ho_bucket_refined`
- `is_large_ho`
- `is_extra_large_ho`
- `area_per_ho_log`
- `ho_per_area_log`
- `ho_area_gap_abs`
- `log_ho`
- 3D 조건부 피처
- `is_3d_work`
- `volume_log`
- `max_side_log`
- `min_side_log`

- 주의
- Cold의 `artist_works_log`는 신규 작가에서는 0으로 들어가는 구조적 피처임
- 작가 가격 통계와는 다르게 Cold에서는 가격 이력 정보를 쓰지 않음

## 4. 가격 범위 / 신뢰도 출력

- 단일 예측 가격만 제공하는 것은 위험함
- Warm 저이력 작가와 Cold 2D/대형/초대형 작품은 오차가 커짐
- H70 내부 calibration split 기준으로 조건별 가격 범위 정책은 유지 가능함

### Warm 가격 범위 후보

| Warm 구간 | 80% 가격 범위 배수 | test coverage | 판단 |
|---|---:|---:|---|
| 전체 | x1.52 | 0.821 | 기본 범위 |
| A: 51건 이상 | x1.26 | 0.813 | 좁은 범위 |
| B: 11-50건 | x1.31 | 0.826 | 좁은 범위 |
| C: 4-10건 | x1.59 | 0.841 | 일반 범위 |
| D: 1-3건 | x1.94 | 0.794 | 넓은 범위 + 신뢰도 경고 |

### Cold 가격 범위 후보

| Cold 구간 | 80% 가격 범위 배수 | test coverage | 판단 |
|---|---:|---:|---|
| 전체 | x2.27 | 0.855 | 기본 Cold 범위 |
| 표준 3D | x2.06 | 0.887 | 비교적 안정 |
| 표준 2D | x2.42 | 0.783 | 넓은 범위 |
| 대형/초대형 high-risk | x2.88 | 0.794 | 넓은 범위 + 신뢰도 경고 |
| 대형 호수 | x3.11 | 0.826 | 넓은 범위 |
| 초대형 호수 | x3.11 | 0.876 | 넓은 범위 |

## 5. 미채택한 주요 후보

| 후보 | 판단 | 근거 |
|---|---|---|
| Warm 라우팅 기준 3건/5건 이상 | 미채택 | H68에서 기준을 높일수록 Warm 성능 악화 |
| Cold 2D fallback | 미채택 | H8에서 전체 Cold와 Cold 2D 모두 악화 |
| Cold 3D 중간 부피 예외 | 미채택 | H71에서 train 기준 threshold 적용 시 p95 악화 |
| 재료 flag/희소도 피처 | 미채택 | H13에서 Cold 개선 없음, Warm 악화 |
| 크기-재료 조합 피처 | 미채택 | H14에서 Cold 개선 없음 |
| medium/support 조합 정리 | 미채택 | H72 grid 재검증에서도 H32보다 median APE 악화 |
| H57 확장 작가 이력 피처 | 미채택 | H67에서 개선 폭이 채택 기준 미달 |
| H58 상호작용 피처 | 미채택 | H67에서 H66보다 악화 |

## 6. 남은 리스크

| 리스크 | 영향 | 현재 대응 |
|---|---|---|
| 작가 이력 피처 temporal-safe 미검증 | Warm 운영 확정의 핵심 리스크 | H16 보류, 날짜/거래시점 컬럼 확보 필요 |
| release test 반복 사용 | 의사결정이 test set에 맞춰질 가능성 | 최종 출시 전 새 holdout 또는 내부 CV 기준 재확인 권장 |
| calibration pipeline 미고정 | 가격 범위가 재학습마다 흔들릴 수 있음 | H70 방식의 calibration split을 pipeline에 고정 필요 |
| 운영 입력 결측 데이터 부족 | 결측 대응 모델 검증 부족 | H15 보류, 운영 입력 로그 확보 필요 |

## 7. 현재 결론

- 현재 기준으로는 Warm / Cold 단일 공유 모델보다 분리 운영이 더 타당함
- Warm은 H66 LightGBM 후보가 가장 강함
- Cold는 H32 조건부 fallback이 가장 강함
- 가격 예측 서비스에서는 단일 가격보다 가격 범위와 신뢰도 경고를 함께 제공하는 것이 안전함
- 단, 운영 확정 전 필수 조건은 아래 2개임
- 작가 이력 피처의 temporal-safe 재검증
- calibration split을 포함한 재현 가능한 production 학습 pipeline 구성
