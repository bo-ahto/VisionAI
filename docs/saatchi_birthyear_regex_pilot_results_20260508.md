# Saatchi artist_birth_year regex 확장 pilot — 결과 보고서

> **작성일**: 2026-05-08
> **Pre-registered analysis plan**: `docs/saatchi_birthyear_regex_pilot_prereg_20260508.md`
> **실험 코드**: `experiments/structural_v1/saatchi_birthyear_regex_pilot.py`
> **실험 결과**: `experiments/structural_v1/results/saatchi_birthyear_regex_pilot_20260508.json`
> **Evidence (24 record)**: `experiments/structural_v1/results/saatchi_birthyear_regex_pilot_evidence_20260508.json`
> **Decision binding**: ❌ **X** — pilot 측정 만 / efficacy / adoption / production candidate / 운영 채택 결정 모두 영향 X

## 0. 한 줄 요약

> **VERDICT (Reproducibility): ✅ PASS** / **VERDICT (Precision): ❌ FAIL** (TP rate 87.50% < 95%) / **VERDICT (Overall): ❌ FAIL**.
> 신규 패턴 (P_NEW_1 + P_NEW_2) 추가 추출 = **24 작가** (P_NEW_1: 23 / P_NEW_2: 1) — artist 회수 +2.8846%p / artwork 회수 +3.8396%p. 그 중 **3 명확한 FP (모두 P_NEW_1 에서 발생)** = multi-year bio 의 "Born in [place]" 다음 의 first year 가 birth year 아닌 case. prereg §3.4 의 명시 한 P_NEW_1 false positive risk 가 실제로 발현.
> **본 FAIL = pilot 측정 의 valid 결과**: P_NEW_1 패턴 의 spec 좁힘 (dis-confirming context exclusion 등) 의 정량 입력 / 별도 후속 cycle 의 영역.

## 1. PASS / FAIL 판정 (prereg §4.1 binding)

### 1.1 Reproducibility ✅ PASS

| 기준 | 기대 | 실측 | 판정 |
|---|---|---|---|
| Regression-free (832 unique artists 전수) | 0 mismatch | 0 mismatch | ✅ |
| 추가 추출 의 validity range (1920-2005) | 모두 in-range | 0 out-of-range | ✅ |
| 운영 `prepare_saatchi_dataset.py` sha-256 / git diff | 변경 X | sha 동일 / diff 0 line | ✅ |
| 운영 `data/saatchi_cleaned.parquet` sha-256 / git diff | 변경 X | sha 동일 / diff 0 line | ✅ |

### 1.2 Precision ❌ FAIL

| 기준 | 기대 (n=24) | 실측 | 판정 |
|---|---|---|---|
| 전수 수동 검수 의 TP rate | ≥ 95% (= max 1 FP) | **TP 21 / FP 3 / TP rate 87.50%** | ❌ FAIL |

> **FAIL 의 의미**: prereg §3.4 의 "P_NEW_1 false positive risk" 가 실제로 발생 (multi-year bio 에서 "Born in [place]" 다음 의 first year 가 birth year 아닌 경우). 본 결과 = 후속 cycle 의 P_NEW_1 spec 좁힘 의 정량 입력.

### 1.3 Overall ❌ FAIL

Reproducibility PASS + Precision FAIL → **Overall FAIL**.

## 2. Coverage increment (보고값 / PASS-FAIL 미적용)

| 영역 | 값 |
|---|---|
| Denominator (artists) | 832 |
| Old extracted (운영 5 패턴) | 35 (4.21%) |
| Pilot extracted (전체 / old + P_NEW_1 + P_NEW_2) | 59 (7.09%) |
| Added artists (P_NEW_1 + P_NEW_2 합계) | **24** (P_NEW_1: 23 / P_NEW_2: 1) (+2.8846%p) |
| Added artwork (새 추출 작가 의 작품 수) | 834 (+3.8396%p of 21,721) |

> **본 회수 = 보고값 만 / PASS-FAIL 미적용** (prereg §4.1). 단, **TP 만** 의 회수 = 21 작가 / 정확 한 회수 효과 = +2.5240%p (artist) — Precision FAIL 로 인 한 효과 영역 의 보수적 영역.

## 3. Evidence — 24 추가 추출 작가 의 전수 분석

### 3.1 사전 분석 판정 (사용자 final 판정 영역)

