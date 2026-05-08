# Saatchi year_made enrichment 복원 (Pre-Registered Analysis Plan)

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: 과거 commit `dce0dfa` (2026-05-01) 의 enrichment artifact 를 git history 에서 복원 후 별도 enriched parquet 으로 merge — Saatchi 21,087 rows 의 year_made 결측 영역 의 정량 회수 의 **restoration reproducibility** 검증
> **Decision binding**: ❌ **X** — Cycle 1 verdict 변경 X / 운영 채택 결정 X / B-2 verdict 무관 / 운영 production parquet 변경 X
> **본 PASS = restoration reproducibility PASS 만**: efficacy PASS X / adoption PASS X / production candidate X
> **사전 자문**: 코덱스 (Saatchi 재수집 의견 — 옵션 A 권고 / git history 복원 / restoration-only)

> ⚠️ **본 cycle 의 scope 명시**:
> - **In-scope**: git history 복원 + 별도 enriched parquet 생성 + restoration coverage 검증 + 결과 보고서
> - **Out-of-scope**: 운영 `saatchi_cleaned.parquet` 변경 (운영 영향 차단) / 운영 모델 retraining / 모델 efficacy 비교 / variant selection / artist_birth_year enrichment

> ⚠️ **신선도 risk 명시**: artifact 기준일 = **2026-05-01** / 본 prereg = **2026-05-08** (8일 stale). 본 복원 결과 = restoration coverage 의 정량 검증 만. 현재 live page 상태 / serve-path freshness 주장 / production live data 와 의 정합 영역 사용 X (별도 신선 fetch cycle 의무).

## 1. Goal

운영 dataset 의 Saatchi 21,087 rows 의 `year_made` 100% 결측 영역 을, **commit `dce0dfa` 의 과거 batch enrichment 결과** 의 raw jsonl 을 git history 에서 복원 후 merge 하여 정량 회수. 본 cycle = restoration coverage 검증 만 / 모델 선택 / efficacy 비교 X.

**Hypothesis (PASS 조건 / restoration reproducibility 만)**:
- 복원 jsonl rows = 21,973 (commit message 정합)
- 복원 jsonl 의 git blob id = `4fb8b53d9242ee62a49fb826c34276d7104c3870` (별도 sha-256 file digest 산출 의무)
- merger 적용 후 enriched parquet 의 Saatchi (in-filter) rows 의 `year_made` notna = **exactly 20,644** (97.90% / commit dce0dfa summary 정합)
- merger 적용 후 work_age = `2026 - year_made` (notna 영역 정확 정합)
- 운영 `saatchi_cleaned.parquet` SHA-256 unchanged (변경 X)

> **본 PASS 의 의미 = restoration reproducibility 만**. efficacy PASS X / adoption PASS X / production candidate X.

## 2. Artifact freeze

### 2.1 git history source (sha-256 file digest 별도 산출)

| Path (in `dce0dfa`) | git blob id | SHA-256 file digest (산출 의무) | 처리 |
|---|---|---|---|
| `model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl` | `4fb8b53d9242ee62a49fb826c34276d7104c3870` | (실행 시 `shasum -a 256` 산출) | 복원 → `data/saatchi_year_enrichment_artifact_20260501/raw.jsonl` |
| `model_test_results/v3_diagnostics/saatchi_step4_full_enrichment.json` | `dc8c07d090af88576c614272009ef54c64cbbf18` | (산출 의무) | 복원 → `data/saatchi_year_enrichment_artifact_20260501/summary.json` |
| `docs/v3_4_2_step4_full_results.md` | `e1dcae48574d41ca3871c707dbddad6b30b84b81` | (산출 의무) | **항상 복원** (참고문서 / unconditional freeze) → `docs/v3_4_2_step4_full_results.md` |

> **Provenance 분리**: git blob id (40-hex) 와 file SHA-256 (64-hex) 는 다른 hash 영역. blob id = git internal object id (sha-1 over header+content) / file SHA-256 = 직접 file content digest. 본 cycle = **둘 다 산출 + 결과 보고서 에 기록 의무**.

### 2.2 운영 dataset (변경 X / 입력 만 / fail-closed protocol)

| Path | 처리 | Pre-run digest 기록 | Post-run digest 검증 |
|---|---|---|---|
| `data/saatchi_cleaned.parquet` | **변경 X** (read-only 입력) | shasum -a 256 기록 | 실행 직후 재산출 / 변경 시 즉시 abort |
| `data/primary_market_dataset.parquet` (Artsy) | 영향 X | 기록 의무 | 재산출 의무 |

**Fail-closed protocol** (실행 코드 의 의무):
1. 실행 시작 시 input parquet sha-256 기록 (logger info)
2. **Output path != input path assert** (코드 레벨 가드)
3. 실행 직후 input parquet sha-256 재산출 → pre-run digest 와 정확 동일 검증 (불일치 시 즉시 abort + 알림)

