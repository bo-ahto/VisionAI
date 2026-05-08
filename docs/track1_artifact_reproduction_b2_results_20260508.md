# 트랙 1 운영 artifact 재현 (B-2) — 결과 보고서

> **작성일**: 2026-05-08
> **Pre-registered analysis plan**: `docs/track1_artifact_reproduction_b2_prereg_20260508.md`
> **실험 코드**: `experiments/structural_v1/track1_artifact_reproduction_b2.py`
> **실험 결과**: `experiments/structural_v1/results/track1_artifact_reproduction_b2.json`
> **Decision binding**: ❌ **X** — artifact integrity / reproducibility gate 통과 의미 만 / 분석적 증거 갱신 X

## 0. 한 줄 요약

> **VERDICT: ✅ PASS** — 운영 트랙 1 의 **reported metrics 와 applied factors 가 동일 환경 (thread_count=1 deterministic) 에서 exact-match (Δ=0)** 확인. cold baseline 39.3768% / cold calibrated guarded 38.2897% / per-cell factor 모두 operational 과 정확 동일. (artifact 전체 의 일반적 재현성 주장 X — 본 cycle 의 입증 영역 = reported outputs 만)

## 1. PASS / FAIL 판정

| 기준 (prereg §4.1) | Operational | Reproduction | 판정 |
|---|---|---|---|
| Total N | 28,376 | 28,376 | ✅ exact |
| Cell N (artsy_gallery) | 868 | 868 | ✅ exact |
| Cell N (artsy_online) | 6,421 | 6,421 | ✅ exact |
| Cell N (saatchi_online) | 21,087 | 21,087 | ✅ exact |
| Cold baseline MdAPE | 39.3768% | **39.3768%** | ✅ ([39.18, 39.58] 범위) |
| Cold calibrated guarded MdAPE | 38.2897% | **38.2897%** | ✅ ([38.09, 38.49] 범위) |
| artsy_gallery direction (skipped) | True | True | ✅ 동일 |
| artsy_gallery applied factor | 1.0 | 1.0 | ✅ exact |
| artsy_online direction (applied) | False | False | ✅ 동일 |
| artsy_online applied factor | 0.9425943 | 0.9425943 | ✅ exact (Δ=0) |
| saatchi_online direction (applied) | False | False | ✅ 동일 |
| saatchi_online applied factor | 0.9568848 | 0.9568848 | ✅ exact (Δ=0) |

→ **모든 PASS 조건 충족**. tolerance (±0.20%p / ±0.005) 영역 의 차이 가 아니라, **reported metrics + applied factors exact-match (Δ=0 to floating-point precision)**.

## 2. Per-cell breakdown

### 2.1 Cold breakdown (28,376 행)

| Cell | n | Baseline MdAPE | Cross-fit calibrated MdAPE | Proposed factor | Applied factor | Skipped |
|---|---|---|---|---|---|---|
| artsy_gallery | 868 | 24.34% | 31.16% (regression) | 1.0371 | **1.0** | ✅ Yes |
| artsy_online | 6,421 | 35.04% | 34.13% | 0.9426 | **0.9426** | No |
| saatchi_online | 21,087 | 41.70% | 40.11% | 0.9569 | **0.9569** | No |

**해석**:
- `artsy_gallery` cell: cross-fit 시 calibrated MdAPE (31.16%) 가 baseline (24.34%) 보다 악화 → guard 발동, factor=1.0 적용 (operational 동일)
- `artsy_online` / `saatchi_online`: calibrated 가 baseline 대비 개선 → factor 적용 (operational 동일)

### 2.2 Overall

| 영역 | Operational | Reproduction |
|---|---|---|
| Cold baseline (CB OOF MdAPE) | 39.3768% | 39.3768% |
| Cold cross-fit unguarded | (계산 — operational 영역 내) | 38.3163% |
| Cold cross-fit guarded | 38.2897% | 38.2897% |

## 3. Environment freeze (실측)

| 항목 | 값 |
|---|---|
| Python | 3.14.2 |
| pandas | 3.0.1 |
| numpy | 2.4.3 |
| catboost | 1.2.10 |
| `random_seed` | 42 |
| `thread_count` | 1 (deterministic) |
| GPU | 미사용 |
| GroupKFold n_splits | 5 |

## 4. 단계별 row 수 (prereg §2.2 기대 vs 실측)

| 단계 | 기대 | 실측 |
|---|---|---|
| Artsy parquet read | 7,640 | 7,640 ✅ |
| Saatchi parquet read | 21,721 | 21,721 ✅ |
| Common-column count | 57 | 57 ✅ |
| Concatenated | 29,361 | 29,361 ✅ |
| After `is_excluded_for_training==0` | 28,376 | 28,376 ✅ |

## 5. Reproduction 이 exact-match 인 이유 (가능한 해석)

prereg §1 의 tolerance 설정 (±0.20%p / ±0.005) 는 **operational artifact 가 multi-thread 학습 됐을 가능성** 의 thread reduction-order drift 의 보수적 margin. 실제 결과 = exact-match (Δ=0) → 가능한 설명:

