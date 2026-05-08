# Saatchi artist_birth_year regex 확장 pilot — Pre-Registered Analysis Plan

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: Saatchi `prepare_saatchi_dataset.py:101` 의 `extract_birth_year(bio)` 의 regex 패턴 을 사전 정의된 후보 로 확장 → 회수율 증분 + precision 의 정량 측정 의 **pilot cycle**
> **Decision binding**: ❌ **X** — Cycle 1 / B-2 verdict 변경 X / 운영 saatchi_cleaned.parquet 변경 X / 운영 채택 결정 X / 모델 efficacy 비교 X
> **본 PASS = pilot 측정 reproducibility 만**: efficacy PASS X / adoption PASS X / production candidate X
> **본 PR merge 의 의미 = pilot 자료 의 기록 만 / 운영 경로 touch 금지 / adoption 신호 X**
> **사전 자문**: 코덱스 (artist_birth_year 2순위 pilot / regex 확장 만으로 몇 %p 오르는지 먼저 측정 / decision-binding X)

> ⚠️ **본 cycle 의 scope 명시**:
> - **In-scope**: 사전 정의 된 regex 패턴 후보 의 추가 / 832 명 전체 의 old-only vs pilot-old-subset regression-free 검증 / 회수율 증분 정량 (보고값) / 추가 추출 작가 전수 수동 검수 / precision 정량
> - **Out-of-scope**: 운영 `prepare_saatchi_dataset.py:101` 직접 변경 (운영 영향 차단) / 외부 source enrichment / 운영 모델 retraining / efficacy 비교 / adoption 결정

## 1. Hypothesis (관측 / 측정 영역 만)

> 본 절 = **측정 hypothesis 만** (PASS / FAIL 의 binding rule 은 §4 만).

`prepare_saatchi_dataset.py:101` 의 기존 5 패턴 + 본 prereg 의 사전 정의 P_NEW_1 / P_NEW_2 추가 시:
- Saatchi 의 832 unique artists 의 birth_year 추출 = 기존 35 → ?
- 추가 추출 작가 의 precision (수동 전수 검수) = ?
- 추가 추출 의 false positive sample bio 분석 = 사용자 의사결정 영역 의 입력

> 모든 결과 = pilot 측정 자료 만 / 운영 채택 / 운영 코드 변경 / 모델 efficacy 영역 결정 X.

## 2. 현재 상태 freeze

### 2.1 운영 saatchi 의 artist_birth_year 영역

| 영역 | n 작가 | % |
|---|---|---|
| 운영 saatchi rows (raw) | 21,721 | — |
| 운영 saatchi unique artist_slug | 832 | 100.00% |
| 현재 birth_year 추출 성공 | **35** | **4.21%** |
| bio 있음 + 4-digit year (1920-2005) 있음 + 추출 실패 | 72 | 8.65% (잠재 회수 영역) |
| bio 자체 없음 | 159 | 19.11% (회수 불가) |
| JSON 에 없는 작가 | 12 | 1.44% (re-fetch 영역 / 본 cycle 영향 X) |
| 그 외 (bio 있지만 1920-2005 year 없음) | ≈ 554 | ≈ 66.59% (회수 불가) |

### 2.2 기존 regex 패턴 (`prepare_saatchi_dataset.py:101-118` freeze)

```python
patterns = [
    r"(?:born|b\.)\s+(?:in\s+)?(?:on\s+)?(?:\w+\s+\d{1,2},?\s+)?(19\d{2}|20[01]\d)",
    r"(?:Born|born)\s+(?:in\s+)?(19\d{2}|20[01]\d)",
    r"\(b\.\s*(19\d{2}|20[01]\d)\)",
    r"(\d{4})년\s*생",
    r"(\d{4})년\s*출생",
]
# Validity range: 1920 <= year <= 2005
```

### 2.3 Validity range (1920-2005) 근거

- **Lower 1920**: 운영 dataset 의 modern primary market 영역 — 100세 이상 작가 의 활동 sparse / 105세 이상 birth year 는 corpus 영역 외
- **Upper 2005**: 운영 학습 시점 (2026) - 21 = 21세 미만 작가 의 활동 sparse + Saatchi 의 일반적 작가 등록 연령 (대부분 18+ 활동)
- **본 pilot 동일 유지**: 신규 패턴 도 1920-2005 적용 / 위 범위 외 의 year 매칭 시 None 반환

