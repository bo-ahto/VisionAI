# Operational Adoption Cycle — Source-conditional Artifact Retrain (PR1 only)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle` (artifact retrain branch / 별도 PR1)
> **연계**:
> - `docs/source_conditional_prereg_20260509.md` (CHAMPION verdict)
> - `experiments/track1_optimization/source_conditional/SOURCE_CONDITIONAL_REPORT.md`
>
> **Decision binding**: ✅ **YES** (artifact 영역 의 의무 영역 의 의무 변경)
>
> ⚠️ **본 cycle scope**: **PR1 만** (artifact retrain + sha256 freeze).
> PR2 (inference pipeline 변경 / routing / tests) = **별도 cycle / 별도 prereg** (코덱스 권고 영역 의 의무 영역 의 의무 정합).

## 1. Goal

Source-conditional CHAMPION verdict 영역 의 의무 영역 의 의무 영역 의 의무 운영 적용 1단계 = **per-source artifact 산출** (전체 데이터 retrain).

PR1 deliverables:
1. Artsy-only Ensemble artifact (CatBoost + XGBoost / 운영 best_params 고정)
2. Saatchi-only Ensemble artifact (CatBoost + XGBoost / 운영 best_params 고정)
3. SHA-256 freeze + provenance.json
4. **PR2 (다음 cycle)** = inference pipeline 변경 / routing / fallback / tests

## 2. Method (코덱스 사전 자문 P1 fix 적용)

### 2.1 Data scale (정확 표현 / P1 fix)

운영 학습 anchor:
- **Raw**: 29,361 rows (Artsy 7,640 + Saatchi 21,721)
- **Filtered** (`is_excluded_for_training == 0` / 운영 anchor): **28,376 rows**
  - **Artsy: 7,289** (filtered)
  - **Saatchi: 21,087** (filtered)
  - 985 rows excluded (data quality / training filter)

⚠️ 본 cycle 영역 의 의무 영역 의 의무 = **filtered 28,376** retrain (raw 29,361 X / 운영 정합 영역 의 의무 영역 의 의무).

### 2.2 Artifact retrain protocol (locked)

**Per-source separate retrain**:
1. **Artsy-only Ensemble**:
   - Data: 7,289 rows (filtered)
   - CatBoost: 운영 best_params 고정 (iter=1000 / depth=8 / lr=0.0953 / l2=1.63 / bagging=0.18)
   - XGBoost: 운영 best_params 고정 (round=3000 / depth=7 / lr=0.0401 / 등)
   - Loss: RMSE / target = ln_price / random_seed=42
2. **Saatchi-only Ensemble**:
   - Data: 21,087 rows (filtered)
   - 동일 best_params + random_seed=42
3. **HP re-tune ❌** / Top N feature selection ❌ / 32 features 영역 의 의무 영역 의 의무 영역 의 의무 (CB_FEATURES_BASE / 운영 정합).

### 2.3 Artifact 산출 (locked / 새 prefix / runtime-compatible bundle)

⚠️ **코덱스 round 2 P1 fix**: 운영 loader 영역 의 의무 영역 의 의무 = `<prefix>_warm_artists.json` + `<prefix>_source_calibration.json` 의무 (`primary_predictor.py:209,231,300+`). PR2 영역 의 의무 영역 의 의무 영역 의 의무 = bundle contract 영역 의 의무 영역 의 의무 정합 의무.

Per-source bundle (새 prefix `source_conditional_v1_<src>`):

```
model_test_results/
├── source_conditional_v1_artsy_catboost.cbm
├── source_conditional_v1_artsy_xgboost.json
├── source_conditional_v1_artsy_xgboost_label_maps.json
├── source_conditional_v1_artsy_metrics.json
├── source_conditional_v1_artsy_warm_artists.json         # P1 fix (loader 의무)
├── source_conditional_v1_artsy_source_calibration.json   # P1 fix (정확 파일명 / no-op schema)
├── source_conditional_v1_artsy_catboost.cbm.provenance.json   # helper 규약
├── source_conditional_v1_artsy_xgboost.json.provenance.json
├── source_conditional_v1_saatchi_catboost.cbm
├── source_conditional_v1_saatchi_xgboost.json
├── source_conditional_v1_saatchi_xgboost_label_maps.json
├── source_conditional_v1_saatchi_metrics.json
├── source_conditional_v1_saatchi_warm_artists.json
├── source_conditional_v1_saatchi_source_calibration.json
├── source_conditional_v1_saatchi_catboost.cbm.provenance.json
└── source_conditional_v1_saatchi_xgboost.json.provenance.json
```