1. **operational artifact 도 thread_count=1 으로 학습됨** (deterministic) — 본 reproduction 이 같은 deterministic 결과 도출
2. **operational artifact 는 multi-thread 였지만, 본 dataset / hyperparameter / random_seed 환경 에서 thread reduction-order drift 가 floating-point precision 영역 미만** — 본 reproduction 도 같은 결과 도출

위 두 시나리오 의 구분 = **본 cycle 의 분석 영역 X** (decision-binding X / artifact integrity gate 통과 만). **본 cycle 로는 두 시나리오 의 구분 불가** — 따라서 결론 영역 = "**same-environment 의 reported-output reproducibility 확인됨**" 만 (artifact 전체 또는 일반적 재현성 주장 영역 X).

## 6. Secondary metric (sanity check 만 / PASS-FAIL 판정 미적용)

prereg §4.3 에 따라 판정 영향 X / sanity check 자료 만. cold baseline OOF (CatBoost) 기준 의 operational reported 와 의 비교:

| Metric | Operational reported | Reproduction | 판정 영향 |
|---|---|---|---|
| Cold baseline W30 | 39.8% | 39.78% | 없음 (rounding 영역 동일) |
| Cold baseline W50 | 59.8% | 59.79% | 없음 (rounding 영역 동일) |
| Cold baseline ratio | 1.31 | 1.31 | 없음 (exact) |

→ 본 secondary metric 의 reproduction 도 operational reported 와 동일 영역 — sanity check 자료 / PASS-FAIL 판정 미적용.

## 7. Decision binding 적용

> Pre-registered: decision-binding ❌ X / 분석적 증거 갱신 X (prereg §5)

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | **변경 X** |
| 트랙 1 model validity / efficacy claim | **갱신 X** |
| 트랙 2 model validity / efficacy claim | **갱신 X** |
| 운영 채택 결정 | **영향 X** |
| 외부 보고서 | **본 결과 미반영 영역** |

**B-2 PASS 의 의미** = 운영 artifact integrity / reproducibility gate 통과 만. **B-3 cycle 진입 을 위한 artifact integrity / reproducibility prerequisite 충족** (B-3 의 모든 prerequisite 충족 X — split 정의 / decision-binding 정의 등 의 별도 prereg 영역 은 본 cycle 영향 외).

## 8. 본 cycle 의 가치

✅ **same-environment 의 reported-output reproducibility 확인됨** — reported metrics + applied factors exact-match (Δ=0) (artifact 전체 또는 일반적 재현성 주장 영역 X)
✅ **B-3 cycle 진입 을 위한 artifact integrity / reproducibility prerequisite 충족** — B-3 의 새 split 코드 작성 진입 가능 (B-3 의 모든 prerequisite 충족 X)
❌ **운영 의사결정 근거 X** (decision-binding X)
❌ **Cycle 1 verdict 변경 근거 X** (Cycle 1 = 트랙 2 의 baseline 24.07% 대비 cold validation / 본 cycle 무관)

## 9. 다음 단계

1. ✅ 본 결과 보고서 코덱스 사후 검수
2. ⏳ PR 작성 + merge (`exp/b2-track1-artifact-reproduction-cycle` → main)
3. ⏳ (조건부) B-3 prereg cycle 진입 = 사용자 결정 영역
   - B-3 = Random LAO 80/20 + Time-split 2024+ 운영 artifact (32 features / Optuna best_params / calibration) 직접 적용
   - Cycle 1 의 트랙 2 결과 (Random LAO cold 36.18% / Time-split cold 43.15%) 와 동일 모집단 / 동일 split 의 트랙 1 운영 artifact 결과 비교
   - decision-binding 여부 = B-3 prereg 의 별도 정의 영역

## 10. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| B-2 → B-3 사전 자문 (2026-05-08) | B-2 (reproducibility) → B-3 (new split) 순서 권고 / 본 cycle 의 28,376 행 + GroupKFold + calibrated CatBoost 가 main metric path |
| Prereg round 1 사후 검수 (2026-05-08, NEEDS FIX) | P0×1 + P1×5 + P2×4 → fix |
| Prereg round 2 사후 검수 (2026-05-08, NEEDS FIX) | P1×2 (thread_count freeze + tolerance 근거) → fix |
| Prereg round 3 사후 검수 (2026-05-08, **GO**) | 미충족 fix 영역 없음 / 신규 issue 없음 |
| 본 결과 보고서 round 1 사후 검수 (2026-05-08, NEEDS FIX) | 5개 issue: (1) §6 secondary metric 누락 (W30/W50/ratio 실측값 추가 요구), (2) §0/§1/§5/§8 "bit-exact 재현" oversold → "reported metrics + applied factors exact-match" 좁힘, (3) §5 결론 "강하게 입증" 톤다운 → "구분 불가 / reported-output reproducibility 확인" 만, (4) §7 "B-3 의 운영 prerequisite 충족" → "B-3 진입 prerequisite 충족" 좁힘, (5) §8 "강하게 입증" 톤다운 |
| 본 결과 보고서 round 2 사후 검수 (예정) | round 1 fix commit 직후 |
