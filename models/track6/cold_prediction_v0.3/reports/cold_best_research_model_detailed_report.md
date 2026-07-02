# Cold 최고 성능 가격 예측 모델 상세 리포트

작성일: 2026-06-10  
대상 모델: 검색 피처 포함 Cold 최고 성능 연구 기준 예측가격  
사용 목적: Cold 가격 예측 모델이 어떤 입력과 계산 순서로 최종 예측가격을 만드는지 설명

## 1. 결론 요약

이 문서는 Cold fixed test 전체 지표 기준으로 가장 좋은 성능을 보인 `검색 피처 포함 연구 기준 예측가격`만 설명한다.

상사 공유용 설명에서는 이 문서만 보면 되도록 최고 성능 경로에 필요한 입력, 계산식, 보정 과정, 재현 결과만 남겼다.

최고 성능 모델의 핵심은 아래와 같다.

- 작품 크기, 매체, 지지체, 작가 메타, 작가명 검색 피처를 함께 사용한다.
- LightGBM 분위 모델로 기준 로그가격과 예측 불확실성을 만든다.
- 예측구간폭이 넓고 과대예측 위험이 큰 row는 보수 분위 가격 쪽으로 낮춘다.
- 작가 검색 결과의 갤러리/미술관 문맥을 이용해 작가 단위 보정값을 마지막에 더한다.
- 최종 로그가격을 `exp()`로 원화 가격으로 변환한다.

fixed test 3,099건 기준 성능은 아래와 같다.

| 예측 단계 | MdAPE | MAPE | p95 APE | 설명 |
|---|---:|---:|---:|---|
| 검색포함 대표 로그가격 | 0.424663 | 0.991042 | 3.305298 | 검색 피처 포함 LightGBM 분위 모델 기반 대표값 |
| 과대예측 방어 로그가격 | 0.417765 | 0.963963 | 2.537708 | 예측구간폭/gap 조건에서 보수 분위 쪽으로 낮춘 값 |
| 최종 검색보정 로그가격 | 0.409820 | 0.849260 | 2.346465 | 방어값에 작가 검색 보정값을 더한 최고 성능 값 |

## 2. 전체 계산 흐름

최종 예측가격은 `기준가 생성 + 위험 방어 + 작가 검색 보정` 순서로 만든다.

```text
[작품 입력 정보 + 작가 정보]
  - 작품 크기
  - 매체와 지지체
  - 작가명 또는 artist_key
  - 작가 생년, 활동단계, 작품 수, 팔로워 등 작가 메타
        |
        v
[작가명 기반 검색 피처 결합]
  - 저장된 검색 피처 캐시 사용
  - 실시간 검색이 아니라 기존에 수집/표준화한 작가 단위 검색 결과 사용
        |
        v
[검색 피처 포함 LightGBM 분위 예측]
  - 기준 로그가격 후보 생성
  - 하위/중앙/상위 분위 로그가격 생성
  - 예측구간폭으로 불확실성 계산
        |
        v
[예측구간폭 기반 대표 로그가격 안정화]
  - 예측구간폭 구간별 out-of-fold 잔차 중앙값 보정
  - 보정값은 로그가격 기준 -0.25 ~ +0.25 안으로 제한
        |
        v
[과대예측 방어]
  - 예측구간폭이 넓고 대표 로그가격이 보수 분위보다 높게 튀면
    대표 로그가격을 보수 분위 쪽으로 50% 낮춤
        |
        v
[작가 검색 보정값 추가]
  - 갤러리/미술관 검색 문맥 기반 작가별 frozen lookup 사용
  - 작가별 보정값을 로그가격에 더함
        |
        v
[최종 로그가격]
        |
        v
[최종 예측가격_KRW = exp(최종 로그가격)]
```

## 3. 입력 피처

### 3.1 작품 피처

작품 자체에서 계산되는 피처는 가격의 기본 크기와 형태를 잡는 역할을 한다.

