# 갤러리 티어/전시 활동 피처 실험 감사

- 작성일: 2026-06-03
- 확인 목적: 갤러리 티어, 개인전/단체전/아트페어 등 전시 활동 피처가 Track6 가격 예측 실험에서 실제로 사용됐는지 점검
- 확인 범위:
  - `data/track6_split`
  - `data/track6_split_with_year_type_edition_size_artist_name`
  - `experiments/track6/E4`, `F1`, `F3`, `F5`, `G4`, `G8`, `G9`, `I1`, `I2`
  - `PP-G1~PP-G5`, `PP-W`, `PP-H`

## 1. 결론

- 갤러리 티어는 Track6 최종/확장 feature split에 들어가지 않았다.
- 따라서 갤러리 티어를 사용한 Track6 모델 성능 실험은 아직 제대로 실행됐다고 보기 어렵다.
- 전시 활동 피처는 확장 split에는 존재하고, 과거 Group E/F/G/I 실험에서 실제로 사용됐다.
- 다만 전시 활동 피처 실험은 현재 최종 후보 라인인 `PP-W`, `PP-H`와 같은 최신 Cold 후처리 실험에는 반영되지 않았다.
- 따라서 전시 활동 피처는 “초기 후보 검증은 됐지만, 최종 후보 구조에서 재검증 필요” 상태로 보는 것이 맞다.

## 2. 데이터 존재 여부

| 피처 | 현재 최종 split `data/track6_split` | 확장 split `data/track6_split_with_year_type_edition_size_artist_name` | 판단 |
|---|---|---|---|
| `gallery_tier` | 없음 | 없음 | Track6 모델 실험 미실행 |
| `artist_exhibition_solo_count` | 없음 | 있음 | 과거 확장 split 실험에서 사용 |
| `artist_exhibition_group_count` | 없음 | 있음 | 과거 확장 split 실험에서 사용 |
| `artist_exhibition_fair_count` | 없음 | 있음 | 과거 확장 split 실험에서 사용 |
| `artist_exhibition_total_count` | 없음 | 있음 | 과거 확장 split 실험에서 사용 |
| `artist_exhibition_available_count` | 없음 | 있음 | 과거 확장 split 실험에서 사용 |

## 3. 전시 활동 피처 생성 방식

- 생성 스크립트: `scripts/track6/augment_track6_split_artist_meta.py`
- 대상 split: `data/track6_split_with_year_type_edition_size_artist_name`
- join key: `_track6_row_id`
- 원천 데이터: `data/track4_primary_market_raw_collected.csv`
- 매핑:
  - `artist_exhibition_solo_count` <- `saatchi__solo_count`
  - `artist_exhibition_group_count` <- `saatchi__group_count`
  - `artist_exhibition_fair_count` <- `saatchi__fair_count`
- 보정:
  - 전시 횟수 값이 `200`을 초과하면 연도 오파싱 가능성이 높다고 보고 결측 처리
  - 각 전시 피처별 결측 flag 생성
  - `artist_exhibition_total_count`, `artist_exhibition_available_count` 생성

## 4. 전시 활동 피처 커버리지

| split | rows | solo non-null | group non-null | fair non-null | total non-null |
|---|---:|---:|---:|---:|---:|
| train | 26,914 | 23,685 | 23,999 | 24,856 | 24,885 |
| validation cold | 2,753 | 2,484 | 2,457 | 2,544 | 2,544 |
| test cold | 3,099 | 2,736 | 2,748 | 2,881 | 2,881 |
| validation warm | 519 | 422 | 434 | 451 | 451 |
| test warm | 607 | 525 | 515 | 545 | 546 |

- 커버리지는 낮지 않다.
- 따라서 전시 활동 피처는 데이터가 없어서 못 쓰는 피처가 아니라, 현재 최종 실험 split과 최신 후처리 라인에 아직 반영되지 않은 피처다.

## 5. 갤러리 티어 데이터 상태

| 원천 파일 | 컬럼 | non-null 비율 | 주요 문제 |
|---|---|---:|---|
| `data/track4_primary_market_raw_collected.csv` | `saatchi__gallery_tier` | 0.3961 | 값이 거의 `3`으로 고정되어 변별력이 낮음 |
| `data/track4_primary_market_raw_collected.csv` | `gallery_primary__gallery_tier` | 0.0000 | 값 없음 |
| `data/track4_primary_market_cleaned_v1.csv` | `gallery_tier` | 0.9132 | `3`, `Gallery` 등이 섞여 실제 등급으로 보기 어려움 |
| `data/track4_primary_market_cleaned_v1.csv` | `gallery_tier_validated` | 0.0370 | 검증된 tier는 매우 적음 |
| `data/primary_market_dataset.csv` | `gallery_tier` | 1.0000 | 값은 있으나 Track6 split에 연결되지 않음 |

