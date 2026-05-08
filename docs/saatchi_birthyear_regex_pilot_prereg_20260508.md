# Saatchi artist_birth_year regex 확장 pilot — Pre-Registered Analysis Plan

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: Saatchi `prepare_saatchi_dataset.py:101` 의 `extract_birth_year(bio)` 의 regex 패턴 을 사전 정의된 후보 로 확장 → 회수율 증분 측정 의 **pilot cycle**
> **Decision binding**: ❌ **X** — Cycle 1 / B-2 verdict 변경 X / 운영 saatchi_cleaned.parquet 변경 X / 운영 채택 결정 X / 모델 efficacy 비교 X
> **본 PASS = regex 회수 coverage 증분 측정 만**: efficacy PASS X / adoption PASS X / production candidate X
> **사전 자문**: 코덱스 (artist_birth_year 2순위 pilot 권고 / regex 확장 만으로 몇 %p 오르는지 먼저 측정)

> ⚠️ **본 cycle 의 scope 명시**:
> - **In-scope**: 사전 정의 된 regex 패턴 후보 의 추가 / 기존 35 작가 추출 결과 의 regression-free 정합 검증 / 회수율 증분 정량 / false positive 수동 sample 검수
> - **Out-of-scope**: 운영 `prepare_saatchi_dataset.py:101` 의 직접 변경 (운영 영향 차단) / 외부 source enrichment (Wikipedia / Artsy / 갤러리 — 별도 cycle) / 운영 모델 retraining / efficacy 비교

## 1. Goal

Saatchi 의 `artist_birth_year` 결손 영역 (832 unique artists 중 35 추출 / 4.21%) 을, **사전 정의된 추가 regex 패턴 으로 확장 시 의 회수율 증분 정량** 을 측정. 본 cycle = pilot / regex spec 의 정량 검증 만 / 운영 코드 변경 X.

**Hypothesis (PASS 조건 / restoration coverage 만)**:
- 기존 35 작가 추출 결과 = regression-free (모든 35 작가 가 새 regex 에서도 동일 birth year 추출)
- 새 regex 의 추가 추출 = 사전 정의된 패턴 의 정확한 매칭 영역 (사전 정의 외 패턴 추가 X)
- 추가 추출 작가 의 false positive 수동 검수 sample (≥10) = ≥ 90% 정확
- 회수율 증분 (artist 단위) ≥ 0.5%p (작아도 OK / 본 cycle = 측정 / decision X)

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

## 3. Method — 사전 정의된 추가 regex 패턴 (frozen)

### 3.1 추가 패턴 후보 (사전 정의 / 본 cycle 외 추가 금지)

bio 분석 결과 의 가장 빈번한 미커버 형식:

| # | 패턴 | 형식 | 예상 매칭 (72 unextracted_with_year 기준) |
|---|---|---|---|
| **P_NEW_1** | `r"(?i)born\s+in\s+[\w\s,]+?[,\s]+(?:in\s+)?(19[2-9]\d\|200[0-5])\b"` | `Born in [city/country] [in] [year]` | ~18 |
| **P_NEW_2** | `r"\b(19[2-9]\d\|200[0-5])\s+year\s+birth\b"` | `[year] year birth` | ~1 |

### 3.2 패턴 추가 의 정확성 보호

- **Validity range 동일 유지**: `1920 ≤ year ≤ 2005`
- **추출 우선순위**: 기존 5 패턴 의 첫 매칭 → 새 P_NEW_1 → P_NEW_2 (순차)
- **첫 매칭 우선**: `re.search` 의 첫 결과 만 (multiple match 시 첫 번째 의 year)
- **None fallback**: 모든 패턴 fail 시 None (기존 동작 유지)

### 3.3 운영 코드 변경 차단

- **`scripts/prepare_saatchi_dataset.py` 직접 변경 X** (운영 영향 차단)
- 본 cycle = 별도 module (`experiments/structural_v1/saatchi_birthyear_regex_pilot.py`) 에서 실험 적 함수 정의
- 결과 적용 시점 (운영 채택 결정 시 / 별도 prereg cycle 의무) 까지 운영 코드 freeze

### 3.4 False positive 검증

- 새 패턴 으로 추가 추출 된 작가 의 무작위 sample ≥ 10 (또는 추가 추출 전체 가 10 미만 시 전체)
- 각 sample 의 bio + 추출 birth_year 의 manual 정확성 검수 (사용자 검토 영역 / 본 cycle 의 결과 보고서 의 명시 자료)
- false positive 정의: bio 의 다른 year (전시 / 출판 / 활동 시작) 를 birth year 로 잘못 추출

## 4. PASS / FAIL 기준

### 4.1 PASS (모두 충족)

- ✅ Regression-free: 기존 35 작가 의 새 regex 추출 결과 = 기존 결과 와 정확 동일 (작가 별 동일 birth year)
- ✅ 추가 추출 작가 의 birth year 모두 1920-2005 범위 (validity range 정합)
- ✅ False positive 수동 sample 검수 정확률 ≥ 90% (또는 추가 추출 < 10 시 전수 검수)
- ✅ 회수율 증분 (artist 단위) ≥ 0.5%p **OR** 명확한 0%p (현실 한계 의 정량 confirm)
- ✅ 운영 `data/saatchi_cleaned.parquet` sha-256 = 변경 X
- ✅ 운영 `scripts/prepare_saatchi_dataset.py` 변경 X (코드 freeze)

### 4.2 FAIL

위 중 하나 미충족 → 별도 디버깅 cycle (본 prereg 미포함):
- Regression detect → 새 패턴 의 우선순위 / overlap 점검
- False positive ≥ 10% → 패턴 spec 점검 / validity range 강화 필요
- 운영 source 변경 detect → 절차 위반 / immediate abort

## 5. Decision binding

❌ **본 cycle = restoration coverage 측정 만 / 분석적 증거 갱신 X**:

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

**본 cycle 의 영향 영역 만**:
- ✅ regex 확장 의 회수율 증분 의 정량 측정 (artist 단위 + artwork 단위)
- ✅ False positive 수동 검수 자료 (사용자 의사결정 영역 의 입력)
- ✅ 후속 cycle (운영 코드 적용 / 별도 prereg cycle 의무) 의 정량 입력

## 6. 실행 protocol

1. ✅ 본 prereg 작성 + 코덱스 사후 검수
2. ⏳ Pilot 코드 작성 (`experiments/structural_v1/saatchi_birthyear_regex_pilot.py`)
   - 기존 + 신규 regex 패턴 의 함수 (운영 코드 변경 X)
   - 운영 saatchi_kr_artists.json 의 매칭 작가 (820) 영역 의 추출 시도
   - regression-free check (기존 35 작가 의 동일 결과)
   - 새 추출 작가 list (artist_id, name, bio 발췌, 추출 year)
   - 회수율 증분 정량 (artist 단위 + artwork 단위)
3. ⏳ 실행 + summary JSON 산출
4. ⏳ False positive 수동 검수 (사용자 영역 / 본 cycle 의 input 의무)
5. ⏳ 결과 보고서 작성 + 코덱스 사후 검수
6. ⏳ PR 작성 + merge

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| Saatchi 재수집 의견 (2026-05-08) | year_made 우선순위 → birth_year 2순위 / regex 확장 만으로 몇 %p 오르는지 먼저 측정 / decision-binding X |
| 본 prereg 사후 검수 (예정) | 본 commit 직후 |