| 피처 | 생성 방식 | 역할 |
|---|---|---|
| `width_cm` | 작품 폭을 cm 단위로 정규화 | 작품 크기 |
| `height_cm` | 작품 높이를 cm 단위로 정규화 | 작품 크기 |
| `depth_cm` | 작품 깊이를 cm 단위로 정규화, 없으면 0 또는 결측 처리 | 입체 작품 여부 보조 |
| `area_cm2` | `width_cm * height_cm` | 2D 기준 면적 |
| `log_area` | `log1p(area_cm2)` | 면적의 과도한 스케일 완화 |
| `aspect_ratio` | `width_cm / height_cm` | 세로형, 가로형, 균형형 구분 |
| `has_depth` | 깊이 정보 존재 여부 | 입체성 보조 |
| `is_3d_candidate` | 깊이/카테고리 기반 입체 후보 여부 | 조각/입체 작품 보조 |
| `medium_category` | 매체 분류 | 회화, 조각, 판화 등 재료 특성 |
| `support_category` | 지지체 분류 | 캔버스, 종이, 패널 등 지지체 특성 |
| `size_bucket` | `log_area` 분위 구간 | 작은 작품/중간/큰 작품 구분 |
| `support_size_bucket` | `support_category + size_bucket` | 지지체와 크기의 조합 효과 |

### 3.2 작가 메타 피처

이 모델은 같은 작가의 충분한 거래 이력을 직접 기준가로 쓰는 방식이 아니다. 대신 작가의 공개 메타와 활동 규모를 보조 신호로 사용한다.

| 피처 | 의미 |
|---|---|
| `artist_meta_birth_year` | 작가 생년 |
| `artist_meta_career_stage` | 생년/활동 정보를 바탕으로 만든 활동단계 |
| `artist_meta_nationality` | 작가 국적 |
| `artist_meta_total_works` | 수집된 작가 작품 수 |
| `artist_meta_for_sale_works` | 판매 중으로 확인된 작품 수 |
| `artist_meta_followers` | 작가 팔로워 수 |
| `artist_meta_for_sale_ratio` | 판매 중 작품 수 / 전체 작품 수 |
| `artist_meta_total_works_log` | `log1p(artist_meta_total_works)` |
| `artist_meta_followers_log` | `log1p(artist_meta_followers)` |
| `artist_meta_*_missing` | 해당 작가 메타가 없는지 여부 |

활동단계는 대략 아래처럼 해석한다.

```text
작가나이 = 기준연도 - artist_meta_birth_year

artist_meta_career_stage =
  early      if 작가나이 < 40
  mid        if 40 <= 작가나이 < 60
  senior     if 60 <= 작가나이 < 80
  legacy     if 작가나이 >= 80 또는 작고 작가로 추정
  missing    if 생년 정보 없음
```

정확한 분류는 데이터 생성 시점의 규칙을 따르며, 이 문서에서는 `작가의 활동 세대와 시장 인지도 차이를 반영하기 위한 구간 피처`로 이해하면 된다.

### 3.3 검색 피처

검색 피처는 작품별 검색값이 아니라 작가명 기준 검색 결과를 작가 단위로 집계한 값이다. 실시간 검색을 매번 수행하지 않고, 기존에 수집한 검색 캐시와 표준화 결과를 사용한다.

| 피처 묶음 | 포함 피처 예시 | 의미 |
|---|---|---|
| 검색량 | `search_result_count`, `search_source_count` | 검색 결과 수와 고유 출처 수 |
| 미술 문맥 | `search_art_context_count`, `search_art_match_ratio` | 검색 결과가 미술/작품 문맥인지 |
| 전시 문맥 | `search_exhibition_context_count`, `search_exhibition_ratio` | 전시 이력이나 전시 소개가 잡히는지 |
| 갤러리/미술관 문맥 | `search_gallery_context_count` | 갤러리, 미술관, 기관 문맥 |
| 시장 문맥 | `search_market_context_count` | 거래, 가격, 판매 관련 문맥 |
| 동명이인 위험 | `search_homonym_context_count`, `search_homonym_risk_grade` | 검색 결과가 다른 동명이인과 섞일 위험 |
| 검색 품질 | `search_quality_score`, `search_quality_grade` | 검색 신호의 종합 신뢰도 |
| 수집 성공 여부 | `search_collected_flag`, `search_success_flag` | 검색 피처가 정상 수집됐는지 |
| 로그 변환 | `search_result_count_log`, `search_source_count_log` 등 | 검색량 피처의 스케일 완화 |
| 상호작용 | `search_quality_x_log_area`, `search_art_match_x_followers_log`, `search_exhibition_x_career_stage`, `search_size_quality_bucket` | 검색 신호와 작품/작가 조건의 조합 효과 |