## 3. Method — 사전 정의된 추가 regex 패턴 (frozen)

### 3.1 추가 패턴 후보 (사전 정의 / 본 cycle 외 추가 금지)

bio 분석 (820 매칭 작가 / 72 unextracted with year 영역) 의 가장 빈번한 미커버 형식:

#### P_NEW_1 (Born in [place] [+ optional in] [year])

```python
# 정확 한 Python regex 문자열 (alternation pipe 는 single `|`)
P_NEW_1 = r"(?i)\bborn\s+in\s+[\w\s,'\-\.]{1,40}?\s+(?:in\s+)?(19[2-9]\d|200[0-5])\b"
```

**의도된 매칭 형식**:
- `Born in Seoul in 1981`
- `Born in Seoul Korea 1973`
- `born in South Korea in 1986`
- `Born in St. Louis, USA, 1985`
- `Born in Xi'an, 1992`

**길이 제한 (1-40 chars between "born in" and year)** = 의도하지 않은 long-distance 매칭 방지.

**False positive risk 명시 (수동 검수 영역)**:
- `Born in London, based in Berlin in 1998` 같은 case 에서 활동/이주 연도 catch 가능 → **수동 검수 의무 영역** (§3.4)
- 첫 매칭 우선 (multi-year bio 의 첫 매칭) — Born 직후 year 가 birth year 의 가장 일반적 형식 의 정합

**False negative risk 명시**:
- `[\w\s,'\-\.]{1,40}?` = 단어/공백/콤마/apostrophe/hyphen/period 허용 / 다른 특수문자 (예: `슬래시 /` / 한자) 미커버 → 일부 비표준 표기 누락 가능 (수동 검수 의 보고값 영역)

#### P_NEW_2 ([year] year birth)

```python
P_NEW_2 = r"\b(19[2-9]\d|200[0-5])\s+year\s+birth\b"
```

**의도된 매칭 형식**:
- `1970 year birth` (한국 작가 의 비표준 영어 형식)

**False positive risk**: 매우 낮음 (specific 표현)

### 3.2 패턴 적용 우선순위

순차 적용 (첫 매칭 우선):

1. 기존 5 패턴 (위 §2.2) 의 순차 시도
2. 모두 fail 시 P_NEW_1 시도
3. P_NEW_1 fail 시 P_NEW_2 시도
4. 모두 fail 시 None 반환

> **첫 매칭 우선 의 precision risk**: multi-year bio 의 경우 첫 매칭 = birth year 가 아닐 수 있음 — **§3.4 의 수동 검수 의무 영역**.

### 3.3 운영 코드 freeze (fail-closed protocol)

#### 운영 영역 변경 차단

| 영역 | 변경 차단 의무 |
|---|---|
| `scripts/prepare_saatchi_dataset.py` | **변경 X** (코드 freeze) — 본 cycle 종료 시 git diff 0 line 의무 |
| `data/saatchi_cleaned.parquet` | **변경 X** (read-only) — pre/post sha-256 정확 동일 의무 |
| `data/primary_market_dataset.parquet` | 본 cycle 사용 X (영향 X) |

#### Fail-closed protocol (실행 코드 의 의무)

1. **실행 시작 시 pre-run digest 기록**:
   - `scripts/prepare_saatchi_dataset.py` 의 sha-256 + git status diff
   - `data/saatchi_cleaned.parquet` sha-256
2. **Output path != input path assert** (코드 레벨 가드)
3. **실행 직후 post-run digest 검증**:
   - 위 영역 의 sha-256 / git diff 가 pre-run 과 정확 동일
   - 불일치 detect 시 즉시 abort + 알림 (raise RuntimeError)
4. **PR 단계 의 가드**:
   - PR diff 에 `scripts/prepare_saatchi_dataset.py` / `data/saatchi_cleaned.parquet` / `data/primary_market_dataset.parquet` 의 변경 라인 = 0 의무 (PR review 시 검증)

#### Pilot 코드 의 위치

- 본 cycle = 별도 module (`experiments/structural_v1/saatchi_birthyear_regex_pilot.py`) 만
- 운영 코드 import 만 (변경 X)

### 3.4 수동 검수 의무 (binding)

#### Scope

추가 추출 (= 새 패턴 P_NEW_1 + P_NEW_2 로 만 추출 / 기존 5 패턴 으로는 추출 X) 작가 의 **전수 수동 검수**.