### 2.3 Output (별도 file / restoration-only artifact)

| Path | 의미 | **사용 제한** |
|---|---|---|
| `data/saatchi_year_enriched.parquet` | merger 적용 결과 (Saatchi 21,087 + year_made / has_year_made / work_age column 채워짐) | ⚠️ **restoration-only** — **모델 efficacy 비교 / verdict 갱신 / production candidate / 운영 채택 결정 사용 금지**. B-3 cycle 의 모집단 옵션 의 정량 입력 만 (별도 prereg 의무). |
| `experiments/structural_v1/results/saatchi_year_enrichment_summary_20260508.json` | merge 결과 정량 summary | 본 cycle 검증 자료 만 |
| `docs/saatchi_year_enrichment_restore_results_20260508.md` | 결과 보고서 | 본 cycle 검증 자료 만 |

## 3. Method

### 3.1 Step 1: git history 복원

```bash
mkdir -p data/saatchi_year_enrichment_artifact_20260501
git show dce0dfa:model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl \
    > data/saatchi_year_enrichment_artifact_20260501/raw.jsonl
git show dce0dfa:model_test_results/v3_diagnostics/saatchi_step4_full_enrichment.json \
    > data/saatchi_year_enrichment_artifact_20260501/summary.json
git show dce0dfa:docs/v3_4_2_step4_full_results.md > docs/v3_4_2_step4_full_results.md
```

> **Verification**:
> - `wc -l raw.jsonl` = 21,973 (정확)
> - `git hash-object raw.jsonl` = `4fb8b53d9242ee62a49fb826c34276d7104c3870` (정확)
> - `shasum -a 256 raw.jsonl` = 보고서 에 산출 값 기록

### 3.2 Step 2: merger 적용 (실제 코드 entry 정합)

operational `scripts/saatchi_year_made_merger.py` 의 다음 함수 호출 (실측 함수명):

- `load_enrichment_year_map(path)` (line 56) → `dict[artwork_url, year_created]` 생성
- `merge_year_made(df, enrichment_map, only_saatchi=True)` (line 82) → year_made update
- `add_has_year_made_flag(df)` (line 116) → has_year_made flag 부여
- `recompute_work_age(df, ref_year=WORK_AGE_REF_YEAR)` (line 123) → work_age 재계산

> **Variant 정의**: 본 cycle = `merge_year_made` + `add_has_year_made_flag` + `recompute_work_age` 만 (V_year_only 의 hard 정의 와 정합 / `recompute_vintage_freshness` 미적용 — career_age / vintage_premium 은 birth_year 결손 90.74% 영향 으로 별도 cycle 의무).

> **Variant 선택 근거 (V_year_saatchi_warm 배제 이유)**: `V_year_saatchi_warm` (warm artist gating) 은 v3.5 step 1 의 운영 채택 variant 영역 — **본 cycle = 모델 선택 X / restoration coverage 확인 만 / 따라서 warm gating semantics 도입 X**. enriched parquet 의 활용 = B-3 cycle 의 모집단 옵션 (별도 prereg) 영역 — gating 적용 여부 = B-3 의 결정 영역.

> **운영 saatchi_cleaned.parquet 변경 차단**: `merge_year_made` 의 결과 = `df.copy()` 의 메모리 dataframe 만 / `data/saatchi_year_enriched.parquet` 으로 별도 저장. 운영 source 변경 X (§2.2 fail-closed protocol 강제).

### 3.3 Step 3: Restoration coverage 검증

다음 정량 영역 의 PASS / FAIL 판정 (본 cycle 의 inline 검증 코드 영역 / 외부 audit script 의존 X):

1. 복원 jsonl rows count = 21,973 (exact)
2. 복원 jsonl 의 git blob id = `4fb8b53d9242ee62a49fb826c34276d7104c3870` (exact)
3. 복원 jsonl unique URL count = 21,087 (exact, retry duplicates 제외)
4. 복원 jsonl unique URL with `fetch_status='ok'` AND `year_created` notna = 20,644 (exact)
5. 운영 saatchi (in-filter, `is_excluded_for_training==0`) URL set = jsonl unique URL set (정확 동일)
6. enriched parquet 의 Saatchi (in-filter) rows 의 year_made notna = **20,644 (exact)**
7. enriched parquet 의 work_age = `2026 - year_made` (notna 영역 정확 정합 / NaN 영역 정확 보존)
8. 운영 saatchi_cleaned.parquet sha-256 = pre-run digest 와 동일 (변경 X)

### 3.4 Step 4: 결과 보고서 + 코덱스 검수 + PR

## 4. PASS / FAIL 기준 (Tighter — restoration reproducibility 만)

