# HO_TABLE 정확화 cycle — Pre-Registered Analysis Plan

> **작성일**: 2026-05-08
> **본 cycle 의 본질**: 운영 `prepare_primary_market_dataset.py:27` 의 `HO_TABLE_F` 의 표준 F 규격 불일치 (코덱스 review 의 deterministic misclassification 발견) → 별도 표준 보간 함수 적용 한 ho_v2 column 산출 + cleansed Tier CSV 업데이트
> **Decision binding**: ❌ **X** — 운영 코드 변경 X / 운영 parquet 변경 X / Cycle 1 / B-2 / 복원 / pilot / Audit / Cleanup verdict 모두 변경 X / 운영 retrain X
> **본 PASS = 정량 비교 record + ho_v2 column 산출 의 reproducibility 만**: efficacy PASS X / adoption PASS X / production candidate X
> **사전 자문**: 코덱스 (HO_TABLE_F provenance 불명 + 표준 불일치 high-risk / 표준 단일 소스 통합 = 별도 결정 안건 / 관측 플래그 권고)

> ⚠️ **본 cycle 의 scope 명시**:
> - **In-scope**: 표준 F 테이블 (`dimension_parser.py:33`) 적용 한 ho_v2 / ho_power_v2 / ln_ho_v2 / ho_x_support_v2 / is_small_v2 산출 + clipped flag 산출 + 운영 ho vs ho_v2 정량 비교 + cleansed Tier CSV update (별도 column 추가 / 기존 ho 영역 보존)
> - **Out-of-scope**: 운영 코드 (`prepare_primary_market_dataset.py` / `primary_feature_builder.py`) 변경 / 운영 parquet 변경 / 모델 retraining / efficacy 비교 (offline backtest 별도 cycle)

## 1. Goal

운영 `HO_TABLE_F` 의 표준 F 규격 불일치 (코덱스 inspection 결과: 작은 호수 영역 ±20-34% / 중대형 영역 ±10-20% 차이) 영역 의 **표준 보간 함수 적용 결과 의 정량 record** + cleansed Tier CSV 의 ho 영역 의 별도 column 추가.

**Hypothesis (PASS 조건 / 정량 record 만)**:
- 표준 F 테이블 (`HO_F_TABLE` from `dimension_parser.py:33`) 의 area_to_ho_f 보간 함수 정확 구현
- 운영 ho vs ho_v2 의 mismatch 정량 (artist 단위 / artwork 단위)
- clipped flag (`is_ho_clipped_low / is_ho_clipped_high / is_size_out_of_range`) 의 정량 산출
- cleansed Tier CSV 에 새 column 추가 (기존 ho 영역 보존 / column 영역 만 추가)
- 운영 코드 / parquet / column dictionary 의 ho 영역 의 기존 정의 변경 X

> **본 PASS = ho_v2 산출 의 reproducibility 만**. efficacy PASS X / adoption PASS X / 운영 ho 의 잘못 인정 X (단순 정량 기록).

## 2. 표준 F 테이블 freeze

### 2.1 표준 F 테이블 (`src/visionai/price_engine/preprocessing/dimension_parser.py:33-42`)

```python
HO_F_TABLE = {
    0: (18.0, 14.0),     # area = 252
    1: (22.7, 15.8),     # 358.66
    2: (25.8, 17.9),     # 461.82
    3: (27.3, 22.0),     # 600.60
    4: (33.4, 24.2),     # 808.28
    5: (34.8, 27.3),     # 950.04
    6: (40.9, 31.8),     # 1300.62
    8: (45.5, 37.9),     # 1724.45
    10: (53.0, 45.5),    # 2411.50
    12: (60.6, 50.0),    # 3030.00
    15: (65.1, 53.0),    # 3450.30
    20: (72.7, 60.6),    # 4405.62
    25: (80.3, 65.1),    # 5227.53
    30: (90.9, 72.7),    # 6608.43
    40: (100.0, 80.3),   # 8030.00
    50: (116.8, 91.0),   # 10628.80
    60: (130.3, 97.0),   # 12639.10
    80: (145.5, 112.1),  # 16310.55
    100: (162.2, 130.3), # 21134.66
    120: (193.9, 130.3), # 25265.17
    150: (227.3, 181.8), # 41323.14
    200: (259.1, 193.9), # 50239.49
}
```

