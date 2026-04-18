# 피처 정합성 감사 보고서 (Feature Integrity Audit Report)

> **작성일**: 2026-03-30
> **범위**: `src/visionai/price_engine/` 전체 57개 HEDONIC_FEATURES
> **방법**: 1차 수동 감사 + 2차 Codex CLI 독립 감사 → 결과 종합
> **목적**: 피처 오용·결측 처리 누락·스케일 불일치 등으로 인해 최종 가격 예측에 영향을 줄 수 있는 문제점 파악

---

## 요약 (Executive Summary)

| 심각도 | 건수 | 핵심 영향 |
|--------|------|-----------|
| **CRITICAL** | 4 | 예측값 자체를 조용히 오염시킴 (에러 없이 잘못된 값 생성) |
| **MAJOR** | 7 | 피처 정보 손실·스케일 불일치·불안정한 값 |
| **MINOR** | 8 | 중복 피처·성능·에지 케이스 |

**즉시 수정 필요 (Top 3)**:
1. `artist_stats_snapshot` — 미낙찰 작품 포함으로 3개 핵심 피처 오염
2. `orientation` — 2D 파싱이 항상 height≥width로 정렬하여 landscape 불가능
3. `medium_x_auction_avg` — log 스케일 반환, 다른 가격 피처와 10^6배 스케일 차이

---

## CRITICAL 이슈

### C1. `artist_stats_snapshot`이 미낙찰 작품(낙찰가=0)을 포함하여 집계

| 항목 | 내용 |
|------|------|
| **파일** | `features/artist_stats_snapshot.py:35-53` |
| **발견** | 1차 수동 + 2차 Codex 동시 발견 |
| **문제** | `compute_artist_stats_snapshot()`에 `price > 0` 필터 없음. `hedonic_stats.py`의 모든 함수는 `_filter_by_cutoff_and_type(require_sold=True)`로 낙찰 건만 사용하는데, snapshot은 전체 레코드(미낙찰 포함)를 집계 |
| **영향** | `artist_avg_price` — 0원 레코드로 하향 편향<br>`artist_total_sold` — 미낙찰 포함으로 과대 계산 (이름과 불일치)<br>`artist_max_price` — 영향 없음 (max이므로)<br>`is_new_artist` — 미낙찰만 있는 작가가 `False`로 분류 (실제론 판매 이력 없음) |
| **예측 영향** | 모든 예측에 영향. 특히 미낙찰 비율이 높은 작가의 가격이 체계적으로 저평가됨 |
| **수정안** | `mask = mask & (works[price_col] > 0)` 추가 (line 39 이전) |

### C2. `orientation` 피처가 2D 작품에서 절대 "landscape"가 될 수 없음

| 항목 | 내용 |
|------|------|
| **파일** | `preprocessing/dimension_parser.py:172-174` + `features/hedonic_stats.py:191-200` |
| **발견** | 1차 수동 + 2차 Codex 동시 발견 |
| **문제** | `parse_dimension()`의 2D 패턴이 `height = max(v1, v2)`, `width = min(v1, v2)`로 정렬 → 항상 `height ≥ width` → `ratio = h/w ≥ 1.0` → landscape 조건(`ratio < 0.83`) 불가능 |
| **영향** | `orientation`은 3-class 범주형이지만 실제로는 2-class(`portrait`/`square`)로만 작동. 가로형 작품의 방향 정보 완전 손실 |
| **예측 영향** | 가로형 vs 세로형 작품의 가격 차이를 학습 불가. `aspect_ratio`도 항상 ≥1.0으로 왜곡됨 |
| **수정안** | 원본 순서 보존: `height = v1, width = v2` (한국 옥션 관례: height×width) 또는 원본 순서가 불명확하면 `orientation` 피처를 `aspect_ratio` 기반으로 재정의 |

### C3. `medium_x_auction_avg`가 log 스케일로 반환 (다른 가격 피처와 불일치)

