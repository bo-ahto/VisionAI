# HO_TABLE 정확화 cycle — 결과 보고서

> **작성일**: 2026-05-08
> **Pre-registered**: `docs/ho_table_correction_prereg_20260508.md`
> **실행 코드**: `scripts/compute_ho_v2.py`
> **실행 결과**: `experiments/structural_v1/results/ho_table_correction_summary_20260508.json`
> **Decision binding**: ❌ **X** — record only / adoption inference 금지 / 운영 코드 / parquet / 모델 변경 X

## 0. 한 줄 요약

> **VERDICT (Reproducibility): ✅ PASS** — 표준 F 테이블 (`dimension_parser.py:33-42`) 의 22 entries import + np.interp 보간 적용 → cleansed Tier CSV (T0-T6) 의 9 신규 column 산출 / **51 → 60 column** 확장. 운영 ho 와 의 **mismatch = T0 의 54.44% (15,448 / 28,376)**. fail-closed protocol 통과 (frozen 15 path 변경 X). decision binding ❌ X.

## 1. PASS / FAIL 판정 (prereg §4.1 binding)

### 1.1 Reproducibility ✅ PASS

| 기준 | 결과 |
|---|---|
| HO_F_TABLE entries == 22 | ✅ |
| HO_F_TABLE[0] == (18.0, 14.0) | ✅ |
| HO_F_TABLE[200] == (259.1, 193.9) | ✅ |
| Frozen 15 path 변경 X (sha-256 + git diff) | ✅ |
| 7 Tier 모두 처리 (T0-T6) | ✅ |
| 모든 Tier 51 → 60 cols (9 신규 column 추가) | ✅ |
| ho_v2_int = np.rint(ho_v2).astype(int) (rounding rule freeze) | ✅ |
| column_dictionary backward (기존 5 row 의 사유 만 append) | ✅ |

### 1.2 Fail-closed (allowlist 기반)

| Frozen path 그룹 | n | 변경 |
|---|---|---|
| 운영 코드 (3 file: prepare_primary_market_dataset.py / primary_feature_builder.py / dimension_parser.py) | 3 | ✅ X |
| 운영 parquet (saatchi_cleaned.parquet / primary_market_dataset.parquet) | 2 | ✅ X |
| 기존 cleansed Tier CSV body (T0-T6 / 51 col 영역) | 7 | ✅ X |
| 기존 display_companion_T0.csv / human_readable_T0.csv / removed_columns_log.csv | 3 | ✅ X |
| **합계** | **15** | **모두 변경 X** |

## 2. 운영 ho vs ho_v2 mismatch (record only)

> 본 절 = 정량 record 만 / PASS-FAIL 미적용 / **운영 ho 의 잘못 인정 X / record only / adoption inference 금지** (prereg §5).

### 2.1 Tier 별 mismatch (artwork 단위)

| Tier | rows | exact | downgrade | upgrade | mismatch | mismatch% |
|---|---:|---:|---:|---:|---:|---:|
| T0 (28,376) | 28,376 | 12,928 | 7,967 | 7,481 | 15,448 | **54.44%** |
| T1 (7,289 Artsy) | 7,289 | 3,258 | 2,218 | 1,813 | 4,031 | 55.30% |
| T2 (7,231 +year) | 7,231 | 3,235 | 2,200 | 1,796 | 3,996 | 55.26% |
| T3 (5,845 +birth) | 5,845 | 2,597 | 1,792 | 1,456 | 3,248 | 55.57% |
| T4 (4,628 strict) | 4,628 | 2,027 | 1,436 | 1,165 | 2,601 | 56.20% |
| T5 (868 KRW) | 868 | 372 | 256 | 240 | 496 | 57.14% |
| T6 (4,460 anomaly free) | 4,460 | 1,954 | 1,361 | 1,145 | 2,506 | 56.19% |

> **모든 Tier 의 mismatch 비율 ≥ 54%**. 운영 의 정수 ho 와 표준 보간 ho_v2_int 의 절반 이상 차이. 코덱스 review 의 deterministic misclassification 정량 confirm.

### 2.2 Clipped / out-of-range flag

| Tier | clipped_low (area<252) | clipped_high (area>50,239) | size_oor (area<=0 or >250K) |
|---|---:|---:|---:|
| T0 | 358 | 131 | 0 |
| T1 | 44 | 79 | 0 |
| T2 | 44 | 79 | 0 |
| T3 | 41 | 71 | 0 |
| T4 | 33 | 57 | 0 |
| T5 | 7 | 27 | 0 |
| **T6 (anomaly free)** | **0** | **0** | **0** ⭐ |

> **T6 = audit rule-filter 적용 후 의 영역 / clipped 모두 0** = audit anomaly filter 의 효과 정합 (코덱스 권고 의 "관측 플래그" 의 실측 영역 가능).

### 2.3 ho_power 변화 분포 (T0 28,376 / 운영 ho_power vs ho_power_v2)

| 통계 | 값 (%) |
|---|---|
| min | -69.96% |
| p10 | -10.07% |
| p25 | -3.60% |
| p50 (median) | **0.00%** |
| p75 | +4.48% |
| p90 | +17.24% |
| max | +55.00% |
| mean | +1.68% |

> 운영 ho_power 의 약 **반수 가 ±10% 영역 변화**, **상위 10% 가 +17% 이상** / 하위 10% 가 -10% 이하. ho_power 의 가격 함수 영향 의 정량 (record only / efficacy 영역 X).

## 3. 산출 파일 (`data/dataset_tiers_cleansed_20260508/`)