- 갤러리 티어는 원천 데이터에는 있으나 Track6 feature split으로 표준화/조인되지 않았다.
- 특히 `saatchi__gallery_tier`는 non-null이 있어도 대부분 `3`이라 모델 피처로 넣어도 정보량이 낮을 가능성이 크다.
- `gallery_tier_validated`는 품질은 더 낫지만 커버리지가 낮다.

## 6. 기존 전시 활동 실험 결과

### 6.1 전시 횟수 단독

| 실험 | 범위 | 최선 모델 | MdAPE | MAPE | p95_APE | 판단 |
|---|---|---|---:|---:|---:|---|
| `E4` 전시 횟수 단독 | Warm | Huber | 0.7452 | 1.5890 | 6.6184 | 단독 피처로 약함 |
| `E4` 전시 횟수 단독 | Cold | Huber | 0.7061 | 1.4040 | 7.2950 | 단독 피처로 약함 |

- 개인전/단체전/아트페어 횟수만으로 가격을 설명하기에는 부족했다.
- 이 결과는 전시 활동 피처를 단독 모델로 쓰기보다 작품 조건, 작가 메타와 결합해야 한다는 근거가 된다.

### 6.2 작품 기본 피처 + 전시 경력

| 실험 | 범위 | 기준 MdAPE | 전시 추가 MdAPE | MdAPE 변화 | p95 변화 | 판단 |
|---|---|---:|---:|---:|---:|---|
| `G4` | Warm | 0.4962 | 0.4879 | -0.0083 | -0.0055 | 소폭 개선 |
| `G4` | Cold | 0.5128 | 0.4980 | -0.0147 | +1.4516 | MdAPE는 개선, tail 악화 |

- 작품 기본 피처에 전시 경력을 추가하면 대표 오차는 일부 줄었다.
- Cold에서는 p95가 크게 악화되어, 그대로 최종 후보로 쓰기는 어렵다.
- 전시 피처는 정확도 개선 가능성은 있으나 큰 오차 방어 장치와 함께 써야 한다.

### 6.3 호수 + 세대/전시 경력

| 실험 | 범위 | 기준 MdAPE | 후보 MdAPE | MdAPE 변화 | MAPE 변화 | p95 변화 | 판단 |
|---|---|---:|---:|---:|---:|---:|---|
| `I1` | Warm | 0.5244 | 0.5169 | -0.0075 | -0.0128 | -0.2751 | 개선 |
| `I1` | Cold | 0.5070 | 0.4769 | -0.0301 | -0.2388 | -0.7019 | 개선 |

- 호수만 쓰는 단순 기준에서는 생년+전시 경력 추가가 명확히 개선됐다.
- 특히 Cold에서 MdAPE, MAPE, p95가 모두 개선됐다.
- 다만 이 기준은 최신 Cold 최종 후보보다 단순한 기준선이므로, 최종 모델 채택 근거로 바로 쓰기는 부족하다.

### 6.4 작품 기본 피처 + 세대/전시 경력

| 실험 | 범위 | 기준 MdAPE | 후보 MdAPE | MdAPE 변화 | MAPE 변화 | p95 변화 | 판단 |
|---|---|---:|---:|---:|---:|---:|---|
| `I2` | Warm | 0.4962 | 0.5074 | +0.0112 | -0.0222 | +0.1072 | 대표 오차 악화 |
| `I2` | Cold | 0.5128 | 0.4643 | -0.0485 | +0.0784 | +0.2821 | MdAPE 개선, 평균/tail 악화 |

- Cold에서는 MdAPE 개선폭이 크다.
- 반면 MAPE와 p95는 악화되어 가격 범위/신뢰도 정책 없이 쓰기 어렵다.

### 6.5 작품 기본 피처 + 전체 작가 메타

| 실험 | 범위 | 기준 MdAPE | 전체 메타 MdAPE | MdAPE 변화 | MAPE 변화 | p95 변화 | 판단 |
|---|---|---:|---:|---:|---:|---:|---|
| `G9` | Warm | 0.4962 | 0.4390 | -0.0572 | -0.0523 | -0.0226 | 개선 |
| `G9` | Cold | 0.5128 | 0.4684 | -0.0443 | +0.1295 | +0.3710 | MdAPE 개선, 평균/tail 악화 |

- 전시 활동만 단독으로 쓰는 것보다 전체 작가 메타 묶음 안에서 쓸 때 효과가 더 컸다.
- Warm에서는 전체 지표가 모두 개선됐다.
- Cold에서는 MdAPE는 좋아졌지만 MAPE/p95가 악화되어 보수적 운영 정책이 필요하다.

## 7. 최신 후처리 실험 반영 여부