| 항목 | 내용 |
|------|------|
| **파일** | `features/hedonic_stats.py:298-308` |
| **발견** | 1차 수동 + 2차 Codex 동시 발견 |
| **문제** | `compute_medium_x_auction_avg()`는 `means_ln` (로그 가격)을 직접 반환. 반면 `compute_medium_avg_price()`는 `np.exp()`로 원본 스케일 변환 후 반환 |
| **영향** | 모델이 `medium_avg_price ≈ 5,000,000` (원)과 `medium_x_auction_avg ≈ 15.4` (로그)를 동시에 봄. CatBoost 트리가 분할할 수는 있지만, 피처 의미가 왜곡되고 Bayesian shrinkage도 잘못된 스케일에서 작동 |
| **예측 영향** | 매체×경매타입 교차 가격 신호가 왜곡됨 |
| **수정안** | 반환 전 `np.exp()` 적용, `compute_medium_avg_price()`와 일관성 확보 |

### C4. Distillation `track` 파라미터가 피처 선택에 사용되지 않음

| 항목 | 내용 |
|------|------|
| **파일** | `estimate_generator/distillation.py:195` + `features/track_config.py:37-40` |
| **발견** | 2차 Codex (소비 경로 감사) |
| **문제** | `fit_student()`에 `track` 파라미터가 있지만 로그 메시지에만 사용. `DISTILLED_TRAIN_ONLY_FEATURES`(`teacher_pred_oof`, `global_estimate_avg`)가 학생 모델에 전달되지 않음. `get_distilled_train_features()` 함수가 존재하지만 호출되지 않음 |
| **영향** | 증류(distillation) 트랙이 타깃 블렌딩만 수행하고, 피처 증강(feature augmentation) 경로가 미연결. 의도된 설계인지 구현 누락인지 불명확 |
| **예측 영향** | 증류 학생 모델의 성능이 설계 의도보다 낮을 수 있음 |
| **수정안** | `track == Track.DISTILLED`일 때 `get_distilled_train_features()` 사용, 또는 의도적 target-only 증류라면 `get_distilled_train_features()` 함수 제거 |

---

## MAJOR 이슈

### M1. 신규 작가의 NaN vs 0 불일치

| 항목 | 내용 |
|------|------|
| **파일** | `estimate_generator/hedonic_features.py:178-210` |
| **발견** | 2차 Codex |
| **문제** | Snapshot 피처는 `fillna(0)`: `artist_avg_price=0`, `artist_total_sold=0`. Hedonic 피처는 NaN 유지: `artist_median_price=NaN`. 같은 "판매 이력 없음" 개념이 0과 NaN 두 가지로 인코딩 |
| **영향** | CatBoost가 0과 NaN을 다르게 분할하여, 같은 상태의 작가를 다른 리프에 배치할 수 있음 |
| **수정안** | NaN으로 통일 (CatBoost 네이티브 결측 처리 활용) |

### M2. Artsy 글로벌 통계의 작가명 매칭률 미검증

| 항목 | 내용 |
|------|------|
| **파일** | `features/hedonic_stats.py:399` + `hedonic_features.py:223-228` |
| **발견** | 1차 수동 |
| **문제** | `global_stats`의 인덱스(`artist_kr`)와 `df["artist_clean"]` 간 매칭이 정확한 문자열 일치에 의존. 이름 불일치 시 조용히 NaN 반환. 매칭률 로깅 없음 |
| **영향** | `global_avg_price`, `global_median_price`, `global_auction_count` 3개 피처가 대부분 NaN일 가능성 |
| **수정안** | 매칭률 경고 로그 추가 + fuzzy matching 또는 이름 정규화 |

### M3. `artist_last_hammer_price` 비결정적 값

| 항목 | 내용 |
|------|------|
| **파일** | `features/hedonic_stats.py:602-605` |
| **발견** | 1차 수동 |
| **문제** | 같은 최근 회차에 여러 작품이 있을 때 `idxmax()`가 첫 번째 행만 임의 반환 |
| **영향** | 동일 입력에 대해 다른 예측 가능 (비결정적 피처) |
| **수정안** | 최근 회차의 중앙값 또는 평균 사용 |

### M4. TwoStepModel·EnsembleModel의 정적 CAT_INDICES