| 파일 | rows | cols (이전 → 새) | 변경 |
|---|---:|---:|---|
| `T0_operational_28376_cleansed_with_ho_v2.csv` | 28,376 | 51 → **60** | 9 신규 column 추가 |
| `T1_artsy_only_cleansed_with_ho_v2.csv` | 7,289 | 51 → 60 | 9 신규 column 추가 |
| `T2_artsy_year_notna_cleansed_with_ho_v2.csv` | 7,231 | 51 → 60 | 9 신규 column 추가 |
| `T3_artsy_year_birth_notna_cleansed_with_ho_v2.csv` | 5,845 | 51 → 60 | 9 신규 column 추가 |
| `T4_artsy_strict_4field_cleansed_with_ho_v2.csv` | 4,628 | 51 → 60 | 9 신규 column 추가 |
| `T5_krw_only_cleansed_with_ho_v2.csv` | 868 | 51 → 60 | 9 신규 column 추가 |
| `T6_t4_anomaly_filtered_cleansed_with_ho_v2.csv` | 4,460 | 51 → 60 | 9 신규 column 추가 |
| `column_dictionary.csv` | 62 entries | 6 → 8 cols | 9 신규 row 추가 + 기존 5 row 사유 append |

> **기존 7 cleansed CSV (51 col) = 변경 X / 기존 column_dictionary 의 53 row 의 정의/생성방식/계산공식 = 변경 X (사유 만 append)**.

### 3.1 9 신규 column

| Column | 한글명 | 정의 |
|---|---|---|
| `ho_v2` | 호수(표준보간) | float64 / `area_to_ho_f` 의 np.interp 보간 |
| `ho_v2_int` | 호수(표준정수) | int / `np.rint(ho_v2).astype(int)` (half-to-even) |
| `ho_power_v2` | 호수^0.74(표준) | float64 / `ho_v2 ** 0.74 if ho_v2>0 else 0` |
| `ln_ho_v2` | 로그호수(표준) | float64 / `log(ho_v2 + 1)` |
| `is_small_v2` | 소형여부(표준) | int8 / `(ho_v2 <= 3.0) ? 1 : 0` |
| `ho_x_support_v2` | 호수×지지체계수(표준) | float64 / `ho_v2 × support_factor` |
| `is_ho_clipped_low_v2` | 호수하한클립 | int8 / `area_cm2 < 252.0` |
| `is_ho_clipped_high_v2` | 호수상한클립 | int8 / `area_cm2 > 50239.49` |
| `is_size_out_of_range_v2` | 크기범위외 | int8 / `area_cm2 ≤ 0.0 OR > 250000.0` |

## 4. Decision binding (반복 명시 — record only)

❌ **본 cycle = ho_v2 정량 record 만 / 분석적 증거 갱신 X / record only / adoption inference 금지**:

| 항목 | 본 cycle 의 영향 |
|---|---|
| Cycle 1 (cold validation) verdict (FAIL) | **변경 X** |
| B-2 (artifact reproducibility) verdict (PASS) | **변경 X** |
| Saatchi enrichment 복원 cycle (PR #51) verdict (PASS) | **변경 X** |
| birthyear regex pilot (PR #52) verdict (FAIL) | **변경 X** |
| Audit (PR #50) cleansed dataset 후보 (T0-T6) | **변경 X** (Tier 정의 / 51 col 보존) |
| Tier CSV cleanup (PR #53) | **변경 X** (51 col 보존 / 9 신규 column 추가 만) |
| 트랙 1 / 트랙 2 efficacy claim | **갱신 X** |
| 운영 채택 결정 | **영향 X** |
| 운영 코드 (`prepare_primary_market_dataset.py` / `primary_feature_builder.py` / `dimension_parser.py`) | **변경 X** |
| 운영 parquet | **변경 X** |
| 모델 retraining | **본 cycle 영역 외** (별도 decision-binding cycle 의무) |
| **본 PR merge** | record 의 기록 만 / 운영 경로 touch 금지 / adoption 신호 X |

> **운영 ho 의 잘못 인정 X**: 본 cycle = 운영 ho 와 표준 F 보간 ho_v2 의 정량 차이 의 record 만 / 운영 ho 의 잘못 / 표준 F 의 정확성 / 모델 가격 영향 모두 본 cycle 의 결정 영역 X.

## 5. 코덱스 권고 의 후속 cycle (사용자 결정 영역 / 본 cycle 영향 X)

| 후속 cycle | 영역 | 의무 |
|---|---|---|
| **운영 ho 의 표준 단일 소스 통합** | `prepare_primary_market_dataset.py` 의 `HO_TABLE_F` 제거 + `dimension_parser` import 의 운영 적용 | 별도 decision-binding prereg cycle (모델 retraining 의무) |
| **3안 offline backtest** | 운영 ho vs 표준 ho_v2 vs 타입별 F환산 의 가격 calibration 영향 측정 | 별도 prereg cycle (재학습 X / inference 만) |
| **canvas_type 활용 결정** | dead feature 제거 vs 타입별 F환산 연결 | 별도 prereg cycle |

## 6. 다음 단계

1. ✅ 본 결과 보고서 코덱스 사후 검수
2. ⏳ PR 작성 + merge (record only / 운영 경로 touch 금지)
3. ⏳ (사용자 결정) 후속 cycle 진입 결정

## 7. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| HO 변환 review (2026-05-08) | provenance 불명 / 표준 불일치 / canvas_type dead feature / silent clipping / 거버넌스 이중 정의 — high-risk 기록 |
| Prereg round 1 (NEEDS FIX): P1×4 + 보완×3 → fix |
| Prereg round 2 (NEEDS FIX): P1×2 (hardcoded 잔존 / 패턴 충돌) → fix |
| Prereg round 3 (**GO**) |
| 본 결과 보고서 사후 검수 (예정) | 본 commit 직후 |
