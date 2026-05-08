# Saatchi year_made enrichment 복원 — 결과 보고서

> **작성일**: 2026-05-08
> **Pre-registered analysis plan**: `docs/saatchi_year_enrichment_restore_prereg_20260508.md`
> **실험 코드**: `experiments/structural_v1/saatchi_year_enrichment_restore.py`
> **실험 결과**: `experiments/structural_v1/results/saatchi_year_enrichment_summary_20260508.json`
> **Decision binding**: ❌ **X** — restoration reproducibility PASS 만 / efficacy PASS X / adoption PASS X / production candidate X

## 0. 한 줄 요약

> **VERDICT: ✅ PASS** — commit `dce0dfa` (2026-05-01) 의 enrichment artifact 의 git history 복원 + merger 적용 후 의 모든 정량 영역 = **exact-match** (Δ=0). Saatchi (in-filter) 21,087 rows 의 `year_made` 결손 영역 의 정량 회수 = **20,644 rows (97.90%)**. 운영 `saatchi_cleaned.parquet` 변경 X (fail-closed 통과).

## 1. PASS / FAIL 판정

| 기준 (prereg §4.1) | 기대 | 실측 | 판정 |
|---|---|---|---|
| 복원 jsonl rows | 21,973 (exact) | 21,973 | ✅ |
| 복원 jsonl unique URL | 21,087 (exact) | 21,087 | ✅ |
| 복원 jsonl unique URL with valid year (`fetch_status='ok'` AND `year_created` notna) | 20,644 (exact) | 20,644 | ✅ |
| 복원 raw.jsonl git blob id | `4fb8b53d9242ee62a49fb826c34276d7104c3870` | 정확 동일 | ✅ |
| 복원 summary.json git blob id | `dc8c07d090af88576c614272009ef54c64cbbf18` | 정확 동일 | ✅ |
| 복원 v3_4_2_step4_full_results.md git blob id | `e1dcae48574d41ca3871c707dbddad6b30b84b81` | 정확 동일 | ✅ |
| jsonl unique URL ⊆ 운영 saatchi (in-filter) URL | 0 mismatch | 0 mismatch | ✅ |
| 운영 saatchi (in-filter) rows | 21,087 | 21,087 | ✅ |
| enriched parquet 의 Saatchi (in-filter) rows year_made notna | 20,644 (exact) | **20,644 (97.9001%)** | ✅ |
| enriched parquet work_age = `2026 - year_made` (notna 영역) | 정확 정합 | exact (allclose) | ✅ |
| 운영 saatchi_cleaned.parquet pre vs post sha-256 | 정확 동일 (변경 X) | 정확 동일 | ✅ |

→ **모든 PASS 조건 충족 / Tolerance = 0 / 모든 영역 exact-match**.

## 2. Provenance

### 2.1 복원 artifact (sha-256 file digest 포함)

| Path | git blob id | SHA-256 file digest | rows / size |
|---|---|---|---|
| `data/saatchi_year_enrichment_artifact_20260501/raw.jsonl` | `4fb8b53d9242ee62a49fb826c34276d7104c3870` | `d9bb6a0c54ccc6a03d0c658b04231ae708a0043a6354cefef8f1449a87afa41b` | 21,973 rows / 10.98 MB |
| `data/saatchi_year_enrichment_artifact_20260501/summary.json` | `dc8c07d090af88576c614272009ef54c64cbbf18` | `dbe6a34e41691574733e234b78111f7ed8ba3e2fa1df6578d9f3c4c795a9c802` | 61 lines |
| `docs/v3_4_2_step4_full_results.md` | `e1dcae48574d41ca3871c707dbddad6b30b84b81` | `3aa9933ddf8358579f3f5389b886cef115ab6719e58014add9522134d7a051fa` | 95 lines |

### 2.2 운영 saatchi_cleaned.parquet (read-only / 변경 X)

| 시점 | SHA-256 |
|---|---|
| Pre-run | `625dce88e78d311d4cd315646d44d794207c6743dbf97fafdd2f7e38a9388870` |
| Post-run | `625dce88e78d311d4cd315646d44d794207c6743dbf97fafdd2f7e38a9388870` |
| Δ | **0** (변경 X / fail-closed protocol 통과) |

### 2.3 Output enriched parquet (별도 file / restoration-only)

| Path | SHA-256 | rows |
|---|---|---|
| `data/saatchi_year_enriched.parquet` | `2d3840369767195105ec2563555a44744c3f4c166db70d81683de952c4dc8c8d` | 21,721 (raw) / 21,087 (in-filter) |

> **Note**: `data/saatchi_year_enriched.parquet` 는 `.parquet` gitignore 영역 (자동 추적 X). 본 보고서 의 SHA-256 = 재현 가능성 의 정량 record. 재실행 시 = `experiments/structural_v1/saatchi_year_enrichment_restore.py` 호출 → 동일 SHA-256 산출 의무 (deterministic).

## 3. jsonl 구조 분석

| 영역 | n |
|---|---|
| Total rows | 21,973 |
| Unique URLs (= main pass attempts) | 21,087 |
| Retry duplicate rows | 886 (= 21,973 - 21,087) |
| Unique URL with `fetch_status='ok'` AND `year_created` valid | 20,644 |
| Unique URL with unresolved year (`5xx` / `network_error` / 영구 fail) | 443 (= 21,087 - 20,644) |