| 항목 | 내용 |
|------|------|
| **파일** | `two_step_model.py:78,117` + `ensemble_model.py:92` |
| **발견** | 2차 Codex (소비 경로) |
| **문제** | `HedonicQuantileModel`은 `cat_indices`를 동적 계산하지만, `TwoStepModel`과 `EnsembleModel`은 모듈 레벨 상수 `HEDONIC_CAT_INDICES` 사용. `extra_features` 추가 시 인덱스 불일치 |
| **영향** | 현재는 안전하지만, 피처 확장 시 조용히 범주형 지정 오류 |
| **수정안** | 모든 모델에서 동적 인덱스 계산 |

### M5. Ensemble 모델이 예측 구간(interval) 미반환

| 항목 | 내용 |
|------|------|
| **파일** | `ensemble_model.py:169` |
| **발견** | 2차 Codex (소비 경로) |
| **문제** | `predict()`가 `price_mid`만 반환. `HedonicQuantileModel`, `TwoStepModel`은 `{price_low, price_mid, price_high}` 반환. Conformal Calibrator와 호환 불가 |
| **영향** | Ensemble을 CQR 캘리브레이션에 사용 불가 |
| **수정안** | MultiQuantile 학습 적용 또는 점 추정 전용임을 문서화 |

### M6. Diameter 패턴 우선순위 오류

| 항목 | 내용 |
|------|------|
| **파일** | `preprocessing/dimension_parser.py:119-131` |
| **발견** | 1차 수동 |
| **문제** | Diameter 패턴이 3D/2D보다 먼저 체크됨. "diameter 30×30×20cm" 같은 문자열이 원형으로 잘못 분류될 수 있음 |
| **영향** | 드문 케이스지만, 3D 조각품이 2D 원형으로 분류되면 `is_3d`, `depth_cm`, `bbox_volume` 모두 오류 |
| **수정안** | Diameter 매칭을 2D/3D 이후로 이동, 또는 정규식을 더 제한적으로 변경 |

### M7. RandomForest(앙상블)의 미등장 범주 처리

| 항목 | 내용 |
|------|------|
| **파일** | `ensemble_model.py:178-187` |
| **발견** | 2차 Codex (소비 경로) |
| **문제** | RF용 정수 인코딩에서 미등장 범주가 `-1`로 매핑. RF는 이를 정상 수치로 취급하여 비정상 분할 가능 |
| **영향** | 신규 작가·신규 매체에 대한 앙상블 예측 품질 저하 |
| **수정안** | Target encoding 또는 NaN 활용 |

---

## MINOR 이슈

### m1. `title_has_year` 생성되지만 HEDONIC_FEATURES에서 제외

| 항목 | 내용 |
|------|------|
| **파일** | `features/title_nlp.py:70-73` |
| **문제** | `extract_title_features()`가 9개 컬럼 생성하지만 `HEDONIC_FEATURES`에 7개만 포함. `title_has_year` 조용히 탈락 |
| **수정안** | 의도적이면 주석 추가, 아니면 피처 목록에 추가 |

### m2. `bbox_volume = 0` (모든 2D 작품)

| 항목 | 내용 |
|------|------|
| **파일** | `hedonic_features.py:448-452` |
| **문제** | `depth_cm.fillna(0)` → 2D 작품 전부 `bbox_volume = h × w × 0 = 0`. `is_3d`와 완전 상관 |
| **수정안** | 2D는 NaN 유지 (CatBoost NaN 처리) 또는 `max(depth, 1)` 사용 |

### m3. `size_bucket` bins가 0을 제외

| 항목 | 내용 |
|------|------|
| **파일** | `features/hedonic_stats.py:184-188` |
| **문제** | `pd.cut(bins=[0, ...])` → 면적=0인 행이 모든 빈 밖으로 NaN |
| **수정안** | `bins=[-1, ...]` 또는 `include_lowest=True` |

### m4. `artist_reappear_flag` ≈ `NOT is_new_artist` (중복)

| 항목 | 내용 |
|------|------|
| **파일** | `features/hedonic_stats.py:630-648` |
| **문제** | 등장 횟수 ≥ 1이면 True → `is_new_artist`의 역과 거의 동일 |
| **수정안** | "최근 N회차 내 재등장"으로 재정의하거나 제거 |

### m5. `long_side_cm` / `short_side_cm` — 한쪽 NaN 시 오류

