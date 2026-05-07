# Archive Closeout — `feature/gallery-tier-v4-research` (2026-05-08)

> **본 문서 성격**: 거대 누적 작업 branch 의 archive closeout note (코덱스 권고 Step 6).
> **Branch**: `feature/gallery-tier-v4-research` — frozen archive (rename X / 보존)
> **Tag**: `archive/gallery-tier-v4-research-20260508`
> **Origin**: https://github.com/bo-ahto/VisionAI/tree/feature/gallery-tier-v4-research

## 1. 배경

본 branch 는 2026-05 의 다양한 cycle 작업이 누적된 거대 branch (main 대비 239+ commits / 359 files / +118,915 / -211 lines). 단일 PR 로 main merge 불가 → 코덱스 자문 권고에 따라 **logical cycle 별 분할 PR + archive note** 로 종결.

## 2. main 으로 보낸 PR 목록 (Step 1-5 + bug fix)

| PR | scope | files | lines |
|---|---|---|---|
| **#27** | `feat: v3.6 production server bundle` (FastAPI cohort gating + monitoring + ETL) | 65 | +16,330 |
| **#28** | `docs: Track 1 Phase 0 closeout (Option A)` — governance only | 8 | +1,318 |
| **#29** | `feat: Track 2 core` (Stage 2-6 + Architecture close + curated dataset) | 100 | +22,943 |
| **#30** | `feat: Track 2 extensions` (Feature Track Axis A.1-A.5 + Sample size + Progressive sampling) | 33 | +6,452 |
| **#31** | `docs: Axis B` (Phase A pre-screen Round 1-3 + handoff packet) | 7 | +1,244 |
| **#32** | `fix: Track 2 core bug fix` (Stage 2 results + structural_pricing root design + .gitignore) | 14 | +2,828 |
| **(본 PR)** | `docs: Archive closeout note` | 1 | +154 |

**Total: 228 files / +51,269 lines** main 적재.

## 3. main 에 보내지 않은 카테고리별 잔존 자산 (132 files)

> 코덱스 자문 권고 = "전부 main 적재 X" / archive only 대상.

### B. v3.0 ~ v3.5 시리즈 research scripts (22 파일) — `archive only`
- `scripts/v3_*.py` (12 파일): baseline_comparison / bootstrap_ci / calibration_plot / emit_provenance / extract_oof / learning_curve / loo_gallery / loo_medium / residual_analysis / source_flip_stats / time_axis / v1_v2_comparison
- `scripts/v31_*.py` (3 파일): cold_path_ablation / d10_calibration / default_vs_tuned_paired
- `scripts/v32_*.py` (4 파일): baseline_cluster_ci / d10_conformal / d10_margin_redesign / v1_historical_paired
- `scripts/v33_*.py` (2 파일): 2_other_medium_audit / warm_saatchi_high_diag
- `scripts/v34_2_step5_year_made_ablation.py`
- `scripts/v35_step1_cohort_gating_ablation.py`
- 결정: `archive only` — 분석 / 검증용 스크립트군 / 운영 경로 변경 X / 대응 results json 까지 함께 archive 의미

### C. v3.4-2 saatchi enrichment 산출물 (16 파일) — `archive only` (예외 일부)
- `scripts/saatchi_enricher_smoke.py` / `saatchi_pilot_enrich.py` / `saatchi_pilot_sampler.py` / `saatchi_remap_experiment.py` / `saatchi_step4_full_enrich.py`
- `model_test_results/v3_diagnostics/saatchi_*.json` + `.jsonl` (7 파일)
- `tests/test_saatchi_detail_enricher.py` / `test_saatchi_year_made_merger.py`
- 결정: `archive only` — 한 사이클 실험 산출물
- **예외 가능성** (사용자 결정 영역): `saatchi_detail_enricher.py` / `saatchi_year_made_merger.py` 는 PR #27 (v3.6 prod-server bundle) 에 이미 포함 (의존성 보존 목적) — 본 잔존은 `tests/` + pilot scripts 만

### D. gallery_tier_v4 (14 파일) — `archive only` (운영 도입 보류 결정)
- `data/art_gallery_tier_list_v4.csv` / `data/gallery_alias_map.csv` (2)
- `model_test_results/ablation_gallery_tier_v4_report.md` / `v4_full_verification_report.md` (2)
- `scripts/ablation_gallery_tier_v4.py` / `ablation_v4_full_verification.py` / `analyze_gallery_tier_coverage.py` / `build_gallery_tier_v4.py` / `tier_b_gating_experiment.py` / `train_primary_market_v3_filtered.py` / `tune_fairness_check.py` / `tune_primary_market_v3_filtered.py` / `tune_v4_warm_artsy.py` / `holdout_292_v4_qa.py` (10)
- 결정: `archive only` — Top30 검수 후 운영 도입 보류 결정 (PILOT-level)