> **전수 검수 의 근거**: 추가 추출 예상 ≈ 18-19 작가 / sample size 작음 / sample 검수 의 신뢰구간 광범위 → 전수 검수 가 더 정확.

#### Evidence field (수동 검수 시 의무 record)

각 추가 추출 작가 마다 다음 6 field 의 record:

| Field | 의미 |
|---|---|
| `artist_id` | 작가 식별자 |
| `display_name` | 작가 표시명 |
| `bio_full` | bio 원문 전체 (검수 자료) |
| `extracted_span` | 매칭 된 패턴 + 추출 substring (regex 의 `m.group(0)`) |
| `extracted_year` | 추출 된 year (정수) |
| `manual_judgment` | TP (true positive / 정확) / FP (false positive / 오탐) / UNCERTAIN |
| `judgment_reason` | 판정 근거 (예: "bio 의 다른 year = 전시 연도 / Born 직후 year 가 birth year 정합") |

#### Adjudication rule

- 검수자: **사용자 (단일 검수자)** — 본 cycle 의 검수 권한 의 sole holder
- UNCERTAIN 판정 = FP 와 동등 처리 (보수적)
- 검수 결과 의 변경 = 별도 cycle 의무 (본 cycle 의 결과 보고서 의 record 는 freeze)

## 4. PASS / FAIL 기준 (binding decision rule 만)

### 4.1 PASS (모두 충족)

#### Reproducibility / Regression

- ✅ **Regression-free (832 명 전수)**: 832 unique artists 영역 의 old-only 결과 (기존 5 패턴 만) 와 pilot 의 old-subset 결과 (pilot 함수 의 기존 5 패턴 영역 만) = 작가 별 정확 동일 (35 작가 + 그 외 모두 None 동일)
- ✅ 추가 추출 작가 의 birth year 모두 1920-2005 범위 (validity range 정합)
- ✅ 운영 `data/saatchi_cleaned.parquet` pre/post sha-256 정확 동일 (변경 X)
- ✅ 운영 `scripts/prepare_saatchi_dataset.py` git diff 0 line (변경 X)

#### Precision (수동 검수)

- ✅ 추가 추출 의 전수 수동 검수 의 **TP rate ≥ 95%** (= FP 또는 UNCERTAIN 비율 ≤ 5%)
  - **정확 한 binding 의 의미 (수학적)**: TP rate = (TP count) / (추가 추출 전체 n). FP + UNCERTAIN ≤ 5% × n 의 정수 round-down 영역 만 PASS.
    - n = 18 → 17/18 = 94.44% → FP 1 시 FAIL / **0 FP 만 PASS**
    - n = 19 → 18/19 = 94.74% → FP 1 시 FAIL / **0 FP 만 PASS**
    - n = 20 → 19/20 = 95.00% → FP 1 시 PASS (95% ≥ 95% 이므로) / **최대 1 FP PASS**
    - n = 39 → 37/39 = 94.87% → FP 2 시 FAIL / **최대 1 FP PASS** (38/39 = 97.44%)
    - n = 40 → 38/40 = 95.00% → FP 2 시 PASS / **최대 2 FP PASS**
  - 본 cycle 의 추가 추출 예상 ≈ 18-19 작가 → 사실상 **0 FP 만 PASS** (1 FP 라도 발생 시 FAIL).
  - UNCERTAIN 도 보수적 FP 처리 (= TP 가 아닌 모든 판정 = FP 와 동등 처리)

> **회수율 증분 (artist 단위) = 보고값 만 / PASS / FAIL 미적용**.
> "측정 pilot" 의 본질 — 회수율 의 크기 자체 가 PASS / FAIL 결정 영역 X (0%p 도 valid 측정 결과 / 0 < x < 0.5%p 도 valid). 회수율 = 결과 보고서 의 정량 record 만 / 후속 cycle 의 입력.

### 4.2 FAIL

위 PASS 조건 중 하나 미충족 → 별도 디버깅 cycle (본 prereg 미포함):
- Regression detect (832 명 의 old-only 비교 결손) → 새 패턴 의 우선순위 / overlap 점검
- 1920-2005 범위 외 추출 detect → validity range 적용 코드 점검
- TP rate < 95% → 패턴 spec 점검 / P_NEW_1 의 false positive 영역 narrow 의무
- 운영 source 변경 detect → 절차 위반 / immediate abort + rollback