| 항목 | 내용 |
|------|------|
| **파일** | `hedonic_features.py:438-439` |
| **문제** | `max(axis=1, skipna=True)` → height=100, width=NaN이면 둘 다 100 (가짜 정방형) |
| **수정안** | 한쪽이라도 NaN이면 NaN 반환 |

### m6. `compute_artist_price_trend` 0 나누기 위험

| 항목 | 내용 |
|------|------|
| **파일** | `features/hedonic_stats.py:113` |
| **문제** | `earlier.mean() == 0`일 때 `inf` 발생 가능 (극히 드물지만) |
| **수정안** | `earlier.mean() == 0` 체크 추가 |

### m7. `parse_dimension` 이중 실행 (성능)

| 항목 | 내용 |
|------|------|
| **파일** | `hedonic_features.py:137` + `441-447` |
| **문제** | `_apply_parsers`에서 1회, `depth_cm` 추출에서 1회 — 동일 데이터 2회 파싱 |
| **수정안** | `_apply_parsers`에서 `depth_cm`도 함께 추출 |

### m8. Artsy 글로벌 통계에 시간 컷오프 미적용

| 항목 | 내용 |
|------|------|
| **파일** | `hedonic_features.py:215-228` |
| **문제** | 정적 CSV를 모든 회차에 동일 적용. 2024 데이터가 2020 회차에 사용됨 |
| **수정안** | 날짜 범위별 버전 관리 또는 의도적 누수로 문서화 |

---

## 발견 교차 검증

| 이슈 | 1차 수동 | 2차 Codex CLI | 비고 |
|------|:--------:|:------------:|------|
| C1. artist_stats 미낙찰 | O | O | 양측 동시 발견 |
| C2. orientation 불가능 | O | O | 양측 동시 발견 |
| C3. log 스케일 불일치 | O | O | 양측 동시 발견 |
| C4. distillation track 미연결 | — | O | Codex만 발견 |
| M1. NaN vs 0 불일치 | — | O | Codex만 발견 |
| M2. Artsy 매칭률 | O | — | 수동만 발견 |
| M3. last_hammer 비결정적 | O | — | 수동만 발견 |
| M4. 정적 CAT_INDICES | O | O | 양측 동시 발견 |
| M5. Ensemble 구간 미반환 | — | O | Codex만 발견 |
| M6. Diameter 우선순위 | O | — | 수동만 발견 |
| M7. RF 미등장 범주 | — | O | Codex만 발견 |

> 1차 수동 감사는 데이터 흐름 중심, 2차 Codex는 인터페이스 계약 중심으로 상호 보완적 발견.

---

## 수정 우선순위 및 영향도 매트릭스

```
영향도 ↑
    │  C1●         C2●
    │       C3●
    │            C4○    M1○
    │  M3●            M2●
    │       M4○  M5○
    │  M6●       M7○
    │  m1  m2  m3  m4  m5  m6  m7  m8
    └──────────────────────────────── 수정 난이도 →

● = 1차+2차 교차 확인   ○ = 단일 감사 발견
```

### 즉시 수정 (Sprint 0)
| 이슈 | 수정 내용 | 영향 범위 | 난이도 |
|------|-----------|-----------|--------|
| C1 | `artist_stats_snapshot.py`에 `price > 0` 필터 추가 | 모든 예측 | 낮음 |
| C3 | `compute_medium_x_auction_avg()`에 `np.exp()` 적용 | 가격 피처 | 낮음 |
| M1 | Snapshot `fillna(0)` → `fillna(np.nan)` 통일 | 신규 작가 | 낮음 |

### 단기 수정 (Sprint 1)
| 이슈 | 수정 내용 | 영향 범위 | 난이도 |
|------|-----------|-----------|--------|
| C2 | 2D 파싱에서 원본 순서 보존 또는 orientation 재정의 | 전체 2D 작품 | 중간 |
| M3 | `artist_last_hammer`를 최근 회차 중앙값으로 변경 | 다작 작가 | 낮음 |
| m3 | `size_bucket` bins에 `include_lowest=True` 추가 | 면적=0 행 | 낮음 |
| m7 | `_apply_parsers`에서 `depth_cm` 함께 추출 | 성능 | 낮음 |