### 2.2 표준 보간 함수 (`dimension_parser.py:48-52`)

```python
def area_to_ho_f(surface_area: float) -> float:
    if surface_area <= 0 or not np.isfinite(surface_area):
        return 0.0
    return float(np.interp(surface_area, _HO_AREAS, _HO_KEYS))
```

`np.interp` 의 linear interpolation = float ho 반환 (운영 의 argmin 정수 vs 표준 의 float continuous 보간 의 차이).

### 2.3 운영 vs 표준 의 핵심 차이

| 호수 | 운영 area (cm²) | 표준 area (cm²) | 차이% |
|---|---|---|---|
| 0 | 180 | 252 | **-28.6%** |
| 1 | 364 | 358.66 | +1.5% |
| 3 | 727 | 600.60 | **+21.0%** |
| 4 | 1084 | 808.28 | **+34.1%** |
| 5 | 1167 | 950.04 | +22.9% |
| 30 | 5858 | 6608.43 | -11.4% |
| 50 | 9128 | 10628.80 | -14.1% |
| 150 | 33894 | 41323.14 | **-18.0%** |
| 200 | 43980 | 50239.49 | -12.5% |

## 3. Method

### 3.1 ho_v2 산출 (별도 함수 / 운영 코드 변경 X)

본 cycle 의 별도 module (`scripts/compute_ho_v2.py`) 에서:

1. 표준 `HO_F_TABLE` **import 원칙** (`from visionai.price_engine.preprocessing.dimension_parser import HO_F_TABLE, area_to_ho_f`). hardcoded copy 사용 금지 (단일 source 통합 원칙).
2. 각 cleansed Tier CSV 의 `area_cm2` 에 `area_to_ho_f` 적용 → `ho_v2` (float, dtype=`float64`)
3. 정수 호수 비교 영역: `ho_v2_int = np.rint(ho_v2).astype(int)` (= half-to-even / numpy default / **rounding rule freeze**)
4. Derived columns 재계산 (모두 float, dtype=float64):
   - `ho_power_v2 = ho_v2 ** 0.74 if ho_v2 > 0 else 0`
   - `ln_ho_v2 = log(ho_v2 + 1)`
   - `is_small_v2 = (ho_v2 <= 3.0) ? 1 : 0` (int8 binary)
   - `ho_x_support_v2 = ho_v2 * support_factor`

> **Rounding rule binding**: `np.rint` 의 banker's rounding (half-to-even) 으로 고정 / Python `round` / `Decimal` 사용 금지. tie 영역 (예: ho_v2 = 0.5 / 1.5 / 2.5) = numpy 기본 (가장 가까운 even). `mismatch_int = (operational_ho != ho_v2_int)` exact rule.

### 3.2 Clipped / out-of-range flag (코덱스 권고)

| Flag | Threshold (절대값) | 비교 연산자 |
|---|---|---|
| `is_ho_clipped_low_v2` | `area_cm2 < 252.0` | `<` (strict less than) |
| `is_ho_clipped_high_v2` | `area_cm2 > 50239.49` | `>` (strict greater than) |
| `is_size_out_of_range_v2` | `area_cm2 <= 0.0` OR `area_cm2 > 250000.0` | `<=` / `>` |

> **Threshold 영역 의 의미**:
> - `252.0` = `HO_F_TABLE[0]` (= 18.0 × 14.0 / 표준 0호 area)
> - `50239.49` = `HO_F_TABLE[200]` 의 area (= 259.1 × 193.9 / 표준 200호 area)
> - `250000.0` = 약 500cm × 500cm (대형 작품 의 상한 / 운영 max 187,200 cm² 보다 크게 설정)