검색 품질 점수는 아래 요소를 조합해 만든다.

```text
검색품질점수 =
  0.30 * 미술문맥비율
+ 0.20 * 신뢰도메인비율
+ 0.15 * 전시문맥비율
+ 0.15 * 시장/거래문맥비율
+ 0.10 * 최근결과비율
+ 0.10 * 검색제공자커버리지점수
+ 0.10 * 작가명일치비율
- 0.30 * 동명이인위험비율
```

검색 품질 등급은 아래처럼 해석한다.

| 등급 | 기준 | 의미 |
|---|---|---|
| high | 검색품질점수 0.70 이상, 동명이인 위험 0.20 미만 | 검색 신호가 비교적 안정적 |
| medium | 검색품질점수 0.45 이상, 동명이인 위험 0.40 미만 | 참고 가능하지만 검수 필요 |
| low | 위 기준 미달 | 보정에 주의 필요 |
| missing | 검색 결과 없음 | 검색 신호 없음 |

## 4. 모델과 계산식

### 4.1 검색포함 대표 로그가격 생성

먼저 LightGBM 분위 모델이 작품 피처, 작가 메타 피처, 검색 피처를 함께 입력받아 여러 분위의 로그가격을 만든다.

```text
검색기반_하위분위_로그가격,
검색기반_중앙분위_로그가격,
검색기반_상위분위_로그가격
  = LightGBM_분위모델(
      작품피처
      + 작가메타피처
      + 검색피처
      + 검색상호작용피처
    )
```

예측 불확실성은 상위 분위와 하위 분위의 차이로 계산한다.

```text
예측구간폭
  = 검색기반_상위분위_로그가격
  - 검색기반_하위분위_로그가격
```

그 다음 예측구간폭을 구간화하고, 같은 구간의 out-of-fold 잔차 중앙값으로 대표값을 안정화한다.

```text
예측구간폭_구간 = bucket(예측구간폭)

구간별_잔차중앙값
  = median(실제_로그가격 - 검색기반_중앙분위_로그가격)
    within same 예측구간폭_구간

구간별_보정값
  = clip(구간별_잔차중앙값, -0.25, +0.25)

검색포함_대표로그가격
  = 검색기반_중앙분위_로그가격
  + 구간별_보정값
```

여기서 out-of-fold는 해당 row를 직접 학습한 모델의 예측값을 쓰지 않고, 그 row가 빠진 fold에서 나온 예측값을 사용한다는 뜻이다. 같은 row를 외우는 방식의 과적합을 줄이기 위한 장치다.

### 4.2 과대예측 방어 로그가격 생성

대표 로그가격이 높게 튈 가능성이 있는 row는 보수 분위 가격 쪽으로 낮춘다. 이 단계의 목적은 평균 오차뿐 아니라 p95 큰 오차를 줄이는 것이다.

먼저 validation 기준으로 두 임계값을 고정한다.

```text
예측구간폭_임계값 = 1.4612207078910142

gap_임계값
  = median(validation에서 검색포함_대표로그가격 - CatBoost_40분위_로그가격)
  = 0.07715547281151025
```

CatBoost 40분위는 gap 임계값을 정하는 데 사용했고, 실제 방어 이동은 LightGBM 40분위 로그가격을 보수 기준으로 사용한다.

```text
방어조건 =
  (예측구간폭 >= 1.4612207078910142)
  AND (검색포함_대표로그가격 - LightGBM_40분위_로그가격 >= 0.07715547281151025)
  AND (LightGBM_40분위_로그가격 < 검색포함_대표로그가격)
```

방어조건이 꺼져 있으면 값을 그대로 둔다.

```text
과대예측방어_로그가격 = 검색포함_대표로그가격
```

방어조건이 켜져 있으면 대표 로그가격을 LightGBM 40분위 로그가격 쪽으로 50% 낮춘다.

```text
과대예측방어_로그가격
  = 0.50 * 검색포함_대표로그가격
  + 0.50 * LightGBM_40분위_로그가격
```

### 4.3 작가 검색 보정값 추가

마지막으로 작가별 검색 보정값을 더한다. 이 값은 `h23_gallery_museum_median_cap0.2` 계열에서 만든 작가 단위 frozen lookup이다.

핵심 해석은 아래와 같다.

