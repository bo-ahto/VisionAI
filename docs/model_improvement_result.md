# 모델 구조 개선 + 크기 결측 해결 결과 보고서

> **작성일**: 2026-03-31
> **변경**: 크기 결측 50%→2% + 피처 57→50개 정리 + 3개 모델 비교(Model-A, TwoStep, Ensemble)

---

## 1. 적용된 개선 사항

### 1.1 데이터 품질 (크기 결측 해결)

| 경매사 | 이전 결측률 | 현재 결측률 | 해결 방법 |
|--------|:---------:|:---------:|-----------|
| 케이옥션 | 7% | 1% | 기존 |
| 서울옥션 | **86%** | **2%** | k-artmarket `width`/`height` 수치 컬럼 활용 |
| 아이옥션 | **92%** | **4%** | 동일 |
| 에이옥션 | **100%** | **1%** | 동일 |
| 라이즈아트 | **100%** | **0%** | 동일 |
| **전체** | **~50%** | **~2%** | `data_schema.py` 수정 |

### 1.2 피처 정리 (57 → 50개)

**제거 9개**: `source_type`(상수), `size_ho`/`size_ho_above40`(폐기), `auction_type_factor`(의미 변질), `medium_x_auction_avg`(희소), `artist_premium_ratio`("메이저" 하드코딩), `artist_reappear_flag`(공선성), `global_avg_price`(공선성), `comp_match_level`(중복)

**추가 2개**: `source_count`(작가 경매사 수), `sale_month`(계절성)

### 1.3 모델 구조 개선

| 모델 | 구조 | 상태 |
|------|------|------|
| **Model-A** | CatBoost MultiQuantile (q25/q50/q75) + CQR | 기존 유지 |
| **TwoStep** | 5-bin 가격 분류 → 구간별 전문 CatBoost | 3-bin → 5-bin 확장 |
| **Ensemble** | CatBoost + LightGBM → Ridge 메타 (분위수별) | RF 제거, LightGBM 추가 |

---

## 2. 학습 결과 — 3개 모델 비교

| 모델 | Test MdAPE | Valid MdAPE | Gap | R² |
|------|:----------:|:-----------:|:---:|:--:|
| **Ensemble** | **48.31%** | 45.99% | 2.33%p | **0.383** |
| Model-A | 49.31% | — | — | — |
| TwoStep | 52.43% | — | — | — |

**Ensemble이 최적** — CatBoost + LightGBM 다양성 효과로 Model-A 대비 1%p 개선.
> **참고**: Ensemble은 CQR 미적용으로 서빙 불가. 현재 서빙 모델은 Model-A. P0(CQR 적용) 완료 후 Ensemble로 전환.

### 이전 대비 성과

| 지표 | 크기 결측 50% (이전) | 크기 결측 2% + 모델 개선 (현재) | 변화 |
|------|:-------------------:|:----------------------------:|------|
| **Test MdAPE** | 52.73% | **48.31%** | **-4.42%p** |
| **R²** | 0.343 | **0.383** | **+0.040** |
| **W30** | 31.0% | **33.1%** | **+2.1%p** |
| **Cold MdAPE** | 67.55% | **63.45%** | **-4.1%p** |
| **Gap** | 0.75%p | **2.33%p** | +1.58%p |
| **Best Model** | Model-A | **Ensemble** | 신규 |

---

## 3. 분석

### 3.1 크기 결측 해결 효과

50% → 2% 결측 해결이 가장 큰 개선 요인. 11개 크기 관련 피처(`height_cm`, `width_cm`, `surface_area`, `aspect_ratio`, `estimated_ho`, `ln_surface_area`, `size_bucket`, `orientation`, `long_side_cm`, `short_side_cm`, `is_size_imputed`)가 전체 데이터에서 유효해짐.

### 3.2 앙상블 효과

CatBoost + LightGBM은 서로 다른 트리 구축 전략(CatBoost: ordered boosting, LightGBM: leaf-wise)으로 다양성 확보. Ridge 메타 학습기가 분위수별 독립 스태킹으로 두 모델의 강점을 결합.

### 3.3 TwoStep 저조 원인

5-bin 분류 정확도가 낮아 잘못된 구간에 배정된 작품의 오차가 누적됨. 다중 출처 데이터에서 가격 분포가 이질적이라 고정 경계(1M/5M/20M/100M)가 적합하지 않음. 향후 동적 경계 또는 소프트 라우팅 적용 시 개선 가능.

### 3.4 Coverage — CQR 적용으로 해결

초기 Ensemble Coverage 5.7% → **CQR 적용 후 58.3%** (G5 PASS).
각 모델에 독립 CQR 캘리브레이터를 적용하여 해결.

---

## 4. 남은 과제

| 우선순위 | 작업 | 예상 효과 |
|----------|------|-----------|
| ~~P0~~ | ~~Ensemble에 CQR 캘리브레이션 적용~~ | **완료** — 58.3% |
| P1 | 작가×매체 조건부 크기 대체 (잔여 2% 개선) | MdAPE -0.5%p |
| P1 | artist_unsold_rate 복구 | MdAPE -1~2%p |
| P2 | 작가 프로필 수집 (KAWF 공공데이터) | Cold MdAPE -3~5%p |
| P2 | TwoStep 소프트 라우팅 | MdAPE -2~3%p |
| P3 | 이미지 피처 (ResNet 임베딩) | Cold MdAPE -10~15%p |

---

## 5. 기술 상세

### 변경된 파일

| 파일 | 변경 |
|------|------|
| `preprocessing/data_schema.py` | k-artmarket `width`/`height` → `size_raw` 통합 |
| `estimate_generator/hedonic_features.py` | HEDONIC_FEATURES 50개, 월 단위 윈도우 최적화 |
| `estimate_generator/two_step_model.py` | 5-bin 확장, price_col 자동 감지 |
| `estimate_generator/ensemble_model.py` | CatBoost+LightGBM, 분위수별 Ridge 메타 |
| `scripts/train_phase5_final.py` | 3개 모델 비교 학습, 피처 캐시 |

### 모델 아티팩트

| 파일 | 설명 |
|------|------|
| `model_a_quantile.cbm` | CatBoost MultiQuantile |
| `conformal_calibrator.pkl` | CQR alpha=0.38 (Model-A용) |
| `hedonic_features_cache.parquet` | 피처 캐시 (재학습 5분) |
| `phase5_final_metrics.json` | 3개 모델 성능 비교 |