### 3.3 운영 ho vs ho_v2 mismatch 정량

- 28,376 rows (T0) 의 운영 `ho` (정수) vs `ho_v2_int` 의 mismatch count
- mismatch 영역 의 분포 (downgrade / upgrade / 정확 동일)
- artist 단위 mismatch (작가 별 평균 ho 변경)
- ho_power 의 변화 (`(ho_power_v2 - ho_power) / ho_power` 의 분포)

### 3.4 cleansed Tier CSV update (별도 column 추가 / 기존 보존)

각 cleansed Tier CSV (T0~T6) 에 다음 **9 column** 추가 (기존 51 column 영역 변경 X):

```
ho_v2                   (float64 / 표준 보간)
ho_v2_int               (int / np.rint half-to-even)
ho_power_v2             (float64 / ho_v2 ^ 0.74)
ln_ho_v2                (float64 / log(ho_v2+1))
is_small_v2             (int8 / ho_v2 <= 3.0)
ho_x_support_v2         (float64 / ho_v2 × support_factor)
is_ho_clipped_low_v2    (int8 / area_cm2 < 252.0)
is_ho_clipped_high_v2   (int8 / area_cm2 > 50239.49)
is_size_out_of_range_v2 (int8 / area_cm2 <= 0.0 OR > 250000.0)
```

→ 9 column 추가 / 기존 51 column → **60 column** cleansed CSV (별도 file / `*_with_ho_v2.csv` suffix).

### 3.5 column_dictionary 업데이트 (backward-compatible)

- 9 신규 column 의 row 추가 (53 → 62 entries)
- **기존 5 row (ho / ho_power / ln_ho / is_small / ho_x_support) 의 backward-compatible 보강**:
  - `정의` / `생성방식` / `계산공식` column = **불변 freeze** (기존 spec 보호)
  - `사유` column 에만 `+ high-risk: 표준 F 규격 불일치 (코덱스 review / ho_v2 별도 산출)` append
  - 추가 / 변경 영역 의 audit 가능성 보장

### 3.6 Fail-closed protocol (repo-wide allowlist)

본 cycle 의 변경 허용 경로 (allowlist) — **그 외 diff 발생 시 즉시 abort**:

#### Allowed (변경 허용)
| 경로 | 영역 |
|---|---|
| `scripts/compute_ho_v2.py` | 신규 산출 코드 |
| `data/dataset_tiers_cleansed_20260508/*_with_ho_v2.csv` | 9 column 추가 cleansed CSV (T0-T6) |
| `data/dataset_tiers_cleansed_20260508/column_dictionary.csv` | 53 → 62 entries (기존 row 의 사유 만 append / 정의/공식/생성방식 불변) |
| `data/dataset_tiers_cleansed_20260508/INDEX.md` / `INDEX.json` | 설명 영역 update |
| `experiments/structural_v1/results/ho_table_correction_summary_20260508.json` | 정량 record |
| `docs/ho_table_correction_prereg_20260508.md` | prereg (본 file) |
| `docs/ho_table_correction_results_20260508.md` | 결과 보고서 |