- 갤러리/미술관 문맥이 강하게 잡히는 작가는 검색 신호가 가격 잔차를 설명하는 경우가 있었다.
- 이 효과를 작가별 보정값으로 저장했다.
- 보정값은 로그가격 기준 약 `-0.20`에서 `+0.20` 범위 안으로 제한되어 있다.
- lookup에 없는 작가는 보정값을 0으로 둔다.

```text
작가검색보정_로그값 =
  search_delta_lookup[artist_key]
  if artist_key exists in lookup

작가검색보정_로그값 = 0
  if artist_key does not exist in lookup
```

최종 로그가격은 아래와 같다.

```text
최종_로그가격
  = 과대예측방어_로그가격
  + 작가검색보정_로그값
```

원화 예측가격은 로그가격을 다시 가격 단위로 변환해서 만든다.

```text
최종_예측가격_KRW = exp(최종_로그가격)
```

전체 식을 한 번에 쓰면 아래와 같다.

```text
최종_예측가격_KRW
  = exp(
      과대예측방어_로그가격
      + 작가검색보정_로그값
    )

과대예측방어_로그가격
  = if 방어조건 then
      0.50 * 검색포함_대표로그가격
    + 0.50 * LightGBM_40분위_로그가격
    else
      검색포함_대표로그가격

검색포함_대표로그가격
  = 검색기반_중앙분위_로그가격
  + clip(예측구간폭_구간별_잔차중앙값, -0.25, +0.25)
```

## 5. 성능 개선이 발생한 지점

성능은 한 번에 좋아진 것이 아니라 세 단계가 누적되며 개선됐다.

| 단계 | MdAPE | MAPE | p95 APE | 개선 해석 |
|---|---:|---:|---:|---|
| 검색포함 대표 로그가격 | 0.424663 | 0.991042 | 3.305298 | 검색 피처와 작가 메타를 포함한 기준 예측 |
| 과대예측 방어 로그가격 | 0.417765 | 0.963963 | 2.537708 | 예측구간폭이 넓은 위험 row의 큰 오차 감소 |
| 검색 delta만 추가한 로그가격 | 0.412921 | 0.875749 | 2.937449 | 작가 검색 문맥이 평균 오차를 크게 낮춤 |
| 과대예측 방어 + 검색 delta | 0.409820 | 0.849260 | 2.346465 | 평균 오차와 큰 오차를 동시에 가장 낮춤 |

해석은 아래와 같다.

- 검색 피처는 작가의 공개 활동성, 전시성, 기관성, 시장 문맥을 보조적으로 설명한다.
- 과대예측 방어는 가격이 높게 튈 수 있는 row의 큰 오차를 줄인다.
- 작가 검색 보정은 평균 오차를 낮추는 효과가 크다.
- 두 보정은 같은 기능을 중복 수행하지 않고, 서로 다른 오차 원인을 보완한다.

## 6. 재현 확인

최고 성능 모델은 별도 검증 스크립트로 재현 확인했다.

```bash
python3 scripts/track6/verify_cold_best_research_reproducibility.py
```

재현 검증은 아래 상류 산출물을 다시 읽어 수행한다.

| 입력 | 파일 | 역할 |
|---|---|---|
| 검색포함 대표 예측 | `experiments/track6/PP-Y18_cold_y16_top_candidate_stability/outputs/predictions.csv` | 대표 로그가격 |
| 예측구간폭 보강값 | `experiments/track6/PP-Y2_cold_lgbq_search_external_combo/outputs/predictions.csv` | `quantile_width_log` 보강 |
| q40 분위 후보 | `experiments/track6/PP-QR1_cold_quantile_regression_alpha_grid/outputs/predictions.csv` | 방어 임계값과 보수 분위 |
| 검색 delta 후보 | `experiments/track6/PP-H20_H26_search_feature_expansion/outputs/candidate_predictions.csv` | 작가 검색 보정 원천 |
| 기록 지표 | `experiments/track6/PP-COLD-DEFENSE1_cold_guard_search_layer_combination/outputs/test_metrics.csv` | 기존 기록 지표와 비교 |

재현 결과는 아래와 같다.

