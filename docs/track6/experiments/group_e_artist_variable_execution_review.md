# Group E 작가 변수 실험 실행 가능성 검토

- 작성일: `2026-05-27`
- 기준 split: `data/track6_split_with_year_type_edition_size_artist_name`
- 보강 스크립트: `scripts/track6/augment_track6_split_artist_meta.py`
- 보강 보고서: `docs/track6/dataset/artist_meta_feature_augmentation_report.md`

## 1. 보강 결과

- 기존 train / warm test / cold test 구성은 바꾸지 않았다.
- `_track6_row_id` 기준으로 full split에 있던 작가 메타를 feature 파일에 붙였다.
- 가격, 라벨, 출처 URL, `artist_meta_source`는 feature 파일에 넣지 않았다.
- 작가 메타 원값과 결측 여부 flag를 함께 추가했다.
- 전시 횟수는 원본 `saatchi__solo_count`, `saatchi__group_count`, `saatchi__fair_count`에서 가져왔다.
- 전시 횟수 컬럼에 섞여 있던 `2021`, `2024` 같은 연도성 이상값은 결측 처리했다.

## 2. 추가된 주요 컬럼

- 작가 기본 메타:
  - `artist_meta_birth_year`
  - `artist_meta_career_stage`
  - `artist_meta_nationality`
- 작가 활동량/시장 노출:
  - `artist_meta_total_works`
  - `artist_meta_for_sale_works`
  - `artist_meta_followers`
  - `artist_meta_is_p1`
- 작가 전시/아트페어 횟수:
  - `artist_exhibition_solo_count`
  - `artist_exhibition_group_count`
  - `artist_exhibition_fair_count`
  - `artist_exhibition_total_count`
- 결측/정보량:
  - `artist_meta_*_is_missing`
  - `artist_exhibition_*_is_missing`
  - `artist_meta_available_count`
  - `artist_meta_completeness_score`
  - `artist_exhibition_available_count`

## 3. Group E 실험별 실행 판단

| 실험 | 사용 피처 | 실행 판단 | 비고 |
|---|---|---|---|
| E1 | `artist_name_ko` | 바로 가능 | 기존 `B1_artist_name_only`와 중복 가능성이 높음. Warm 중심으로 해석 |
| E2 | `artist_works_log` | 바로 가능 | 생성 변수. 단독 효과 실험 가능 |
| E2-B | 학습량 10/20/30개 통제 | 별도 설계 필요 | 같은 작가의 학습량을 인위적으로 줄이는 재샘플링 실험 |
| E3 | `artist_meta_birth_year` | 바로 가능 | 숫자형 피처. 결측 flag와 함께 확인 권장 |
| E4 | `artist_exhibition_solo_count`, `artist_exhibition_group_count`, `artist_exhibition_fair_count` | 바로 가능 | 이상값 표준화 완료. 개별/묶음 실험 가능 |
| E5 | `artist_meta_nationality` | 바로 가능 | 범주형 피처. 국적별 표본 수 편차 확인 필요 |
| E6 | `artist_meta_total_works`, `artist_meta_for_sale_works` | 바로 가능 | 숫자형 피처. 출처/시점 의존성 해석 주의 |
| E7 | `artist_meta_followers`, `artist_meta_is_p1` | 바로 가능 | `artist_meta_is_p1`은 Cold test에서 값 종류가 제한적이므로 단독 결론 주의 |

## 4. 실험 실행 전 주의점

- E1은 작가명 자체를 쓰므로 Cold 결과는 참고값으로만 본다.
- E2의 `artist_works_log`는 수집값이 아니라 train 기준 작가별 작품 수로 만든 생성 변수다.
- E3~E7은 Cold에서도 사용할 수 있지만, 실제 운영에서 해당 작가 메타를 입력 또는 작가 DB에서 확보할 수 있어야 한다.
- E4 전시 횟수는 현재 Saatchi 계열 원본에서 온 값이므로, 다른 출처 작가에게 결측이 생길 수 있다.
- 모든 Group E 실험은 전체 / 메타 있음 / 메타 없음 구간 성능을 따로 보는 것이 좋다.

## 5. 권장 실행 순서

1. E1은 기존 B1 결과와 중복 여부를 먼저 확인한다.
2. E2는 단독 생성 변수 효과만 먼저 확인한다.
3. E3, E5는 기본 작가 프로필 단독 피처로 먼저 확인한다.
4. E4는 개인전/그룹전/아트페어를 각각 단독으로 본 뒤 묶음으로 비교한다.
5. E6, E7은 활동량/인지도 계열로 묶어 후속 실험까지 연결한다.
6. E2-B 학습량 통제 실험은 단순 feature ablation이 아니므로 별도 실험군으로 분리한다.

## 6. 폴더링 후보

- `experiments/track6/E1_artist_name_only`
- `experiments/track6/E2_artist_work_count_only`
- `experiments/track6/E2B_artist_training_amount_sensitivity`
- `experiments/track6/E3_artist_birth_year_only`
- `experiments/track6/E4_artist_exhibition_counts_only`
- `experiments/track6/E5_artist_nationality_only`
- `experiments/track6/E6_artist_activity_sale_exposure_only`
- `experiments/track6/E7_artist_popularity_only`