> **해석**: 21,973 rows = main pass (21,087) + retry pass 1 (443 retried, 0 recovered) + retry pass 2 (443 retried, 0 recovered) = retry duplicate 886. summary.json 의 `fill_rate_year=0.9789917958932044` 와 정확 동일 (20,644 / 21,087 = 97.9001%).

## 4. Restoration coverage (in-filter Saatchi)

| 영역 | n | % |
|---|---|---|
| Saatchi (in-filter, `is_excluded_for_training==0`) rows | 21,087 | 100.00% |
| Saatchi year_made filled (enriched) | **20,644** | **97.9001%** |
| Saatchi year_made unresolved | 443 | 2.0999% |

> **단계별 정합**:
> - Operational saatchi_cleaned.parquet raw rows = 21,721
> - In-filter Saatchi (`is_excluded_for_training==0`) = 21,087 (= 21,721 - 634 excluded)
> - Enriched in-filter Saatchi year_made notna = 20,644 (97.90%)
> - work_age = `2026 - year_made` (notna 영역 정확 / NaN 영역 보존)

## 5. Decision binding 적용

❌ **본 cycle = restoration reproducibility PASS 만 / 분석적 증거 갱신 X**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | **변경 X** |
| B-2 (artifact reproducibility) verdict (PASS) | **변경 X** |
| Audit 보고서 (PR #50) 의 cleansed dataset 후보 (T0-T6) | **변경 X** (T0 28,376 의 정의 변경 X / enriched parquet 은 별도 후속 cycle 의 입력) |
| 트랙 1 / 트랙 2 efficacy claim | **갱신 X** |
| 운영 채택 결정 | **영향 X** |
| 운영 saatchi_cleaned.parquet | **변경 X** (fail-closed 통과) |
| 외부 보고서 | 본 결과 미반영 영역 |

**본 cycle 의 영향 영역 만**:
- ✅ enriched parquet (`data/saatchi_year_enriched.parquet`) = **B-3 cycle (또는 후속 cycle) 의 모집단 옵션 의 정량 입력** 가능 (별도 prereg 의무)
- ✅ Saatchi 의 `year_made` 결손 영역 의 **정량 회수 가능성 의 검증 PASS** (restoration coverage 97.90% / 모델 효과 / 운영 채택 영역 X)

> **사용 제한 재확인**: enriched parquet = restoration-only / 모델 efficacy 비교 / verdict 갱신 / production candidate / 운영 채택 결정 사용 금지 (prereg §2.3 동일).

## 6. 신선도 risk 명시

- artifact 기준일: **2026-05-01** (commit dce0dfa)
- 본 보고서: **2026-05-08** (8일 stale)
- 본 결과 의 적용 영역 = restoration coverage 의 정량 검증 만 / **현재 live page 상태 / serve-path freshness 주장 / production live data 와 의 정합 영역 사용 X** (별도 신선 fetch cycle 의무).

## 7. enriched parquet 의 후속 cycle 입력 옵션 (참고 / 본 cycle 영향 X)

본 enriched parquet 의 후속 활용 가능 영역 (모두 별도 prereg cycle 의무):

| 영역 | 활용 가능성 | 별도 cycle 의무 |
|---|---|---|
| B-3 cycle 의 모집단 정의 의 정량 입력 | ✅ 가능 (Saatchi 영역 의 year_made 추가 가능) | B-3 prereg cycle 의 모집단 옵션 결정 영역 |
| Audit (PR #50) 의 새 Tier 정의 (예: T7 = enriched + 4-field strict) | ✅ 가능 (별도 audit cycle) | 별도 audit prereg cycle |
| career_age 추가 enrichment | △ 부분 가능 (artist_birth_year 결손 90.74% 영향) | birth_year 추가 enrichment 별도 cycle (2순위 pilot) |
| 모델 retraining / efficacy 비교 | ❌ **본 cycle 영역 X** | 별도 prereg cycle (decision-binding 정의 의무) |

## 8. 다음 단계 (사용자 결정 영역 / 본 cycle 영향 X)

1. ✅ 본 결과 보고서 코덱스 사후 검수
2. ⏳ PR 작성 + merge
3. ⏳ (사용자 결정) 후속 cycle 진입:
   - **B-3 cycle prereg** (Random LAO + Time-split 운영 artifact 적용 / 본 enriched parquet 의 모집단 옵션 활용 여부 결정 영역)
   - **artist_birth_year pilot cycle** (bio regex 확장 측정 / 2순위)
   - **Audit 새 Tier 추가 cycle** (T7 = enriched + 4-field strict 의 정량 정의)

## 9. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Saatchi 재수집 의견 (2026-05-08) | year_made 우선순위 / batch 운영 cache 분리 / B-3 정량 입력 만 / decision-binding X / git history 복원 권고 |
| Prereg round 1 (2026-05-08, NEEDS FIX) | P0×2 + P1×6 + P2×2 → fix |
| Prereg round 2 (2026-05-08, NEEDS FIX) | P1×1 (Artsy parquet 정합성) → fix |
| Prereg round 3 (2026-05-08, **GO**) | 미충족 영역 없음 |
| 본 결과 보고서 사후 검수 (예정) | 본 commit 직후 |