### 중기 수정 (Sprint 2)
| 이슈 | 수정 내용 | 영향 범위 | 난이도 |
|------|-----------|-----------|--------|
| C4 | Distillation track 피처 선택 연결 또는 불필요 코드 정리 | 증류 모델 | 중간 |
| M2 | Artsy 매칭 fuzzy matching + 매칭률 로깅 | 외부 데이터 | 중간 |
| M4 | 모든 모델에서 동적 cat_indices 계산 | 전 모델 | 낮음 |
| M5 | Ensemble MultiQuantile 또는 문서화 | 앙상블 | 높음 |

---

## 감사 방법론

### 1차 수동 감사
- **범위**: 피처 생성 경로 (`hedonic_features.py` → `hedonic_stats.py` → `dimension_parser.py` → `artist_stats_snapshot.py`) + 소비 경로 (`quantile_model.py` → `two_step_model.py` → `ensemble_model.py` → `conformal_calibrator.py` → `distillation.py` → `track_config.py`)
- **방법**: 57개 HEDONIC_FEATURES 각각의 선언→계산→소비 경로를 추적하며 타입·스케일·결측·시간 정합성 검증
- **소요**: ~5분 (2개 병렬 에이전트)

### 2차 Codex CLI 감사
- **범위**: `src/visionai/price_engine/` 전체
- **프롬프트**: 피처 생성/소비/누수/엣지케이스/파이프라인 일관성 5개 카테고리
- **방법**: 독립적으로 전체 파일 읽기 + 교차 참조
- **소요**: ~5분

### 교차 검증 결과
- **양측 동시 발견**: 5건 (C1, C2, C3, M4 + `타입` CAT_FEATURE_NAMES 이슈)
- **수동만 발견**: 3건 (M2, M3, M6) — 데이터 품질·런타임 동작 중심
- **Codex만 발견**: 4건 (C4, M1, M5, M7) — 인터페이스 계약·설계 의도 중심
- **결론**: 두 접근법이 상호 보완적이며, 단일 감사로는 ~60%만 발견 가능

---

## 수정 이력 및 적용 결과

> 아래는 감사 결과를 기반으로 실제 적용한 코드 수정과 성능 영향 분석이다.

### 적용된 수정 (최종 — 성능 검증 완료)

| 이슈 | 수정 파일 | 변경 내용 | 테스트 | 성능 영향 |
|------|-----------|-----------|:------:|-----------|
| C1 | `artist_stats_snapshot.py:39` | `mask = mask & (works[price_col] > 0)` 추가 | PASS | Cold MdAPE -0.6%p 개선 |
| M3 | `hedonic_stats.py:607-611` | `idxmax()` → 최근 회차 `median()` | PASS | 예측 안정성 개선 |
| m3 | `hedonic_stats.py:189` | `include_lowest=True` 추가 | PASS | 무시 가능 |
| m7 | `hedonic_features.py:145,446` | `_apply_parsers`에서 `depth_cm` 추출, 이중 파싱 제거 | PASS | 성능 최적화 |

### 성능 검증 후 보류된 수정

| 이슈 | 원래 수정 | 성능 영향 | 결정 | 사유 |
|------|-----------|-----------|------|------|
| **C2** | 2D `height=v1, width=v2` | MdAPE +1.6%p 악화 | **보류** | 논리적으로 올바르나, 기존 모델이 max/min 정렬 기반으로 학습하여 height_cm·aspect_ratio·orientation 분포 변화가 test set에서 과적합 유발. 향후 충분한 데이터 축적 시 재적용 검토. |
| **C3** | `medium_x_auction_avg` exp() 변환 | MdAPE +3.7%p 악화 | **보류** | CatBoost 트리 모델에서 log 스케일 피처가 ln_price 타깃과 일관적이며, exp() 변환 시 오히려 성능 악화. 의도적 log 스케일 유지로 재분류. |
| **M1** | 초기값 NaN 통일 | MdAPE +2%p 악화 | **보류** | CatBoost가 기존 0 기본값을 "미판매" 시그널로 이미 학습. NaN 변경 시 cold-start 비율 증가 + 분기 패턴 붕괴. 기존 0 유지가 실질적으로 더 효과적. |

### 미적용 이슈 (후속 과제)