| 검증 항목 | 결과 |
|---|---:|
| test row 수 | 3,099 |
| validation row 수 | 2,753 |
| 검색 lookup 작가 수 | 372 |
| test 검색 커버리지 | 1.000000 |
| validation에서 재계산한 guard 임계값 차이 | 0.000e+00 |
| 후처리기와 독립 계산식의 로그가격 최대 차이 | 0.000e+00 |
| frozen lookup delta와 원천 delta의 test 최대 차이 | 2.665e-15 |
| 재계산 지표와 기록 지표의 최대 차이 | 1.110e-16 |
| 전체 재현 통과 여부 | true |

재현 산출물은 아래에 저장되어 있다.

| 구분 | 위치 |
|---|---|
| 재현 검증 스크립트 | `scripts/track6/verify_cold_best_research_reproducibility.py` |
| 재현 검증 결과 | `models/track6/cold_prediction_v0.3/reproduction/best_research_reproducibility_check.json` |
| 재현 지표 CSV | `models/track6/cold_prediction_v0.3/reproduction/best_research_reproducibility_metrics.csv` |
| 후처리기 | `models/track6/cold_prediction_v0.3/predict/apply_cold_postprocess_v0_3.py` |
| 방어/검색 보정 파라미터 | `models/track6/cold_prediction_v0.3/config/cold_postprocess_params_v0_3.json` |
| 작가 검색 보정 lookup | `models/track6/cold_prediction_v0.3/config/search_delta_lookup_v0_3.json` |

## 7. 설명용 용어 정리

| 용어 | 의미 |
|---|---|
| 로그가격 | 가격에 자연로그를 취한 값. 고가 작품의 영향이 과도하게 커지는 것을 완화한다. |
| 분위 예측 | 하나의 가격만 예측하지 않고 낮은 가격대, 중앙 가격대, 높은 가격대를 함께 예측하는 방식이다. |
| 예측구간폭 | 상위 분위 로그가격과 하위 분위 로그가격의 차이. 값이 클수록 모델이 불확실하다는 뜻이다. |
| out-of-fold | 해당 row를 학습하지 않은 fold에서 나온 예측값. 잔차 보정의 과적합을 줄이기 위해 사용한다. |
| 과대예측 방어 | 예측가격이 보수 분위보다 높고 불확실성도 클 때 가격을 낮춰 큰 오차를 줄이는 후처리다. |
| 검색 delta | 작가 검색 문맥에서 나온 작가별 로그가격 보정값이다. |
| frozen lookup | 실시간 계산이 아니라 고정된 파일에 저장된 조회표다. |

## 8. 내부 추적 ID

본문에서는 이해를 돕기 위해 기능명으로 설명했다. 코드와 산출물을 대조할 때 필요한 내부 ID는 아래와 같다.

| 문서용 이름 | 내부 추적 ID | 기능 |
|---|---|---|
| 검색포함 대표 로그가격 | `PP-Y18 qwidth representative` | 검색 피처 포함 LightGBM 분위 모델 기반 대표값 |
| 과대예측 방어 로그가격 | `guard` | qwidth/gap 조건에서 보수 분위 쪽으로 낮춘 값 |
| 작가 검색 보정값 | `h23_gallery_museum_median_cap0.2` | 작가 검색 문맥 기반 보정값 |
| 최종 검색보정 로그가격 | `guard_search_gm`, `COLD_BASE_RESEARCH_V1`, `v0.3 guard+search` | fixed test 전체 지표 기준 최고 성능 예측값 |

## 9. 최종 설명 문장

상사에게 한 문단으로 설명할 때는 아래처럼 말하면 된다.

```text
Cold 최고 성능 가격 예측 모델은 작품 크기, 매체, 지지체, 작가 메타와 작가명 검색 피처를 함께 사용합니다.
먼저 LightGBM 분위 모델이 기준 로그가격과 예측구간폭을 만들고,
예측구간폭이 넓어 과대예측 위험이 큰 경우에는 보수 분위 가격 쪽으로 50% 낮춥니다.
마지막으로 갤러리/미술관 검색 문맥에서 만든 작가별 보정값을 더해 최종 로그가격을 만들고,
이를 exp()로 변환해 최종 원화 예측가격을 산출합니다.
이 경로는 Cold fixed test 3,099건에서 MdAPE 0.409820, MAPE 0.849260, p95 APE 2.346465로 가장 좋은 성능을 보였고,
별도 재현 스크립트에서도 기존 기록 지표와 동일하게 재현됐습니다.
```