### E. v5 pilot (10 파일) — `archive only` (pilot FAIL 종결)
- `scripts/extract_dinov2_embeddings.py` / `smoke_test_gpboost.py` / `v5_composite_retrieval_pilot.py` / `v5_image_diagnostic_pilot.py`
- `src/visionai/price_engine/_v5_eval_framework.py` / `tests/test_v5_eval_framework.py`
- `docs/v5_cycle_plan_20260504.md` / `v5_R_composite_design.md` / `v5_cycle_사전등록_초안.md` / `1개월_병행일정_V5_Structural.html`
- 결정: `archive only` — Day 1-4 PILOT FAIL 3/5 종결
- **예외 가능성** (사용자 결정 영역): `_v5_eval_framework.py` 가 다른 트랙 공용 infra 로 재사용 시 별 PR 분리 검토

### F. docs research history (26 파일) — `archive only` (예외 일부)
- v3.0 보고서 / v3.0 diagnostics 보고서 (v3_보강계획_20260430.md / v3_보강계획_외부공유용 / v3_0_diagnostics_보고서.html)
- 외부 공유 / 협조 응답: 협조_응답_가격범위_옵션1_설계 / 협조_응답_미매칭갤러리_검수요청 / 협조_응답_DB마이그레이션_질문 / 협조_응답_source라벨룰
- 임원 / 발표 / 외부 공유: 임원보고_VisionAI_모델운영_20260505.md / 심사위원_기술보고서.html / 심사위원_발표스크립트.html / 콜론30_발표스크립트.html / 출처라벨_플립실험_보고서.html / 박지연_마이그레이션_회신
- 데이터 클렌징 단계계획 / 트랙2_최종보고서.md (v1, HTML 버전 = PR #29 에 포함)
- v3.4-2 결과 보고서 6종: phase1_manual_validation / step1_stratified_validation / step3_pilot_results / step4_full_results / step5_ablation_design / step5_full_results
- v3.3 external_data_inventory + unmatched_galleries_top30.csv
- 결정: `archive only` — 작업 history / 외부 공유 본 / 협조 응답 산출물

### H. 운영 의사결정 / 외부 공유 docs (7 파일) — `mixed`
- **archive only (4)**: `docs/v3_보강계획_20260430.md` / `v3_보강계획_외부공유용` / `v5_cycle_plan_20260504.md` / `v5_cycle_사전등록_초안.md`
- **사용자 결정 영역 (1)**: `docs/v4_운영도입_의사결정_20260504.md` (의사결정 기록 가치 / main merge 검토)
- **HOLD — Step 6 범위 제외 (2)**: `docs/model_technical_report_v2.md` / `model_technical_report_v2.html` — PR #25 (`docs/technical-report-v2`) 와 중복 가능성 / 단일 소스로 정리 의무
- **F 와의 중복 표기 caveat**: `v3_보강계획*` / `v5_cycle*` 는 정책 의미 강조 위해 본 H 절에 재등장. 분류 기준 = 132 잔존 총수 검산 X / 정책 분류 표시 only.

### I. root 메타 파일 (3 파일 — .gitignore 는 PR #32 에 포함)
- **archive only**: `CLAUDE.md` (project 내부 작업지침 / 운영 코드 무관)
- **사용자 결정 영역**: `README.md` (uv/uv.lock setup 정리 / repo 표준 채택 시 main merge), `.pre-commit-config.yaml` (팀 도입 의사 시 main merge)

### J. model_test_results/ (50+ 파일) — `archive only` (예외 일부)
- `v3_diagnostics/*` (residual analysis / loo gallery / loo medium / bootstrap CI / baseline comparison / calibration / d10 conformal / source flip / time axis / 등) — 50+ json/png/npz/jsonl
- `gallery_tier_coverage_report.md` / `source_flip_explanation.html` / `source_flip_report*.md`
- 결정: `archive only` — 대량 생성 산출물 / 스크립트가 main 에 있어도 결과물까지 main 적재 X
- **예외 가능성** (사용자 결정 영역): `model_test_results/integrated_v3_filtered_tuned.provenance.json` (운영 v3 모델 metadata / canonical artifact 가치)

### 기타 (root + data)
- `data/top30_피드백.csv` (외부 협조 산출물) — `archive only`
- `integrated_v3_filtered_tuned.provenance.json` 는 J 절의 사용자 결정 영역 항목으로 단일 분류 (본 절 중복 등재 X / 132 잔존 총수 검산성 보존).

## 4. 사용자 결정 영역 (코덱스 자문 명시)

기술적으로 정답이 하나가 아닌 항목 — 사용자 레포 운영 철학에 따라 결정:

1. **`README.md`, `.pre-commit-config.yaml`** main 표준 채택 여부
2. **`saatchi_*` 유틸 / 테스트** 공용 자산 승격 여부 (`saatchi_detail_enricher.py` 는 이미 PR #27 포함 / `tests/test_saatchi_*` 만 잔존)
3. **`_v5_eval_framework.py`** pilot 실패와 분리해 infra 로 살릴지
4. **`v4_운영도입_의사결정_20260504.md`** 같은 decision memo main 적재 여부
5. **`model_test_results/integrated_v3_filtered_tuned.provenance.json`** canonical artifact 적재 여부

위 항목 중 적재 결정 시 별도 follow-up PR 생성 필요. 본 archive closeout 으로 inheriting X.

## 5. PR #25 (model_technical_report_v2) 와의 정합성

`docs/model_technical_report_v2.md` + `.html` 은 별도 branch (`docs/technical-report-v2`) 의 PR #25 와 중복 영역. **본 Step 6 범위 제외** — 단일 소스로 PR #25 라인에서 정리.

## 6. Branch 보존 정책 (frozen archive)

- **Branch**: `feature/gallery-tier-v4-research` — origin 그대로 보존 / rename X
- **Tag**: `archive/gallery-tier-v4-research-20260508` — 본 closeout 시점의 HEAD 고정
- **개별 commit history**: 코덱스 사전 / 사후 검수 round 별 audit trail 보존 (각 cycle 의 P0/P1/P2 fix 이력 / commit ref `7190fc1` ~ `88a0c0e` 등)
- **새 작업 진입 X**: 본 branch 에서 추가 commit 금지 (frozen)

## 7. 후속 작업 시 참조

본 archive 의 자산 활용 방법:

```bash
# 본 branch 의 특정 파일 가져오기 (read-only 참조)
git show feature/gallery-tier-v4-research:scripts/v3_baseline_comparison.py
git show feature/gallery-tier-v4-research:model_test_results/v3_diagnostics/baseline_comparison.json

# 본 branch 의 history 검색
git log feature/gallery-tier-v4-research --grep="<keyword>"

# Tag 기반 archive 참조
git checkout archive/gallery-tier-v4-research-20260508
```

후속 cycle 진입 시 사용자 결정 영역 (위 §4) 의 적재 여부를 결정한 후 별도 PR 생성.

## 8. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Branch merge scope 사전 자문 | "D → C" 권고 (보존 후 분할 재구성) / 거대 PR A 비권고 / 분할 PR step 1-5 + step 6 archive |
| Step 6 archive 사전 자문 | 카테고리 별 권고 (must-merge / archive only / 사용자 결정 영역) / 3단 분리 / archive note 1개 / branch freeze + tag |
| Step 6 archive 사후 검수 (예정) | 본 commit 후 |

## 9. 결정 이력 요약

| 항목 | 결정 |
|---|---|
| **PR #26 (거대 단일 PR)** | **closed** (분할 PR 로 대체) |
| **분할 PR step 1-5** | **merged 대상** (PR #27, #28, #29, #30, #31) |
| **누락 bug fix** | **merged 대상** (PR #32 — Stage 2 results + structural_pricing + .gitignore) |
| **Archive closeout note** | **merged 대상** (본 PR) |
| **B / C / D / E / F / J 잔존 자산** | **archived only** (frozen branch 보존) |
| **사용자 결정 영역 (H 일부 / I 일부)** | **사용자 후속 결정 / 본 closeout 으로 inheriting X** |
| **Branch policy** | **frozen archive + tag** (rename X) |

## 10. 참조

- 트랙 1 closeout: `docs/track1_phase0_closeout_20260507.md` (PR #28)
- 트랙 2 methodology pipeline: `docs/트랙2_methodology_pipeline_20260507.md` (PR #29)
- 트랙 2 production spec: `docs/트랙2_production_통합_spec_20260507.md` (PR #29)
- v3.6 phase 3 runbook: `docs/v3_6_phase3_runbook.md` (PR #27)
- Methodology deviation log: `docs/methodology_deviation_log.md` (PR #28 / 후속 PR 에서 entries append)
