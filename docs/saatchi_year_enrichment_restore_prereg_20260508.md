# Saatchi year_made enrichment 복원 (Pre-Registered Analysis Plan)

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: 과거 commit `dce0dfa` (2026-05-01) 의 enrichment artifact (97.90% fill / 21,973 rows) 를 git history 에서 복원 후 별도 enriched parquet 으로 merge — Saatchi 21,087 rows 의 year_made 결측 영역 의 정량 회수
> **Decision binding**: ❌ **X** — Cycle 1 verdict 변경 X / 운영 채택 결정 X / B-2 verdict 무관 / 운영 production parquet 변경 X
> **사전 자문**: 코덱스 (Saatchi 재수집 의견 — 옵션 A 선택 / git history 복원 권고)

> ⚠️ **본 cycle 의 scope 명시**:
> - **In-scope**: git history (`dce0dfa`) 의 enrichment artifact 복원 + 별도 enriched parquet (`data/saatchi_year_enriched.parquet`) 생성 + audit re-run + 결과 보고서
> - **Out-of-scope**: 운영 `saatchi_cleaned.parquet` 변경 (운영 영향 차단) / 운영 모델 retraining / artist_birth_year 추가 enrichment (별도 pilot cycle)

## 1. Goal

운영 dataset 의 Saatchi 21,087 rows 의 `year_made` 100% 결측 영역 을, **commit `dce0dfa` 의 과거 batch enrichment 결과** (97.90% fill, 20,644 / 21,087) 의 raw jsonl 을 git history 에서 복원 후 merge 하여 정량 회수.

**Hypothesis (PASS 조건)**:
- 복원된 jsonl rows = 21,973 (commit message 와 정합)
- merger 적용 후 Saatchi rows 의 `year_made` notna count ∈ [20,500, 21,000] (97.90% ± margin)
- merger 적용 후 work_age 자동 재계산 (`2026 - year_made`) 정합
- 운영 `saatchi_cleaned.parquet` 변경 X (별도 enriched parquet 만 생성)

## 2. Artifact freeze

### 2.1 git history source

| Path (in `dce0dfa`) | Size | 처리 |
|---|---|---|
| `model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl` | 10.98 MB / 21,973 rows | 복원 → `data/saatchi_year_enrichment_raw.jsonl` (data/ 영역) |
| `model_test_results/v3_diagnostics/saatchi_step4_full_enrichment.json` | 61 lines | 복원 → `data/saatchi_year_enrichment_summary.json` (provenance) |
| `docs/v3_4_2_step4_full_results.md` | 95 lines | (이미 main 에 있는지 확인 / 없으면 docs/ 복원) |

> **Provenance**: 복원 file 들 = commit `dce0dfa1fd5b3d7e6e43f651e921140e56b68a2b` (2026-05-01 22:04 KST) 의 정확 한 sha-256 hash 동일 보장 (git show extraction).

### 2.2 운영 dataset (변경 X / 입력 만)

| Path | 처리 |
|---|---|
| `data/saatchi_cleaned.parquet` | **변경 X** (운영 source / read-only 입력) |
| `data/primary_market_dataset.parquet` (Artsy) | 본 cycle 영향 X |

### 2.3 Output (별도 file)

| Path | 의미 |
|---|---|
| `data/saatchi_year_enriched.parquet` | merger 적용 결과 (Saatchi 21,087 + year_made / work_age column 채워진 영역) |
| `experiments/structural_v1/results/saatchi_year_enrichment_summary_20260508.json` | merge 결과 의 정량 summary |
| `docs/saatchi_year_enrichment_restore_results_20260508.md` | 결과 보고서 |

## 3. Method

### 3.1 Step 1: git history 복원

```bash
mkdir -p data
git show dce0dfa:model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl > data/saatchi_year_enrichment_raw.jsonl
git show dce0dfa:model_test_results/v3_diagnostics/saatchi_step4_full_enrichment.json > data/saatchi_year_enrichment_summary.json
```

> **Verification**: 복원 후 `wc -l` = 21,973 정합 / sha-256 = git blob `4fb8b53d9242ee62a49fb826c34276d7104c3870` 정합.