### 2.4 Calibration (no-op / runtime schema 정합 / P1 fix)

⚠️ **운영 unified `source_calibration.json` 재사용 X** (코덱스 round 1 P1 / unified residual 기준 fit / per-source 부정합).

Per-source no-op calibration JSON (loader schema 정합 / round 2 P1 fix):

```json
{
  "version": "v1-source-conditional-noop",
  "model_target": "source_conditional_v1_artsy",
  "method": "no-op identity (Phase 2 cycle 영역 의 의무 영역 의 의무 재산출)",
  "cold_factors": {
    "artsy_gallery": 1.0,
    "artsy_online": 1.0
  },
  "warm_factors": {
    "artsy_gallery": 1.0,
    "artsy_online": 1.0
  }
}
```

(Saatchi bundle 동일 / cells = `{"saatchi_online": 1.0}`)

→ **Phase 2 별도 cycle** (별도 prereg): per-source calibration 재산출 (Artsy / Saatchi 별도 source-cell calibration).

### 2.4.1 Warm artists (P1 fix / 코덱스 round 3)

⚠️ 운영 영역 의 의무 영역 의 의무 영역 의 의무 = global warm set (source 무관 / 작품수 ≥ 5). Per-source bundle 영역 의 의무 영역 의 의무 영역 의 의무 = source 별 영역 의 의무 영역 의 의무:

- **Artsy bundle warm_artists.json**: source==artsy AND artist 작품수 ≥ 5 영역 의 의무 영역 의 의무 artist_slug set (filtered 7,289 영역 의 의무 영역 의 의무)
- **Saatchi bundle warm_artists.json**: source==saatchi AND ≥ 5 (filtered 21,087)
- 산출 schema (운영 정합):
  ```json
  {
    "warm_artist_slugs": [...],
    "n_artists": ...,
    "n_warm_works": ...,
    "min_count": 5,
    "source": "artsy",
    "note": "source-conditional v1 / source-별 분리 / 작품수 ≥ 5"
  }
  ```

### 2.4.2 Per-artifact provenance (P1 fix / 코덱스 round 3)

⚠️ helper 규약 (`_provenance.py:214`): `<artifact>.provenance.json` sibling.

Per-bundle provenance:
- `source_conditional_v1_artsy_catboost.cbm.provenance.json`
- `source_conditional_v1_artsy_xgboost.json.provenance.json`
- `source_conditional_v1_saatchi_catboost.cbm.provenance.json`
- `source_conditional_v1_saatchi_xgboost.json.provenance.json`
- `source_conditional_v1_<src>_source_calibration.provenance.json` (calibration script 영역 의 의무 영역 의 의무 정합)

각 provenance schema (helper 규약):
```json
{
  "model_target": "source_conditional_v1_artsy",
  "data_paths": {...},
  "git_commit": "...",
  "artifact_hashes": {"main": {"path": "...", "sha256": "...", "exists": true}},
  "timestamp": "2026-05-09T..."
}
```

### 2.4.3 No-op calibration schema (P1 fix / 코덱스 round 3)

운영 schema (loader 정합 / `primary_predictor.py:325-340`):
- 의무: `version` / `model_target` / `cold_factors` (dict / cell-keyed)
- 본 cycle 영역 의 의무 영역 의 의무 = **모든 cold_factors / warm_factors = 1.0** (no-op identity):

```json
{
  "version": "v1-source-conditional-noop",
  "model_target": "source_conditional_v1_artsy",
  "method": "no-op identity (Phase 2 cycle 별도 prereg 영역 의 의무 영역 의 의무 재산출)",
  "cold_factors": {
    "artsy_gallery": 1.0,
    "artsy_online": 1.0
  },
  "warm_factors": {
    "artsy_gallery": 1.0,
    "artsy_online": 1.0
  }
}
```

