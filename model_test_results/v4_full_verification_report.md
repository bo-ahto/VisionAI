# gallery_tier_v4 종합 검증 보고서 (2026-05-04)

## 목적

Top30 갤러리 검수 → v4 갤러리 리스트 (88+30=118건) 도입 시 모델 예측력 변화를 코덱스 자문 권고대로 종합 검증.

## 검증 단계

| Step | 내용 | 산출물 |
|---|---|---|
| 1 | v3 → v4 리스트 (118건) | `data/art_gallery_tier_list_v4.csv` |
| 2 | 매핑 CSV 외부화 (43건) | `data/gallery_alias_map.csv` |
| 3 | Coverage + 분리도 측정 | `model_test_results/gallery_tier_coverage_v4.{json,md}` |
| 4 | Coverage gate 통과 (94.7%) | — |
| 5 | 1차 ablation (full data CatBoost) | `model_test_results/ablation_gallery_tier_v4.json` |
| 6 | Artsy-only ablation + Tier segment + XGBoost | `model_test_results/ablation_v4_full_verification.json` |
| 7 | 292 holdout QA | `model_test_results/holdout_292_v4_qa.json` |
| 8 | Hyperparameter tuning (10.90 결과) | `model_test_results/tune_v4_warm_artsy.json` |
| 9 | Tier B gating 실험 | `model_test_results/tier_b_gating_experiment.json` |
| 10 | Saatchi remap 실험 | `model_test_results/saatchi_remap_experiment.json` |
| 11 | 튜닝 fairness 재검증 (32 vs 33 budget-matched + holdout) | `model_test_results/tune_fairness_check.json` |

## 핵심 결과

### Coverage (Step 3)
| 지표 | 이전 (v3) | 현재 (v4) |
|---|---:|---:|
| 매칭 갤러리 | 11/66 (17%) | **41/66 (62%)** |
| 매칭 작품 | 965/7,289 (13%) | **6,902/7,289 (95%)** |
| Tier B vs E ratio | 2.04x (n=114) | 0.909x (n=2,587/387, CI 1 포함) |

### Ablation 종합 (Step 5-6)

**KFold (warm)**
| 모델 | Subset | base | +v4 | Δ |
|---|---|---:|---:|---:|
| CatBoost | Artsy full | 16.99 | 17.49 | **+0.50** |
| CatBoost | Artsy-only | 14.74 | 14.80 | +0.06 |
| XGBoost | Artsy full | 11.33 | 10.84 | **-0.49** |
| XGBoost | Artsy-only | 8.20 | 7.99 | -0.21 |

**GroupKFold (cold)**
| 모델 | Subset | base | +v4 | Δ |
|---|---|---:|---:|---:|
| CatBoost | Artsy full | 33.35 | 32.80 | **-0.55** |
| CatBoost | Artsy-only | 34.28 | 32.73 | **-1.55** |
| XGBoost | Artsy full | 36.56 | 35.11 | **-1.45** |
| XGBoost | Artsy-only | 32.37 | 32.15 | -0.22 |

### Saatchi Remap 실험 (Step 10) ⚠️ Negative result

코덱스 가설 D (Saatchi=Tier E source proxy) 검증을 위해 Saatchi → "UNKNOWN_SAATCHI" 별도 category 매핑.

**KFold (warm)**
| 조건 | Artsy MdAPE | Δ vs baseline |
|---|---:|---:|
| baseline_32 | 16.99 | — |
| v4_saatchi_TierE | 17.49 | +0.50 |
| v4_saatchi_UNKNOWN | **17.87** | **+0.88** (더 악화!) |

→ **가설 D 부정**. Saatchi 분리하면 더 악화. CatBoost warm Artsy regression 의 원인은 단순 source proxy가 아닌 다른 메커니즘.

가능한 대안 가설:
- Saatchi 데이터 자체 (가격 분포)가 학습에 영향
- Tier E n=387 만 남으면 표본 부족 → noise
- ordered target stats 가 Saatchi 분리 시 sub-optimal 학습

### Tier B Gating 실험 (Step 9)
| CV | 조건 | overall | Tier B segment |
|---|---|---:|---:|
| KFold | control_32 | 12.16 | 10.25 |
| KFold | v4_full | 12.04 | 9.75 |
| KFold | v4_tier_b_gated | 12.04 | 9.75 |

→ **XGBoost label encoding 환경에서 string-level Tier B gating 무효**. 두 조건이 동일 결과.
→ 또한 full data XGBoost 에서는 Tier B 도 개선 (-0.50). Tier B 악화는 **Artsy-only XGBoost 환경에서만** 발생한 artifact.

### 292 Holdout QA (Step 7)
- 매칭률 33% (97/292)
- alias 작동 ✅
- 미매칭 9개 갤러리 → 본 마이그레이션 시 추가 검수 필요
- 표기 정규화: "갤러리 기체" ↔ "갤러리기체" alias 추가 완료

### 하이퍼파라미터 튜닝 (Step 8)
| 조건 | warm Artsy MdAPE |
|---|---:|
| 32-feature default | 16.99 |
| 33-feature default | 17.49 |
| 33-feature **tuned** (depth 9, iter 2000) | **10.90** |

⚠️ **Fairness 우려**: 32 도 동일 budget 으로 튜닝 안 됨, 같은 5-fold로 탐색+평가 = selection bias.

### 튜닝 Fairness 재검증 (Step 11) — 진행 중
- Artist-level 80/20 holdout split (22,950/5,426)
- 32와 33 모두 동일 Optuna budget (20 trials, inner 5-fold)
- 최종 비교: 80% 학습 → 20% holdout
- 4 conditions: CB-32, CB-33, XGB-32, XGB-33

**예상 결과 시점**: ~2시간 소요

## 코덱스 자문 결론 (2차)

> CatBoost + v4 보류 / XGBoost + v4 조건부 운영 후보 / 10.90 증거 불충분

### 운영 도입 권고 (옵션 B 수정판)
1. 1차 운영 후보 = **XGBoost + v4**
2. 적용 범위: Artsy / matched galleries / 비-B tier 우선
3. Saatchi 와 CatBoost 는 추가 실험 후 재판정

### PR 분할
- **PR 1**: v4 list, alias map, 생성 스크립트, 데이터 사양 문서
- **PR 2**: experiments + 리포트 + **튜닝 fairness 재검증 포함**
- **PR 3**: training pipeline에 v4 연결 (PR 2 후)
- **PR 4**: serving + env gate + rollout (PR 3 후)

## 발견된 새 사실 (코덱스 자문 후 추가)

### Saatchi remap negative result
- 코덱스 가설 D (source proxy) 가 **이번 실험에서 부정됨**
- Saatchi → UNKNOWN_SAATCHI 매핑 시 Artsy regression 더 커짐 (+0.50 → +0.88)
- 추가 자문 필요

### Tier B 악화는 Artsy-only artifact
- Full data XGBoost: Tier B 개선 (-0.50)
- Artsy-only XGBoost: Tier B 악화 (+2.74)
- → 데이터 분포 dependent. 운영 권고 (Tier B gating)는 재검토 필요

## 다음 단계

1. **튜닝 fairness 재검증 완료 대기** (~2시간)
2. **최종 코덱스 자문** — Saatchi remap negative result + fairness 결과 종합
3. **PR 1 즉시 commit** (data 산출물)
4. **PR 2** — experiments + 리포트 (별도 PR)
5. **PR 3/4** — training/serving 도입은 fairness 결과 + 추가 자문 후
