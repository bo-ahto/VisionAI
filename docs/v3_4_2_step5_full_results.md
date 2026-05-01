# v3.4-2 step 5 ablation FULL 결과 + 코덱스 권장 채택안

작성일: 2026-05-02
배경: step 4 saatchi 21,087 enrichment (97.90% fill) → step 5 ablation (V0 / V_year_only / V_full).
설정: n_splits=5, CB iter=1000, XGB iter=3000, n_boot=10K, artist-cluster bootstrap CI95.

---

## 1. 결과 — 전체 + cohort breakdown

### 1.1 Variant 별 MdAPE

| Variant | overall | cold (1,314) | cold_le2 (571) | warm_5_9 (2,114) | saatchi_online (21,087) |
|---------|--------:|-------------:|---------------:|-----------------:|------------------------:|
| V0 | 10.358% | 42.575% | 39.462% | 17.150% | 10.668% |
| **V_year_only** | **9.619%** (Δ-0.74) | 43.570% (Δ+0.99) | 41.644% (Δ+2.18) | 16.881% (Δ-0.27) | 9.626% (Δ-1.04) |
| V_full | 9.610% (Δ-0.75) | 43.660% (Δ+1.09) | 42.439% (Δ+2.98) | 17.172% (Δ+0.02) | 9.625% (Δ-1.04) |

### 1.2 saatchi_online × work_count bucket

| Bucket | n | V0 | V_year_only Δ | V_full Δ |
|--------|--:|---:|--------------:|---------:|
| 1-2 | 243 | 46.95% | +0.34% | -0.12% |
| 3-4 | 385 | 47.65% | -0.55% | **-2.54%** |
| 5-9 | 1,036 | 19.56% | -0.40% | +0.33% |
| **10+** | **19,423** | 9.90% | **-0.98%** | **-1.03%** |

### 1.3 Paired comparisons (artist-cluster bootstrap CI95 — primary)

| 비교 | Δ overall | CI95 | excludes_zero | Wilcoxon row p (보조) | Wilcoxon artist p (cluster-aware) |
|------|----------:|-----:|:-------------:|----------------------:|----------------------------------:|
| V_year_only vs V0 | -0.739% | **[-1.144, -0.324]** | **TRUE** | 2.6e-55 | **0.018** |
| V_full vs V0 | -0.747% | **[-1.169, -0.349]** | **TRUE** | 6.4e-51 | **0.034** |
| V_full vs V_year_only | -0.009% | (잡음 수준) | False | high | high |

---

## 2. 핵심 finding (smoke 와 정반대 패턴)

1. **overall 통계 유의 개선**: V_year_only Δ-0.74%p, CI 0 미포함, artist-level p=0.018
2. **개선 main source = saatchi_online 10+ warm 작가** (n=19,423, Δ-0.98 ~ -1.03%p)
3. **cold cohort 는 worse**: V_year +0.99%p, V_full +1.09%p — year_made 가 sparse cohort 에서 spurious / overfit
4. **cold_le2 (n=571) 는 가장 worse** (+2.18 ~ +2.98%p) — "low support 본질은 데이터 부족, 라벨/feature 만으로 해결 X" (코덱스 v3.3-2 가설 일관)
5. **V_full vs V_year_only overall 차이 무** (-0.009%, CI 0 포함)
6. **smoke 결론은 misleading 했음**: smoke (CB 100 iter underfit) 에선 cold 가 도움처럼 보였으나 full (CB 1000 iter 충분 학습) 에서 spurious 노출

---

## 3. 코덱스 최종 권장 (P0)

### 3.1 채택 결정
> **V_year_only 채택**, **cold cohort 에서는 year_made 비활성**.
> V_full 은 backlog 후보 (이번 라운드 deploy 대상 X).

이유:
- V_full 의 overall 이득은 사실상 동일 (Δ-0.009%)
- V_full 이 cold/cold_le2 손실 더 큼 (+1.09 vs +0.99 / +2.98 vs +2.18)
- saatchi_online 3-4 의 V_full -2.54%p 는 n=385 로 재현성 불충분

### 3.2 cold cohort 보호장치 (1순위 ~ 2순위)
1. **Saatchi-conditional feature**: saatchi row 만 year_made 사용. 비-saatchi/cold = NaN/disabled.
2. **서빙 라우팅 cold gating**: cold artist 는 year_made 무시 강제 (has_year_made=0 처리).

→ overall 유의 개선은 saatchi_online 10+ (n=19,423) 가 이끔. global on 보다 **cohort-gated on** 이 맞음.

### 3.3 Framing
> 이번 실험은 year_made 를 전체에 켜는 근거가 아니라, **saatchi warm 대형 cohort 에 선택적으로 켜면 overall 약 -0.74%p, saatchi 약 -1.0%p 개선을 기대할 수 있다는 근거**다.

---

## 4. v3.5 backlog (코덱스 권장 4-step)

1. **V_year_only + cohort gating 오프라인 검증** — saatchi-only 또는 warm-only conditional feature 변형 ablation
2. **Production feature availability 정리** — `external_collector.py` 가 작품 year_made 미수집. saatchi 만 detail page enrichment 가능 (코덱스 v3.4-1 검증)
3. **`external_collector.py` enrichment/latency/coverage 검토** — 추가 ~0.6-1 sec/req latency vs -0.74%p ROI trade-off
4. **Gated rollout 전후 drift 모니터링 설계** — has_year_made flag 활성률 / 비활성 cold 의 grade margin 변화 등

---

## 5. Train/Serve drift caveat (그대로)

- 현재 production scrape 는 작품 year_made/year_created 미수집 (`src/visionai/price_engine/api/external_collector.py:1-18`)
- 본 ablation 은 **research only** — deploy 즉시 가능 X. v3.5 ops review 필요.
- saatchi 만 enrichment feasible, artsy 는 anti-bot 강함 (별도 partnership/API)
- **conditional feature (saatchi-only) 도 drift 회피 X** — 학습 시 saatchi train rows 채워지나 production scrape 미보충 시 mismatch 그대로

---

## 6. smoke vs full 교훈

| 측면 | smoke (n_splits=2, CB iter=100) | full (n_splits=5, CB iter=1000) |
|------|--------------------------------:|--------------------------------:|
| overall Δ | -0.151%, CI 0 포함 | **-0.739%, CI 0 미포함** |
| cold | **-1.87%p improvement** (mislead) | **+0.99%p worse** (정정) |
| 의사결정 가치 | wiring 검증 / 방향성 | **신뢰도 충분 — primary** |

→ **smoke 는 wiring 검증 용도 한정**, 작은 effect 의사결정 근거 X (코덱스 P1).

---

## 7. 산출물

- `scripts/v34_2_step5_year_made_ablation.py` (이미 commit)
- `model_test_results/v3_diagnostics/v34_2_step5_year_made_ablation.json` — full 결과 (overwrite)
- `docs/v3_4_2_step5_full_results.md` (본 문서)

---

## 8. v3.4-2 5-step 진행도 — close

- ✅ step 1: stratified 26건 검증
- ✅ step 2: parser + 18 단위 테스트
- ✅ step 3: pilot 1,000건 (99.6% fill)
- ✅ step 4: 21,087 전수 enrichment (97.90% fill)
- ✅ **step 5: ablation** (V_year_only Δ-0.74%p 통계 유의, cold cohort 차단 조건)

→ **v3.4-2 close**. v3.5 backlog 으로 이전 (saatchi-conditional + production feasibility).