> ⚠️ **본 절 = 결과 보고서 작성 시 의 evidence 분석 / 사용자 의 final 판정 영역 의 입력 만**. 사용자 의 review/override 가능 (별도 cycle 의무 시).

#### TP (21 / 24 = 87.50%)

명확 한 birth year 표기 의 정확 한 추출:

| # | Display name | Year | Pattern | Span |
|---|---|---|---|---|
| 01 | Tae Kim | 1970 | P_NEW_2 | `1970 year birth` |
| 02 | Choin Lim | 1981 | P_NEW_1 | `Born in Seoul in 1981` |
| 03 | Young-sung Kim | 1973 | P_NEW_1 | `Born in Seoul Korea 1973` |
| 04 | Jooyeon Nam | 1970 | P_NEW_1 | `born in Seoul, Korea on September 21, 1970` |
| 05 | Woojung Son | 1986 | P_NEW_1 | `born in South Korea in 1986` |
| 06 | Eunah Cho | 1968 | P_NEW_1 | `born in Seoul, Korea in 1968` |
| 08 | TAE WOOK LEE | 1979 | P_NEW_1 | `born in South Korea in 1979` |
| 09 | Erion Cha | 1980 | P_NEW_1 | `Born in South Korea in 1980` |
| 10 | lee yimchoon | 1965 | P_NEW_1 | `Born in Goseong, Korea in 1965` |
| 11 | siyeong kim | 1965 | P_NEW_1 | `born in South Korea in 1965` |
| 12 | BiHop | 1977 | P_NEW_1 | `Born in Seoul in 1977` |
| 13 | Junsung Chang | 1968 | P_NEW_1 | `Born in Seoul in 1968` |
| 15 | Choong Yeul Yoo | 1960 | P_NEW_1 | `Born in July 23, 1960` |
| 16 | Dongmin Chae | 1993 | P_NEW_1 | `born in Seoul in 1993` |
| 17 | Luke Lee | 1966 | P_NEW_1 | `born in Gwangju, South Korea 1966` |
| 18 | Yoo Choong Yeul | 1960 | P_NEW_1 | `Born in July 23, 1960` |
| 20 | Youngjin Han | 1960 | P_NEW_1 | `Born in Korea in 1960` |
| 21 | YANGHEE CHANG | 1976 | P_NEW_1 | `born in Seoul in 1976` |
| 22 | Do Min | 1976 | P_NEW_1 | `born in South Korea in 1976` |
| 23 | mansoon kim | 1987 | P_NEW_1 | `Born in South Korea, in 1987` |
| 24 | Hanki Bae | 1933 | P_NEW_1 | `born in Korea at 1933` |

#### FP (3 / 24 = 12.50%)

| # | Display name | 추출 year (오) | 정확 한 birth year | 오류 사유 |
|---|---|---|---|---|
| 07 | Lee soodong | **2004** | 추출 안 됨 (bio 에 birth year 없음 / Daegu 출신 만 명시) | `I came to Seoul 2004` = 서울 이주 연도 / regex 가 "Born in Daegu, South Korea . I came to Seoul 2004" 의 첫 매칭 catch |
| 14 | Eunseon Kim | **1997** | **1991** (bio 의 "1991 Born in Seoul, Korea") | `1991 Born in Seoul, Korea 1997-1999 Resided in Birmingham` — regex 가 "Born in Seoul, Korea\n1997" catch (Born in 다음 의 first year = 1991 X / 1997 = Birmingham 거주 시작) |
| 19 | Bong Jun Kim | **1974** | **1954** (bio 의 "1954 Born in Seoul") | `1954 Born in Seoul 1974~1978 Hong Ik University` — regex 가 "Born in Seoul\n\n1974" catch (Born in 다음 의 first year = 1974 X / 진짜 = 1954, 1974 = 대학 입학) |

### 3.2 FP 패턴 의 본질 분석

세 FP case 모두 다음 구조 의 bio:

1. **[14], [19]**: `<birth_year> Born in <place> <other_year>` 형식 — birth year 가 "Born in" **이전** 에 있고, "Born in" 다음 의 first year = 학력 / 거주 등 **이후 활동 연도**. 한국 작가 의 이력서 형식 (연도 prefix → 사건) 에서 빈번.
2. **[07]**: `Born in <place A>. I came to <place B> <year>` 형식 — "Born in" 의 place 만 표기 / birth year 자체 가 bio 에 없음 / 다음 sentence 의 이주 연도 catch.