## 5. Decision binding (반복 명시)

❌ **본 cycle = pilot 측정 reproducibility 만 / 분석적 증거 갱신 X**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | **변경 X** |
| B-2 (artifact reproducibility) verdict (PASS) | **변경 X** |
| Saatchi enrichment 복원 cycle (PR #51) verdict (PASS) | **변경 X** |
| Audit (PR #50) cleansed dataset 후보 (T0-T6) | **변경 X** |
| 트랙 1 / 트랙 2 efficacy claim | **갱신 X** |
| 운영 채택 결정 | **영향 X** |
| 운영 saatchi_cleaned.parquet | **변경 X** (read-only) |
| 운영 prepare_saatchi_dataset.py | **변경 X** (코드 freeze) |
| 외부 보고서 | 본 결과 미반영 영역 |
| **본 PR merge 의 의미** | pilot 자료 의 기록 만 / 운영 경로 touch 금지 / adoption 신호 X |

> **본 결과 의 모든 활용 = 후속 adoption prereg 의 입력 영역 만**. 본 cycle 의 PASS = 운영 코드 변경 의 approval X / 운영 모델 retraining 의 approval X.

## 6. 실행 protocol

1. ✅ 본 prereg 작성 + 코덱스 사후 검수
2. ⏳ Pilot 코드 작성 (`experiments/structural_v1/saatchi_birthyear_regex_pilot.py`)
   - 기존 + 신규 regex 의 함수 (운영 코드 import 만 / 변경 X)
   - 운영 saatchi_kr_artists.json 매칭 작가 (820) 영역 의 추출 시도
   - 832 unique artists 전체 의 old-only vs pilot-old-subset 정확 동일 검증
   - 추가 추출 작가 의 6-field evidence record (`additional_extractions.json`)
   - 회수율 증분 정량 (artist 단위 + artwork 단위) — 보고값
   - Pre/post fail-closed digest 검증
3. ⏳ 실행 + summary JSON 산출 (필드 사전 정의):
   - `verdict`: "PASS" / "FAIL"
   - `reproducibility_checks`: regression-free / validity range / fail-closed digest
   - `precision_checks`: 추가 추출 작가 의 evidence record list (TP/FP 판정 사용자 입력 후)
   - `coverage_increment` (보고값): denominator (832), old_extracted_n (35), new_extracted_n, added_artists_n, increment_pct_artist, increment_pct_artwork
   - `sample_frame`: scope = "운영 saatchi 832 unique artists / saatchi_kr_artists.json 매칭 820"
   - `pre_digest` / `post_digest`: 운영 source sha-256 / git diff
4. ⏳ 사용자 의 전수 수동 검수 (TP/FP/UNCERTAIN 판정 + judgment_reason)
5. ⏳ 결과 보고서 작성 (사용자 검수 결과 반영) + 코덱스 사후 검수
6. ⏳ **PR 작성 + merge** (pilot 자료 만 / 운영 경로 touch 금지 / adoption 신호 X 명시)

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Saatchi 재수집 의견 (2026-05-08) | year_made 우선순위 → birth_year 2순위 / regex 확장 만으로 몇 %p 오르는지 먼저 측정 / decision-binding X |
| 본 prereg round 1 사후 검수 (2026-05-08, NEEDS FIX) | P0×2 (fail-closed protocol binding 부족 / PR merge 의 adoption 오인) / P1×8 (regex `\|` literal 오류 / PASS rule 비대칭 / FP 기준 약 / 수동 검수 binding 부족 / regression-free 좁음 / P_NEW_1 false positive risk / P_NEW_1 false negative risk / 첫 매칭 우선 precision risk / validity range 근거 결손) / P2×3 (hypothesis vs PASS 분리 / §5 반복 / summary JSON 필드 명시) |
| 본 prereg round 2 사후 검수 (2026-05-08, NEEDS FIX) | P1×1 (§4.1 Precision 의 "0~1 FP 허용" 표현 의 수학적 부정확 — n=18-19 의 95% threshold 는 사실상 0 FP 만 PASS) — round 2 fix: 정확한 수학적 binding 표 명시 + n 별 (18 / 19 / 20 / 39 / 40) PASS 영역 의 정확 한 정수 round-down 표기 |
| 본 prereg round 3 사후 검수 (예정) | round 2 fix commit 직후 |