### 3.2 Step 2: merger 적용 (`saatchi_year_made_merger.py`)

operational `scripts/saatchi_year_made_merger.py` 의 `merge_year_enrichment()` 함수 호출:

- 입력 1: 복원된 `data/saatchi_year_enrichment_raw.jsonl` (url → year_created 매핑)
- 입력 2: `data/saatchi_cleaned.parquet` (read-only)
- variant: `V_year_only` (year_made + has_year_made + work_age 추가, vintage_premium / freshness_discount / career_age 미적용 — career_age 는 birth_year 결손 90.74% 영향으로 별도 cycle)
- WORK_AGE_REF_YEAR = 2026 (operational 정의 그대로)

> **운영 saatchi_cleaned.parquet 변경 차단**: merger 의 결과 = **메모리 dataframe** 만 / `data/saatchi_year_enriched.parquet` 으로 별도 저장. 운영 source 변경 X.

### 3.3 Step 3: Audit re-run

`scripts/audit_primary_market_data.py` 의 핵심 로직 을 enriched parquet 에 적용:
- Saatchi (enriched) 21,087 rows 의 `year_made` notna count
- 4-field 결합 결측 영역 의 변경 영역

> **본 cycle 영역**: enriched parquet 의 정량 영역 만 / 운영 dataset (T0 28,376) 의 metric 변경 영역 X.

### 3.4 Step 4: 결과 보고서 + 코덱스 검수 + PR

## 4. PASS / FAIL 기준

### 4.1 PASS (모두 충족)

- ✅ 복원 jsonl rows = 21,973 (exact, commit message 정합)
- ✅ 복원 jsonl sha-256 = git blob hash 정확 동일
- ✅ merger 적용 후 Saatchi `year_made` notna ∈ [20,500, 21,000] (97.90% ± margin)
  - **Tolerance 근거**: `dce0dfa` 의 reported 20,644 / 21,087 = 97.90% / 운영 dataset 의 row count 와 jsonl 의 row count mismatch (21,087 vs 21,973) 의 ID 매칭 영역 의 보수적 margin (일부 jsonl row 가 운영 dataset 에 미존재 가능)
- ✅ work_age = `2026 - year_made` (notna row 영역 정확 정합)
- ✅ 운영 `saatchi_cleaned.parquet` 변경 X (sha-256 unchanged)

### 4.2 FAIL

위 중 하나 미충족 → 별도 디버깅 cycle (본 prereg 미포함):
- jsonl row mismatch → git history 복원 절차 점검
- merger fill rate 결손 → merger 의 url 매칭 로직 점검
- 운영 parquet 변경 detect → 절차 위반 / rollback 의무

## 5. Decision binding

❌ **본 cycle = decision-binding X / 분석적 증거 갱신 X**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | 변경 X |
| B-2 (artifact reproducibility) verdict (PASS) | 변경 X |
| 트랙 1 / 트랙 2 efficacy claim | 갱신 X |
| 운영 채택 결정 | 영향 X |
| 운영 saatchi_cleaned.parquet | 변경 X (read-only) |
| 외부 보고서 | 본 결과 미반영 영역 |

**본 cycle 의 영향 영역 만**:
- ✅ enriched parquet (`data/saatchi_year_enriched.parquet`) = B-3 cycle (또는 후속 cycle) 의 모집단 옵션 의 정량 입력
- ✅ Saatchi 의 `year_made` 결손 영역 의 정량 회수 가능성 의 검증

## 6. 실행 protocol

1. ✅ 본 prereg 작성 + 코덱스 사후 검수
2. ⏳ git history 복원 (`git show dce0dfa:path > out`)
3. ⏳ merger 실행 + enriched parquet 저장
4. ⏳ audit re-run + summary 산출
5. ⏳ 결과 보고서 작성
6. ⏳ 결과 보고서 코덱스 사후 검수
7. ⏳ PR 작성 + merge

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Saatchi 재수집 의견 (2026-05-08) | year_made 우선순위 / batch 운영 cache 분리 / B-3 정량 입력 만 / decision-binding X / git history 복원 권고 |
| 본 prereg 사후 검수 (예정) | 본 commit 직후 |