Saatchi bundle 영역 의 의무 영역 의 의무 = `cold_factors / warm_factors = {"saatchi_online": 1.0}`.

### 2.5 Sanity check (운영 회귀 / non-binding)

본 cycle 영역 의 의무 영역 의 의무 영역 의 의무 = artifact 산출 후 sanity inference test:
- Artsy artifact 영역 의 의무 영역 의 의무 영역 의 의무 dummy input → output (NaN / inf X)
- Saatchi artifact 영역 의 의무 영역 의 의무 영역 의 의무 dummy input → output

⚠️ 전면 운영 회귀 테스트 = PR2 영역 의 의무 영역 의 의무 영역 의 의무.

## 3. Out-of-scope (PR2 / 다음 cycle)

❌ **본 cycle scope X**:
- inference pipeline 변경 (primary_predictor.py / primary_server.py)
- Source routing logic + fallback (unknown source → unified)
- 운영 회귀 테스트 (matched / unknown / batch)
- Per-source calibration 재산출 (Phase 2 별도 prereg)
- Per-source HP tuning (Phase 3 별도 prereg)
- Re-test (또 다른 fresh holdout / 재현성)

## 4. Decision Criterion (locked)

**채택 (PASS)**:
- ✅ Artifact 산출 정상 (Artsy + Saatchi / sha-256 freeze 정합)
- ✅ Per-source dummy inference sanity (NaN / inf 영역 의 의무 영역 의 의무 X)
- ✅ provenance.json 영역 의 의무 영역 의 의무 정확 (data scale / best_params / random_seed)
- ✅ no-op calibration JSON 영역 의 의무 영역 의 의무 정합

**비채택 (FAIL)**:
- ❌ Artifact 산출 실패 / inference NaN / sha-256 mismatch / provenance 영역 의 의무 영역 의 의무 잘못

## 5. Serving contract 영역 의 의무 영역 의 의무 영역 의 의무 (P1 fix / PR2 영역 의 의무 영역 의 의무)

⚠️ **운영 predictor 영역 의 의무 영역 의 의무 영역 의 의무 = warm: XGBoost / cold: CatBoost** (별도 라우팅 / `primary_predictor.py:177` 영역 의 의무 영역 의 의무).

⚠️ **SourceCond 평가 영역 의 의무 영역 의 의무 영역 의 의무 = Ensemble (CB+XGB)** (per-source / 평가 경로 영역 의 의무 영역 의 의무 영역 의 의무 영역).

⚠️ **PR2 결정 의무**:
- 옵션 A (강함): per-source Ensemble serving (warm/cold 영역 의 의무 영역 의 의무 영역 의 의무 변경 / SourceCond CHAMPION 평가 정합)
- 옵션 B (약함): per-source warm=XGBoost / cold=CatBoost (운영 정합 / 다만 평가 vs 서빙 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무 영역 의 의무)
- → **PR2 별도 prereg 영역 의 의무 영역 의 의무 결정**.

본 cycle (PR1) 영역 의 의무 영역 의 의무 영역 의 의무 = **artifact만 산출** (CB + XGB 별도 / Ensemble 영역 의 의무 영역 의 의무 영역 의 의무 PR2 영역 의 의무 영역 의 의무).

## 6. 진행 일정

| 단계 | 영역 | 시간 |
|---|---|---:|
| prereg doc + 코덱스 round 1 fix | 본 doc | 0.5 시간 |
| 코덱스 round 2 사전 자문 | 본 fix 검수 | 0.5 |
| Artifact retrain script | per-source / 전체 데이터 | 0.5 |
| Background run | 2 retrain × ~10분 | ~20분 |
| sha-256 freeze + provenance | | 0.5 |
| 코덱스 사후 검수 | round 3 | 0.5 |
| commit + PR1 | | 0.5 |
| **합계** | — | **~3 시간** |

## 7. 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P1: 평가/서빙 경로 + calibration unified 재사용 + 데이터 규모) → fix |
| 2차 사전 자문 (예정) | 본 fix commit 직후 |
| 3차 사후 검수 (예정) | Artifact 산출 후 |