### 4.1 PASS (모두 충족 / exact 영역)

- ✅ 복원 jsonl rows = **exactly 21,973**
- ✅ 복원 jsonl git blob id = **`4fb8b53d9242ee62a49fb826c34276d7104c3870`** (정확)
- ✅ 복원 jsonl unique URL = **exactly 21,087**
- ✅ 복원 jsonl unique URL with valid year (`fetch_status='ok'` AND `year_created` notna) = **exactly 20,644**
- ✅ jsonl unique URL ⊆ 운영 saatchi (in-filter) URL = **0 mismatch** (jsonl URL 모두 운영 영역 에 존재)
- ✅ 운영 saatchi (in-filter, `is_excluded_for_training==0`) URL count = **exactly 21,087**
- ✅ enriched parquet 의 Saatchi (in-filter) rows year_made notna = **exactly 20,644** (97.9001% 정확)
- ✅ enriched parquet 의 in-filter Saatchi work_age = `2026 - year_made` (notna 영역 정확 동일 / NaN 영역 보존)
- ✅ 운영 saatchi_cleaned.parquet pre-run vs post-run sha-256 = **정확 동일** (변경 X)

> **Tolerance = 0** (모든 영역 exact). dce0dfa summary 의 reported 영역 과 정확 동일 결과 의무. 정확 동일 영역 외 = FAIL 처리 / 별도 디버깅 cycle 의무.

### 4.2 FAIL

위 중 하나 미충족 → 별도 디버깅 cycle (본 prereg 미포함):
- jsonl row / blob id mismatch → git history 복원 절차 점검
- merger fill rate ≠ 20,644 → merger 의 url 매칭 로직 점검 / jsonl 구조 변경 detection
- 운영 parquet sha-256 변경 detect → 절차 위반 / fail-closed abort + rollback 의무 / **즉시 stop**

## 5. Decision binding

❌ **본 cycle = restoration reproducibility PASS 만 / 분석적 증거 갱신 X**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | **변경 X** |
| B-2 (artifact reproducibility) verdict (PASS) | **변경 X** |
| Audit 보고서 (PR #50) 의 cleansed dataset 후보 | **변경 X** (T0 28,376 의 정의 변경 X / enriched parquet 은 별도 후속 cycle 의 입력) |
| 트랙 1 / 트랙 2 efficacy claim | **갱신 X** |
| 운영 채택 결정 | **영향 X** |
| 운영 saatchi_cleaned.parquet | **변경 X** (read-only / fail-closed 보장) |
| 외부 보고서 | 본 결과 미반영 영역 |

**본 cycle 의 영향 영역 만**:
- ✅ enriched parquet (`data/saatchi_year_enriched.parquet`) = **B-3 cycle (또는 후속 cycle) 의 모집단 옵션 의 정량 입력** (별도 prereg 의무)
- ✅ Saatchi 의 `year_made` 결손 영역 의 **정량 회수 가능성 의 검증** (restoration coverage 만 / 모델 효과 / 운영 채택 영역 X)

## 6. 실행 protocol

1. ✅ 본 prereg 작성 + 코덱스 사후 검수
2. ⏳ git history 복원 (`git show dce0dfa:path > out`)
3. ⏳ 복원 file 의 sha-256 산출 + git blob id 검증
4. ⏳ Pre-run 운영 parquet sha-256 기록
5. ⏳ Inline merger + restoration coverage 검증 코드 작성 (`experiments/structural_v1/saatchi_year_enrichment_restore.py`) — 외부 audit script 의존 X
6. ⏳ 실행 + Post-run 운영 parquet sha-256 검증
7. ⏳ 결과 보고서 작성 + 코덱스 사후 검수
8. ⏳ PR 작성 + merge

## 7. 운영 정의 정합

- `WORK_AGE_REF_YEAR = 2026` (`scripts/saatchi_year_made_merger.py:43`) — **dataset build 에 고정된 operational definition** (현재 연도 X). `prepare_primary_market_dataset.py:254` 정의 그대로.

## 8. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Saatchi 재수집 의견 (2026-05-08) | year_made 우선순위 / batch 운영 cache 분리 / B-3 정량 입력 만 / decision-binding X / git history 복원 권고 |
| 본 prereg round 1 사후 검수 (2026-05-08, NEEDS FIX) | P0×2 (restoration-only 명시 강화 / fail-closed protocol 승격) / P1×6 (merger 함수명 정정 / audit script 부재 / blob id vs sha-256 분리 / PASS tolerance tighter / variant 선택 근거 / 신선도 risk / artifact freeze unconditional) / P2×2 (WORK_AGE 표현 / decision-binding 강화) |
| 본 prereg round 2 사후 검수 (예정) | round 1 fix commit 직후 |