#### Frozen (변경 금지 / pre/post sha-256 검증 의무)
| 경로 | 영역 |
|---|---|
| `scripts/prepare_primary_market_dataset.py` | 운영 코드 (HO_TABLE_F freeze) |
| `src/visionai/price_engine/api/primary_feature_builder.py` | 운영 inference 코드 |
| `src/visionai/price_engine/preprocessing/dimension_parser.py` | 표준 F 테이블 source (read-only import) |
| `data/saatchi_cleaned.parquet` | 운영 raw |
| `data/primary_market_dataset.parquet` | 운영 raw |
| `data/dataset_tiers_cleansed_20260508/T0_operational_28376_cleansed.csv` | 기존 cleansed CSV body (51 col / 명시 열거) |
| `data/dataset_tiers_cleansed_20260508/T1_artsy_only_cleansed.csv` | 기존 cleansed CSV body (51 col / 명시 열거) |
| `data/dataset_tiers_cleansed_20260508/T2_artsy_year_notna_cleansed.csv` | 기존 cleansed CSV body (51 col / 명시 열거) |
| `data/dataset_tiers_cleansed_20260508/T3_artsy_year_birth_notna_cleansed.csv` | 기존 cleansed CSV body (51 col / 명시 열거) |
| `data/dataset_tiers_cleansed_20260508/T4_artsy_strict_4field_cleansed.csv` | 기존 cleansed CSV body (51 col / 명시 열거) |
| `data/dataset_tiers_cleansed_20260508/T5_krw_only_cleansed.csv` | 기존 cleansed CSV body (51 col / 명시 열거) |
| `data/dataset_tiers_cleansed_20260508/T6_t4_anomaly_filtered_cleansed.csv` | 기존 cleansed CSV body (51 col / 명시 열거) |
| `data/dataset_tiers_cleansed_20260508/display_companion_T0.csv` | 기존 display companion |
| `data/dataset_tiers_cleansed_20260508/human_readable_T0.csv` | 기존 한글 파생본 |
| `data/dataset_tiers_cleansed_20260508/removed_columns_log.csv` | 기존 제거 record |

#### Fail-closed 검증 protocol

1. 실행 시작 시 **frozen list 의 모든 path 의 sha-256 + git diff lines 기록** (logger info)
2. **Output path 가 allowlist 외 / Frozen list 의 경로 인 경우 즉시 abort** (코드 레벨 가드)
3. 실행 직후 **frozen list 의 모든 path 의 sha-256 / git diff 재산출 → pre-run digest 와 정확 동일 검증**
4. 불일치 detect 시 = `RuntimeError("FAIL-CLOSED: <path> changed during run")` raise + rollback 의무

## 4. PASS / FAIL 기준

### 4.1 PASS (모두 충족)

#### Reproducibility
- ✅ 표준 F 테이블 정확 구현 (운영 `dimension_parser.py:33-42` 의 22 entries 의 import + assertion: `len(HO_F_TABLE) == 22 AND HO_F_TABLE[0] == (18.0, 14.0) AND HO_F_TABLE[200] == (259.1, 193.9)` 등 spot-check)
- ✅ ho_v2 산출 = `area_to_ho_f(area_cm2)` 의 정확 결과 (= `np.interp(area_cm2, _HO_AREAS, _HO_KEYS)` 의 spec)
- ✅ ho_v2_int = `np.rint(ho_v2).astype(int)` (rounding rule freeze)
- ✅ Derived columns (ho_power_v2 / ln_ho_v2 / is_small_v2 / ho_x_support_v2) 의 정의 일치
- ✅ cleansed Tier CSV 업데이트 = 기존 51 column 변경 X / 9 신규 column 추가 = **60 column**

#### Fail-closed (allowlist 기반 / §3.6)
- ✅ Frozen list 의 모든 path 의 pre/post sha-256 정확 동일
- ✅ Output path 가 allowlist 의 경로 만 (그 외 = 즉시 abort)
- ✅ column_dictionary 의 기존 ho 계열 5 row 의 `정의` / `생성방식` / `계산공식` 불변 (사유 만 append)

#### 정량 record (보고값 / PASS-FAIL 미적용)
- 운영 ho vs ho_v2_int mismatch 의 정량 (artist 단위 + artwork 단위) — 결과 보고서 record 만
- ho_power 변화 분포 — record 만
- clipped flag 의 정량 — record 만

### 4.2 FAIL

위 PASS 조건 중 하나 미충족 → 별도 디버깅 cycle (본 prereg 미포함):
- 운영 코드 / parquet 변경 detect → fail-closed abort + rollback
- 표준 F 테이블 의 22 entries mismatch → import / 복사 spec 점검
- ho_v2 산출 의 spec 차이 → 코드 점검

## 5. Decision binding (반복 명시)