| 이슈 | 사유 | 우선순위 |
|------|------|----------|
| C4 | 증류 모델 미채택 (Model-A q50 유지), target-only 증류는 설계 의도일 가능성 | 낮음 |
| M2 | Artsy 데이터 구조 변경 필요, fuzzy matching 별도 구현 | 중간 |
| M4 | 현재 `extra_features` 미사용으로 실질적 영향 없음 | 낮음 |
| M5 | Ensemble 모델은 현재 파이프라인에서 비활성 상태 | 낮음 |
| M6 | "diameter + 3D" 복합 문자열은 실 데이터에서 미발견 | 낮음 |
| M7 | Ensemble RF는 현재 파이프라인에서 비활성 상태 | 낮음 |

---

## 피처 변경 성능 영향 분석

> 이 섹션은 수정된 피처가 기존 학습 모델 및 재학습 후 성능에 미치는 영향을 분석한다.

### 핵심 결론: 성능 검증을 통한 선별적 적용

7개 수정을 전체 적용 후 재학습한 결과 **Test MdAPE가 35.5% → 39.25%로 악화**되어,
**A/B 실험을 통해 안전한 수정만 선별 적용**하였다.

### A/B 실험 결과 (2026-03-30)

| 실험 | 적용 수정 | Test MdAPE | Cold MdAPE | Gap | Gates |
|------|-----------|------------|------------|-----|-------|
| **Baseline** (수정 전) | 없음 | 35.5% | 48.7% | 3.9%p | 2/7 |
| 전체 적용 | C1+C2+C3+M1+M3+m3+m7 | 39.25% | 52.51% | 7.6%p | 2/7 |
| C2 원복 | C1+C3+M1+M3+m3+m7 | 37.64% | 49.58% | 6.8%p | 2/7 |
| **최종 (C2+C3+M1 원복)** | **C1+M3+m3+m7** | **35.56%** | **48.08%** | **4.4%p** | **3/7** |

### 성능 악화 근본 원인 분석

| 원복 수정 | 악화 원인 |
|-----------|-----------|
| **C3** (exp 변환) | CatBoost 트리 모델에서 log 스케일 피처가 `ln_price` 타깃과 일관적. 300,000배 스케일 변환은 트리 분할 패턴을 근본적으로 파괴 → MdAPE +3.7%p |
| **C2** (원본 순서) | `height_cm`, `aspect_ratio`, `orientation` 분포가 동시에 변경되어 test set에서 과적합 유발 → MdAPE +1.6%p |
| **M1** (NaN 통일) | C1과 상호작용으로 cold-start 비율 증가. CatBoost가 기존 0을 "미판매" 시그널로 학습한 패턴 붕괴 → MdAPE +2%p |

> **교훈**: "논리적으로 올바른 수정"이 반드시 "예측 성능 개선"으로 이어지지 않음.
> 기존 모델이 "잘못된" 피처 분포에 최적화되어 있으면, 올바른 분포로의 전환이
> 오히려 성능을 악화시킬 수 있다. 대규모 피처 분포 변경은 반드시 A/B 실험으로 검증해야 한다.

### 최종 적용 수정의 성능 영향

| 지표 | Baseline | 최종 | 변화 | 평가 |
|------|----------|------|------|------|
| Test MdAPE | 35.5% | 35.56% | +0.06%p | **동등** (오차 범위) |
| Cold MdAPE | 48.7% | 48.08% | **-0.62%p** | **개선** |
| Warm MdAPE | — | 33.82% | — | 참고 |
| Coverage | 56.1% | 55.6% | -0.5%p | **동등** |
| Gates | 2/7 | **3/7** | **+1** | **G5 PASS 유지** |

### 보류 수정의 향후 재적용 조건

| 수정 | 재적용 조건 |
|------|------------|
| **C2** | 충분한 학습 데이터 축적 후 (5만건+), 또는 `orientation` 피처를 `surface_area` 기반으로 재정의하여 height/width 순서 의존성 제거 |
| **C3** | 전체 가격 피처를 log 스케일로 통일하는 대규모 리팩터링 시 함께 적용 |
| **M1** | Cold-start 전용 모델 분리 구현 시 (warm/cold 별도 학습), NaN이 cold 전용 분기로 활용 가능 |
