# Per-source Calibration 재산출 (Phase 2 / decision-binding)

> **작성일**: 2026-05-09
> **분기**: `exp/track1-feature-optimization-cycle`
> **연계**: PR1 (commit `f74f73b`) artifact bundle (no-op calibration) /
> PR2A.5 + PR2B + PR2B-prereq.1/2 (commit `c60708a`)
> **Decision binding**: ✅ YES (artifact 변경 / 다만 default OFF / mode=shadow/canary/on 시만 영향)

## 1. Goal

PR1 산출 시 per-source calibration = **no-op** (모든 cell=1.0 / Phase 2 별도 cycle 영역 의 의무 영역 의 의무 영역 의 의무 deferred). 본 cycle = **per-source 별도 fit**:
- Artsy-only artifact + Artsy-only cross-fit OOF → Artsy cell factors (artsy_gallery / artsy_online)
- Saatchi-only artifact + Saatchi-only cross-fit OOF → Saatchi cell factors (saatchi_online)

## 2. Method (코덱스 사전 자문 + scripts/calibrate_source_bias.py 패턴 정합)

### 2.1 Per-source cross-fit 5-fold protocol

기존 `calibrate_source_bias.py` 영역 의 의무 영역 의 의무 = unified data full / 본 cycle 영역 의 의무 영역 의 의무 = source filter + per-source artifact 영역 의 의무 영역 의 의무.

**Per-source steps**:
1. PR1 artifact load: `source_conditional_v1_<src>_{catboost.cbm, xgboost.json, ...}`
2. Source filter: `df[df["source"] == src]` (Artsy 7,289 / Saatchi 21,087)
3. Cross-fit 5-fold (cold = `GroupKFold-5(artist_slug)` / warm = `KFold-5(random_state=42)` / `_warm_mask` slice)
4. OOF prediction (held-out fold prediction 영역 의 의무 영역 의 의무 누적)
5. Cell factor (per-cell `median(y_actual / y_pred)`):
   - Artsy: `artsy_gallery` (KRW) / `artsy_online` (USD/EUR/GBP/HKD)
   - Saatchi: `saatchi_online` (USD)
6. **Per-cell guard**: cross-fit unguarded MdAPE > baseline MdAPE 영역 의 의무 영역 의 의무 cell → factor=1.0 fallback (regression 방지)

### 2.2 Output (per-source bundle update)

기존 PR1 no-op JSON 영역 의 의무 영역 의 의무 영역 의 의무 = real factors:
```json
{
  "version": "v1-source-conditional-fitted",
  "model_target": "source_conditional_v1_artsy",
  "method": "per-source cross-fit 5-fold + per-cell guard",
  "cold_factors": {"artsy_gallery": <fit>, "artsy_online": <fit>},
  "warm_factors": {"artsy_gallery": <fit>, "artsy_online": <fit>},
  "cold_overall": {"baseline_mdape": ..., "calibrated_mdape_cross_fit_guarded": ...},
  "warm_overall": {...},
  "per_cell_breakdown": {...}
}
```

### 2.3 Provenance regenerate

`<bundle>.provenance.json` sibling = artifact_hashes.main.sha256 update (artifact 영역 의 의무 영역 의 의무 영역 의 의무 변경 / git_commit / timestamp 갱신).

### 2.4 Bundle integrity test update

`tests/price_engine/test_pr2b_bundle_integrity.py::test_source_calibration_no_op_schema` 영역 의 의무 영역 의 의무 = 영역 의 의무 영역 의 의무 영역 의 의무 변경:
- 기존: `all(v == 1.0 for v in cold_factors.values())` (no-op)
- 변경: version="v1-source-conditional-fitted" / cell key 정합 / factor in [0.1, 10.0] (sanity bound) — no-op 영역 의 의무 영역 의 의무 영역 의 의무 X

## 3. Decision Criterion

**채택 (PASS)**:
- ✅ Per-source script `calibrate_source_bias_per_source.py` 신규 / `--source artsy|saatchi` 인자
- ✅ Bundle update (no-op → real factors / version 변경)
- ✅ Provenance regenerate
- ✅ Bundle integrity test update (fitted factors 정합)
- ✅ ruff Python clean
- ✅ All tests PASS (전체 회귀)

**비채택 (FAIL)**:
- ❌ Per-source filter 누락 (unified full-data 사용)
- ❌ Per-cell guard 누락
- ❌ regression cell (calibrated MdAPE > baseline) → factor=1.0 fallback X

## 4. Out-of-scope

❌ **운영 unified `integrated_v3_filtered_tuned_source_calibration.json` 변경** — 본 cycle scope X (운영 default OFF 영역 의 의무 영역 의 의무 동일).
❌ **재현성 검증** (또 다른 fresh holdout / 별도 cycle).
❌ **Per-source HP tuning** (Phase 3 / Optuna / 별도 cycle).

## 5. 한계 / Risk

- **Artsy 7,289 rows = 작은 샘플**: cross-fit 5-fold (1,458 OOF / fold) / cell factor 분산 가능
- **Saatchi 21,087 rows = saatchi_online 단일 cell**: cell factor 단일 / per-cell guard 영역 의 의무 영역 의 의무 영역 의 의무 = 단일 영역 의 의무 영역 의 의무 영역 의 의무
- **Per-cell regression**: 작은 샘플 영역 의 의무 영역 의 의무 영역 의 의무 cross-fit MdAPE > baseline 가능 → factor=1.0 fallback (regression 방지)

## 6. 코덱스 자문 이력

| round | verdict |
|---|---|
| 1차 사전 자문 | NEEDS FIX (P1: 구현 X) — 본 round 영역 의 의무 영역 의 의무 = 구현 단계 / 디자인 정합 |
| 2차 사후 검수 (예정) | bundle update + provenance regenerate + tests pass 후 |