❌ **본 cycle = ho_v2 정량 record 만 / 분석적 증거 갱신 X**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | **변경 X** |
| B-2 (artifact reproducibility) verdict (PASS) | **변경 X** |
| Saatchi enrichment 복원 cycle (PR #51) verdict (PASS) | **변경 X** |
| birthyear regex pilot (PR #52) verdict (FAIL) | **변경 X** |
| Audit (PR #50) cleansed dataset 후보 (T0-T6) | **변경 X** (Tier 정의 변경 X / column 영역 추가 만) |
| Tier CSV cleanup (PR #53) | **변경 X** (51 column 보존 / 9 신규 column 추가) |
| 트랙 1 / 트랙 2 efficacy claim | **갱신 X** |
| 운영 채택 결정 | **영향 X** |
| 운영 `prepare_primary_market_dataset.py` / `primary_feature_builder.py` | **변경 X** (코드 freeze) |
| 운영 parquet | **변경 X** (read-only) |
| 모델 retraining | **본 cycle 영역 외** (별도 decision-binding cycle 의무) |

**본 cycle 의 영향 영역 만**:
- ✅ ho_v2 column 의 cleansed Tier CSV 업데이트 (기존 51 column 보존)
- ✅ 운영 ho vs ho_v2 의 정량 mismatch record (사용자 의 후속 결정 영역 의 정량 입력)
- ✅ column_dictionary 의 ho 영역 의 high-risk 사유 추가

> **본 cycle 의 PASS = 운영 ho 의 표준 불일치 의 정량 confirm 만 (record only / adoption inference 금지)**. 운영 코드 의 표준 단일 소스 통합 / 모델 retraining = 별도 decision-binding cycle 의무 (코덱스 권고 영역). 결과 보고서 의 모든 정량 = adoption / efficacy / 운영 채택 결정 의 직접 근거 X.

## 6. 실행 protocol

1. ✅ 본 prereg 작성 + 코덱스 사후 검수
2. ⏳ 산출 코드 작성 (`scripts/compute_ho_v2.py`)
   - 표준 F 테이블 import (`from visionai.price_engine.preprocessing.dimension_parser import HO_F_TABLE, area_to_ho_f` 만 / hardcoded copy 금지 / §3.1 정합)
   - cleansed Tier CSV 의 area_cm2 에 area_to_ho_f 적용 → 9 신규 column 산출
   - 운영 ho vs ho_v2 mismatch 정량 + clipped flag 정량
   - fail-closed digest 검증 (pre/post)
3. ⏳ 실행 + summary JSON 산출
4. ⏳ cleansed Tier CSV update (`*_with_ho_v2.csv`)
5. ⏳ column_dictionary update (62 entries / ho 영역 high-risk 사유 추가)
6. ⏳ 결과 보고서 작성
7. ⏳ 결과 보고서 코덱스 사후 검수
8. ⏳ PR 작성 + merge

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| HO 변환 review (2026-05-08) | provenance 불명 / 표준 불일치 / canvas_type dead feature / silent clipping / calibration 영향 / 거버넌스 이중 정의 (1차시장 hardcoded vs 경매 dimension_parser) — high-risk 기록 + 표준 단일 소스 통합 별도 결정 안건 + 관측 플래그 권고 + 3안 offline backtest 권고 |
| 본 prereg round 1 사후 검수 (2026-05-08, NEEDS FIX) | P1×4 (fail-closed allowlist 결손 / ho_v2_int rounding rule / 표준 table import 원칙 / 8↔9 column 오타) + 보완 3 (clipped threshold 절대값 / dictionary backward append / record only 반복) — round 1 fix |
| 본 prereg round 2 사후 검수 (2026-05-08, NEEDS FIX) | P1×2 (§6 step 2 의 "또는 hardcoded copy" 문구 잔존 — §3.1 정합 X / §3.6 frozen `T*_*.csv` 패턴 이 allowed `*_with_ho_v2.csv` 와 겹침) — round 2 fix: frozen list 의 7 cleansed CSV 명시 열거 + step 2 import 원칙 만 |
| 본 prereg round 3 사후 검수 (예정) | round 2 fix commit 직후 |