| 실험군 | 전시 피처 포함 | 갤러리 티어 포함 | 판단 |
|---|---|---|---|
| `PP-W1~PP-W5` | 없음 | 없음 | 최신 Cold 작가 메타 고도화에 전시/갤러리 미반영 |
| `PP-H7~PP-H10` | 검색 문맥상 `search_exhibition_context_count`, `search_gallery_context_count`만 있음 | 실제 `gallery_tier` 없음 | 검색 기반 간접 피처만 사용 |
| `PP-G1~PP-G5` | 요구 컬럼 누락으로 차단 | 요구 컬럼 누락으로 차단 | 신규 외부 DB 실험은 미실행 |

## 8. 실험이 제대로 됐는지에 대한 판단

- 전시 활동 피처:
  - 데이터 생성은 됐다.
  - 과거 확장 split 실험도 실제로 실행됐다.
  - 단독/조합/작품 기본 피처 결합까지 일부 검증됐다.
  - 그러나 최신 최종 후보 구조에서 재검증되지 않았기 때문에 “최종 후보 기준으로 제대로 완료”됐다고 보기는 어렵다.
- 갤러리 티어:
  - 원천 데이터에는 있다.
  - Track6 학습 split에는 없다.
  - PP-G3/PP-G4는 요구 컬럼 누락으로 차단됐다.
  - 따라서 갤러리 티어 실험은 아직 제대로 실행되지 않았다.

## 9. 필요한 보완 실험

1. `PP-X1` 전시 활동 피처를 최신 Cold CatBoost 후보에 추가
   - 기준: `PP-W2 generated_all_meta_all`
   - 추가 피처: `artist_exhibition_solo_count`, `artist_exhibition_group_count`, `artist_exhibition_fair_count`, `artist_exhibition_total_count`, 결측 flag
   - 목적: 최신 CatBoost 구조에서도 전시 활동 피처가 MdAPE를 낮추는지 확인

2. `PP-X2` 전시 활동 피처를 최신 LightGBM Quantile 후보에 추가
   - 기준: `PP-W4 base_lightgbm_quantile_meta_all`
   - 목적: 전시 활동 피처가 MAPE/p95 안정화에 도움이 되는지 확인

3. `PP-X3` 전시 활동 피처 기반 보정/라우팅
   - 기준: 전시 횟수 없음/적음/많음, 전시 정보 결측 여부
   - 목적: 전시 정보가 부족한 작가에서 큰 오차가 늘어나는지 확인

4. `PP-X4` 갤러리 티어 표준화 후 모델 투입
   - 우선 `gallery_tier_validated`를 사용하되, 결측률이 높으므로 `gallery_tier_available_flag`와 함께 사용
   - `saatchi__gallery_tier`는 대부분 3으로 고정되어 단독 피처로는 위험

5. `PP-X5` 갤러리 티어 + 전시 활동 결합
   - 사용 피처: 검증된 갤러리 tier, 개인전/단체전/아트페어 수, 전시 정보 품질 flag
   - 목적: 작가의 시장 신뢰도와 활동 이력을 함께 보면 Cold 안정성이 좋아지는지 확인

## 10. 보고용 한 줄 결론

- 개인전/전시 활동 피처는 과거 확장 split에서 실험됐고 일부 개선 신호가 있었지만, 최신 최종 후보 모델에는 아직 반영되지 않았다.
- 갤러리 티어는 원천 데이터에는 있으나 Track6 학습 피처로 연결되지 않아 아직 제대로 실험되지 않았다.
- 따라서 다음 단계에서는 최신 `PP-W` Cold 후보에 전시 활동 피처와 정제된 갤러리 티어를 추가해 재검증해야 한다.

## 11. 재검증 실행 업데이트

- 업데이트일: 2026-06-03
- 실행 스크립트: `scripts/track6/run_pp_x_gallery_exhibition_revalidation.py`
- 실행 결과:
  - `PP-X1~PP-X5` 재검증 실험 실행 완료
  - 통합 결과 파일: `experiments/track6/PP-X_gallery_exhibition_summary_metrics.csv`
  - 실행 요약 문서: `docs/track6/experiments/pp_x_gallery_exhibition_revalidation_execution_summary.md`
- 핵심 결과:
  - CatBoost는 갤러리 피처 단독 추가에서만 아주 소폭 개선됐다.
  - LightGBM Quantile은 전시/갤러리 피처 추가 시 test MdAPE가 `0.4766`에서 `0.4451`까지 개선됐다.
  - 다만 해당 후보는 MAPE와 p95_APE가 악화되어 서비스 단일 후보로 바로 채택하기 어렵다.
  - p95 안정성 기준은 기존 `PP-W4 base_lightgbm_quantile_meta_all`이 여전히 더 낫다.
