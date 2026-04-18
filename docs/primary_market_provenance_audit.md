# 1차 시장 모델 Provenance Audit

> **작성일**: 2026-04-18
> **목적**: 배포된 1차 시장(Primary Market) 예측 모델(A)의 아티팩트·메트릭·학습 경로 출처를 repo 증거로 고정한다.
> **범위**: 모델 family **A (1차 시장)** 전용. 경매 낙찰가 모델(B)은 별도 문서.
> **주의**: 본 문서는 **기록 정리(provenance audit)** 이며 새 실험을 수행하지 않는다. 모든 수치는 기존 JSON/코드에서 인용.

---

## 1. 배포 아티팩트 경로

| 단계 | 파일 | 위치 증거 |
|---|---|---|
| 빌드 (Dockerfile) | `integrated_v3_catboost.cbm` (6.15 MB) | `Dockerfile.api:13` `COPY model_test_results/integrated_v3_catboost.cbm ./models/...` |
| 빌드 (Dockerfile) | `integrated_v3_xgboost.json` (9.88 MB) | `Dockerfile.api:14` |
| 런타임 로드 | `primary_predictor.load_models(model_dir)` | `src/visionai/price_engine/api/primary_predictor.py:66-75` |
| 파일 시스템 mtime | 2026-04-17 14:08 | `ls -la model_test_results/integrated_v3_*` |
| Git 추가 시점 | `39f7e6e Add v3 model files for API deployment` (2026-04-16 16:39 KST) | `git log 39f7e6e` |
| 서빙 엔트리 | `primary_server.py`, port 8000, endpoint `/api/v1/predict` | `src/visionai/price_engine/api/primary_server.py:443` `FastAPI(...)` |
| 배포 도메인 | `visionai-api.ahto.city` | `docs/project_status_20260417.md` |

---

## 2. 피처셋 (CB_FEATURES 37개)

근거: `src/visionai/price_engine/api/primary_predictor.py:22-39`

**수치형 (30개)**:
`ho, ho_power, ln_ho, area_cm2, ln_area, aspect_ratio, is_small, support_factor, ho_x_support, is_unique, is_edition, work_age, has_depth, artist_birth_year, has_birth_year, career_age, career_stage, ln_followers, artist_total_works, for_sale_ratio, ho_price_level, medium_price_level, profile_completeness, gallery_tier, gallery_city_count, has_seoul, has_international, is_krw, vintage_premium, freshness_discount`

**범주형 (7개, CAT_FEATURES)**:
`support_type, medium_category, attribution_class, gallery_name, gallery_type, price_currency, source`

**중요**: 이 37개 피처는 경매 낙찰가 모델(B)의 `HEDONIC_FEATURES` 46개와 **완전히 다른 리스트**다. 공유되는 이름은 일부(`artist_birth_year`, `medium_category`)지만 A의 피처 빌더(`primary_feature_builder.build_features`)는 B의 `estimate_generator` 모듈을 **사용하지 않는다** (A 빌더 import: `math`, `re`, `numpy`만).

**예외**: `scripts/predict_primary_market.py:25-30` 은 A 문맥의 보조 스크립트인데 B 모듈(`estimate_generator.hedonic_features`, `estimate_generator.market_rounder`) 및 공용 전처리 모듈(`preprocessing.medium_parser`)을 import한다. `medium_parser`는 A/B 모두에서 쓰일 수 있는 공용 모듈이고, `hedonic_features`/`market_rounder`는 B 소속이다. 이 스크립트는 "A 작품을 경매 스타일로 재해석하는 ad-hoc 예측 실행기"라 **배포 서빙 경로(Dockerfile.api + primary_server)와는 무관**하다.

---

## 3. 성능 메트릭 (근거: `model_test_results/integrated_v3_metrics.json`)

**데이터 구성**:
- 총 29,361건 = Artsy+Artue 7,640 + Saatchi 21,721 (근거: `integrated_v3_metrics.json` `data` 필드)
- 작가 1,589명 (근거: **`integrated_v3_metrics.json`에는 기록 없음**, API `primary_server.py:494` 하드코딩 값)

**GroupKFold (Cold Start, 새 작가 기준)**:

| 모델 | MdAPE | W30 | W50 | ratio |
|---|---|---|---|---|
| Baseline | 43.8% | 35.7% | 55.1% | 1.04 |
| CatBoost v3 | 38.9% | 39.9% | 61.1% | 1.07 |
| XGBoost v3 | 39.4% | 40.1% | 59.4% | 1.06 |
| **Ensemble** | **38.7%** | **40.1%** | **60.6%** | **1.07** |

**GroupKFold — Artsy 서브샘플 (n=7,640)**:
- Ensemble MdAPE **31.6%**, W30 47.6%, W50 70.1%

**GroupKFold — Saatchi 서브샘플 (n=21,721)**:
- Ensemble MdAPE **42.3%**, W30 37.4%, W50 57.2%

**KFold (이미 학습된 작가의 새 작품)**:

| 모델 | MdAPE | W30 | W50 |
|---|---|---|---|
| **XGBoost v3** | **11.7%** | **78.8%** | **90.5%** |
| Ensemble | 13.8% | 75.6% | 89.1% |
| CatBoost v3 | 17.1% | 70.1% | 86.2% |

**⚠ 주의**:
- 위 수치는 2026-04-16~17 사이 어느 시점에 생성된 `integrated_v3_metrics.json`의 기록을 인용한 것이다. 본 audit은 측정을 다시 수행하지 않는다.
- KFold는 fold 내에 같은 작가의 다른 작품이 섞이는 환경이라 production cold start 경우와 다르다.
- 서비스가 받을 실제 쿼리 분포와 학습 분포가 다를 수 있다 (Artsy/Saatchi 비율 등).

---

## 4. API `/api/v1/model/info` 응답

근거: `primary_server.py:489-498`

```json
{
  "model_version": "v3",
  "training_count": 29361,
  "artist_count": 1589,
  "mdape_groupkfold": 38.7,
  "mdape_kfold": 11.7,
  "features_count": 37
}
```

**⚠ 주의**: 이 값들은 **하드코딩**. 모델이 변경되면 서버 코드도 수동 갱신 필요. 현재 코드 기준 값은 `integrated_v3_metrics.json` ensemble/xgboost 결과와 일치.

---

## 5. 학습 스크립트 (gap)

**Repo 증거만으로는 학습 스크립트 확정 불가.**

- `scripts/` 에서 `integrated_v3_catboost.cbm` / `integrated_v3_xgboost.json` 을 **생성(write)** 하는 파일이 발견되지 않음
- `scripts/train_phase5_v3.py` 는 이름은 비슷하나 HedonicQuantileModel(`model_a_quantile.cbm`)을 저장하는 **경매 낙찰가 모델(B)** 스크립트
- `scripts/train_phase5_v2.py`, `train_phase5_integrated.py`, `train_phase5_with_profiles.py` 등도 B 쪽
- git 추가 커밋 `39f7e6e Add v3 model files for API deployment` 은 아티팩트만 추가, 생성 스크립트는 포함하지 않음

**결론**: 현재 repo에는 1차 시장 모델 **재학습을 자동 재현할 수 있는 파이프라인 스크립트가 없다**. 이는 운영 위험 — 모델 업데이트 시 외부 환경(로컬 notebook 등)에 의존해야 한다. **Follow-up 과제**로 기록.

---

## 6. 이전 버전 아티팩트 (참고)

| 버전 | 메트릭 파일 | 비고 |
|---|---|---|
| v2 | `integrated_v2_metrics.json` | "integrated_v2_catboost (Artsy+Artue+Saatchi)" |
| **v3 (배포)** | **`integrated_v3_metrics.json`** | **현재 서비스 중** |
| v4 | `integrated_v4_metrics.json` | 미배포 반복 버전 (피처 확장 시도) |
| v5 | `integrated_v5_metrics.json` | 미배포 반복 버전 |
| v6 | `integrated_v6_metrics.json` | 미배포 반복 버전 |

**Baseline 백업 (`model_test_results/baseline_pre_retrain_20260417/`)** — 2026-04-17 stash 전 상태 부분 보존. `ls` 기준 실존 파일:

- v2: `integrated_v2_catboost.cbm`, `integrated_v2_metrics.json` (xgboost 없음)
- v3: `integrated_v3_catboost.cbm`, `integrated_v3_xgboost.json`, `integrated_v3_metrics.json`
- v4: `integrated_v4_catboost.cbm`, `integrated_v4_xgboost.json`, `integrated_v4_metrics.json`
- v5: `integrated_v5_xgboost.json`, `integrated_v5_metrics.json` (catboost 없음)
- v6: `integrated_v6_metrics.json` (cbm/xgb 없음)

즉 v2/v5/v6 는 일부 아티팩트 누락 상태로 백업됨. **"v2~v5 전체 복사본"은 사실과 다름** — 부분 백업.

---

## 7. Follow-up 과제

1. **학습 스크립트 공개** — 현재 gap. `scripts/train_integrated_v3.py` (가칭) 추가해서 재학습 재현성 확보.
2. **`model_info` 하드코딩 해소** — `integrated_v3_metrics.json` 읽어 동적 반환.
3. **Smoke test 정기화** — 배포된 모델 응답을 주기적으로 확인하는 간단한 regression test.
4. **버전 관리 체계** — `model_test_results/integrated_v{n}_*` 파일명 외에 명시적 registry 고려.

---

## 8. 요약

- **배포된 1차 시장 모델은 v3**, 29,361건 학습, 1,589 작가, 37 피처, CatBoost+XGBoost 라우팅.
- **주요 성능**: GroupKFold Ensemble 38.7% MdAPE (Cold Start), KFold XGBoost 11.7% (학습 작가).
- **서빙 경로는 A 전용**: `primary_server` + `primary_predictor` + `primary_feature_builder` + `integrated_v3_*` 아티팩트.
- **최근 경매 모델(B) refactor는 이 경로에 영향 없음**.
- **Follow-up 필요**: 학습 스크립트 재현성, model_info 동적화.