**P_NEW_1 의 구조적 한계**:
- `(?i)\bborn\s+in\s+[\w\s,'\-\.]{1,40}?\s+(?:in\s+)?(YEAR)\b`
- 길이 제한 (1-40 chars) 만 으로는 multi-clause bio (특히 이력서 형식) 의 보호 불가
- 첫 매칭 우선 규칙 의 precision risk 가 실제로 발현

## 4. Decision binding (반복 명시)

❌ **본 cycle = pilot 측정 만 / 분석적 증거 갱신 X / FAIL 도 valid 측정 결과**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | **변경 X** |
| B-2 (artifact reproducibility) verdict (PASS) | **변경 X** |
| Saatchi enrichment 복원 cycle (PR #51) verdict (PASS) | **변경 X** |
| Audit (PR #50) cleansed dataset 후보 (T0-T6) | **변경 X** |
| 트랙 1 / 트랙 2 efficacy claim | **갱신 X** |
| 운영 채택 결정 | **영향 X** |
| 운영 saatchi_cleaned.parquet | **변경 X** (read-only / fail-closed 통과) |
| 운영 prepare_saatchi_dataset.py | **변경 X** (코드 freeze / fail-closed 통과) |
| 외부 보고서 | 본 결과 미반영 영역 |
| **본 PR merge 의 의미** | pilot 자료 의 기록 만 / 운영 경로 touch 금지 / adoption 신호 X |

**본 cycle 의 가치**:
- ✅ 운영 코드 변경 X 의 fail-closed 통과 (Reproducibility PASS)
- ✅ P_NEW_1 spec 의 한계 의 정량 detection (3 FP / 12.50%) — 후속 cycle 의 입력
- ✅ 회수율 증분 의 정량 record (24 작가 / +2.88%p artist / +3.84%p artwork)
- ❌ 운영 코드 적용 의 approval X (FAIL → 후속 cycle 의 spec 좁힘 의무)

## 5. 후속 cycle 의 입력 (사용자 결정 영역 / 본 cycle 영향 X)

본 결과 의 활용 가능 영역 (모두 별도 prereg 의무):

1. **P_NEW_1 spec 좁힘 cycle** (recommended):
   - dis-confirming context exclusion (예: "Born in [place], I came to [place B] [year]" 의 두 번째 year 배제) — **가능한 후보 / 별도 cycle 의 spec 결정 영역**
   - "[year] Born in" 의 prefix-year 우선 매칭 (한국 작가 이력서 형식 대응) — **가능한 후보 / 가설 수준 / 별도 cycle 의 검증 영역**
2. **외부 source enrichment cycle** (Wikipedia / Artsy / 갤러리 — 한국 작가 영역 sparse / 별도 cycle)
3. **현 상태 유지** + 운영 의 V_year_saatchi_warm 의 옵션 B disable 패턴 으로 birth_year 결손 영역 분리 처리

## 6. 다음 단계

1. ✅ 본 결과 보고서 코덱스 사후 검수
2. ⏳ PR 작성 + merge (pilot 자료 만 / adoption 신호 X)
3. ⏳ (사용자 결정) 후속 cycle 진입 결정

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Saatchi 재수집 의견 (2026-05-08) | year_made 우선순위 → birth_year 2순위 |
| Prereg round 1 (NEEDS FIX) | P0×2 + P1×8 + P2×3 → fix |
| Prereg round 2 (NEEDS FIX) | P1×1 (precision binding 수학 정정) → fix |
| Prereg round 3 (**GO**) | 미충족 영역 없음 |
| 본 결과 보고서 round 1 (2026-05-08, NEEDS FIX) | P1×1 (§0 한 줄 요약 의 pattern-level 귀속 오류 — "P_NEW_1 추가 추출 24" → 정정: 신규 패턴 (P_NEW_1 + P_NEW_2) 합계 24 / FP 3건 모두 P_NEW_1 분리 명시) — round 1 fix: §0 / §2 의 pattern 분포 분리 (P_NEW_1 23 / P_NEW_2 1) + §5 후속 cycle 의 가설 영역 명시 |
| 본 결과 보고서 round 2 사후 검수 (예정) | round 1 fix commit 직후 |
