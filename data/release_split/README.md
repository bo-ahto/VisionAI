# Track 3 Release Split v3 — 데이터 사용 가이드

영구 분리된 학습/평가 데이터. 작가 단위 split + 동명이인 수동 검수 반영 + 학습용 컬럼 최소화.

> 🔴 **v3 주요 변경 (vs v1/v2)**
> 1. **동명이인 수동 검수 적용** — TRUE_homonym 40명 entity-level 정리 (한글명 뒤 `_A/_B/_C…` suffix로 구분).
> 2. **한글명 정정 3건** — 유수즈이→유수지, 이효윤→이효연, 이진우_B→이우진.
> 3. **학습용 컬럼 최소화** — 12 → **11 cols** (PR15 B_cm: `has_depth` 제거, `depth_cm`만 유지).
> 4. **source_platform 영구 제거** — 모델이 출처 bias 학습 못 함 (v2부터 유지).

## 📦 파일 구성

| 파일 | rows | 작가 | 비중 | 용도 |
|---|---:|---:|---:|---|
| `track3_train.csv` | 34,859 | 1,966 | 86.7% | **학습 전용** |
| `track3_test_warm.csv` | 1,717 | 1,717 | 4.3% | **Warm-start 평가** (학습된 작가의 신규 작품) |
| `track3_test_cold.csv` | 3,561 | 200 | 8.9% | **Cold-start 평가** (진짜 신규 작가) |
| `split_metadata.json` | — | — | — | 분리 정보 + homonym handling 설명 |

**전체 합계**: 40,137 rows (테스트 13.1%)

## 🔒 Leakage 방지 규칙 (반드시 준수)

### 분리 보장
- `train` ∩ `test_cold` 작가 = **0** (작가 단위 완전 분리, code에서 assert)
- `test_warm` 작가는 모두 `train`에 ≥1건 남아 있음

### 학습 시 필수 protocol
1. **`track3_train.csv`만 fit에 사용** — test 데이터 절대 보지 말 것
2. **모든 transform은 train만 보고 fit**:
   - Categorical vocabulary (artist_name_ko, medium 등)
   - Scaler (log_area, estimated_ho 등)
   - Bucket 경계 (ho_bucket 등)
   - Aggregate feature (artist_works_log 등)
3. **Test는 fitted transform으로 transform만**

### 잘못된 예 (절대 금지)
```python
# ❌ 전체 보고 fit
df_all = pd.concat([train, test_warm, test_cold])
df_all["artist_name_ko"] = df_all["artist_name_ko"].astype("category")  # leakage!

# ❌ artist 작품수 전체에서 계산
artist_works = df_all.groupby("artist_name_ko").size()  # leakage!
```

### 올바른 예
```python
# ✅ Aggregate feature는 train만 보고 계산
artist_works = train.groupby("artist_name_ko").size().to_dict()
train["artist_works_log"] = np.log1p(train["artist_name_ko"].map(artist_works).fillna(0))
test_warm["artist_works_log"] = np.log1p(test_warm["artist_name_ko"].map(artist_works).fillna(0))
test_cold["artist_works_log"] = np.log1p(test_cold["artist_name_ko"].map(artist_works).fillna(0))  # unseen → 0
```

## 📋 Schema — 학습용 11개 컬럼

> **사용자 요청**: 학습에 직접 쓰이지 않는 메타 컬럼은 모두 제거. 모델이 학습 외 정보를 우연히 참고하지 못함.

| Column | Type | 학습 input? | 비고 |
|---|---|---|---|
| `artist_name_ko` | str | ★ (Warm), ✗ (Cold) | **분리 ID** (동명이인은 `_A/_B/_C…` suffix) |
| `medium_category` | str | ★ | oil, acrylic, watercolor 등 [categorical] |
| `support_category` | str | ★ | canvas, paper, panel 등 [categorical] |
| `depth_cm` | float | ★ | 실측 깊이 (PR15 B_cm: `has_depth` 대체) |
| `width_cm` | float | △ | aspect_ratio derive용 |
| `height_cm` | float | △ | aspect_ratio derive용 |
| `log_area` | float | ★ | log(width × height) |
| `estimated_ho` | float | ★ | 한국 미술시장 호수 추정 |
| `orientation` | str | ★ | landscape/portrait/square [categorical] |
| `price_krw_unified` | int | 평가 시 원본 KRW | 학습 input 아님 |
| `ln_price_krw_unified` | float | **target** | 자연로그 변환 가격 |

추가 derive (학습 시 직접 생성, train만 보고):
- `medium_ho_bucket` = medium × ho_bucket (interaction)
- `aspect_ratio` = log(width / height)
- `artist_works_log` = log1p(train 작가 작품 수)

### 제거된 컬럼 (학습 외 메타)
- ~~`source_platform`~~ — Artsy +45.5% bias 차단 (v2부터)
- ~~`source_listing_id`~~, ~~`artist_entity_id_raw`~~, ~~`artist_name_raw`~~ — 메타 ID
- ~~`has_depth`~~ — PR15 B_cm: 2D 작품 부작용 차단 위해 제거 (v3)
- ~~`area_cm2`~~ — log_area로 derive 가능
- ~~`is_outlier`~~ — 모두 0 (필터링 완료)
- ~~`artist_name_ko_orig`, `is_homonym`, `artist_entity_suffix`~~ — 동명이인 메타 (학습 외)
- ~~`price_amount_raw`, `price_currency_raw`, `price_krw`, `was_converted`~~ — 원본 가격 형식

## 🆔 동명이인 처리 (v3)

### 작가 ID 구조
- **일반 작가**: 한글명 그대로 (`황선태`, `이우환` 등)
- **동명이인 분리 작가**: 한글명 뒤 `_A`, `_B`, `_C`… suffix
  - 예: `구자현_A` (Artsy `koo-ja-hyun` 21건), `구자현_B` (Artsy `jahyun-koo` 18건), `구자현_C` (Artsy `koo-ja-hyun-2` 15건)
  - 메인 entity (작품수 가장 많은) = `_A`, 보조는 작품수 내림차순으로 `_B`, `_C`…

### 처리 과정
1. PR16: `(artist_name_ko, artist_entity_id_raw, source_platform)` 조합으로 자동 식별 → 38명 분리
2. PR16e: 수동 검수 적용 (`data/homonym_review/`)
   - **MERGE**: 같은 사람으로 확인된 entity는 `_A` 등 target ID로 통합 (Artue의 작품별 entity 합침)
   - **KEEP**: 다른 사람 확정 → 그대로 유지 (예: `김유리_A` Saatchi 180건 vs `김유리_B` Saatchi 8건)
   - **RENAME**: 한글명 정정 (유수즈이→유수지, 이효윤→이효연, 이진우_B→이우진)

### 결과
- 원본 한글명 작가 수: 2,175
- v2 분리 후: 2,370 (+195 over-split 포함)
- **v3 수동 검수 후: 2,209** (Artue over-split 정리)

### 검수 자료 (수작업용)
- `data/track3_unified_v3.csv` — 모든 메타 포함 전체 데이터 (25 cols)
- `data/homonym_review/manual_review.csv` — 동명이인 검수 결과

## 📊 분포 정보

### 가격 분포 (KRW, median)

| Set | median | Q25 | Q75 |
|---|---:|---:|---:|
| train | ~2.79M | ~1.2M | ~6.9M |
| test_warm | ~2.9M | ~1.24M | ~7.0M |
| test_cold | **~2.25M** | ~0.83M | ~5.4M |

⚠️ **test_cold가 train보다 약간 낮음** — cold 작가는 low/mid에 더 분포. covariate shift 가능성, **per-source metric** 함께 보고 권장.

### Cold 작가 stratification (seed=42)

| Group | 기준 | train pool | cold test 선정 |
|---|---|---:|---:|
| low | 작품 ≤2건 | ~510명 | 100명 (50%) |
| mid | 작품 3-10건 | ~820명 | 60명 (30%) |
| high | 작품 >10건 | ~870명 | 40명 (20%) |
| **합계** | | **2,209명** | **200명** |

## 🎯 평가 protocol

### 권장 metric
- **median APE** (primary) — outlier robust
- **MAPE** — outlier 민감
- **RMSE (log)**
- **Within-30%** — 실용 정확도
- **Within-50%**

### 보고 형식 권장
```
[Warm-start] (test_warm n=1,717)
  median APE: XX.X% / W30: XX.X%

[Cold-start] (test_cold n=3,561)
  median APE: XX.X% / W30: XX.X%

[Overall] (warm + cold)
  median APE: XX.X% (보조 지표)
```

→ **반드시 Warm / Cold 분리 보고** (단일 평균은 두 시나리오 난이도를 가림).

### 운영 라우팅 시뮬레이션
- 실 운영: `train_count >= 1` → Warm, `== 0` → Cold
- 평가도 동일: test_warm은 Warm 모델, test_cold는 Cold 모델

## 📁 생성 코드

- `scripts/track3/pr16e_apply_manual_review.py` — manual review 적용 + release_split 재생성 (seed=42, 재현 가능)
- `scripts/track3/pr16_homonym_label.py` — entity_id 기반 자동 분리 라벨링 (v2 단계)

## ⚠️ 알려진 한계

1. **listing-price prediction** — 시장가치 예측 아님
2. **시간 split 없음** — temporal validation 불가
3. **>100M Cold** 작품은 사실상 예측 불가 (운영 시 비공개 권장)
4. **Source 정보 없음** → Artsy 마크업 (+45.5%) bias 학습 못 함
5. **test_warm은 작가당 1건** → 작가별 신뢰도 낮음 (overall만 의미)
6. **test_cold는 covariate shift 가능** — price 분포가 train과 약간 다름
7. **동명이인 38명 → 정리됨** (v3에서 수동 검수 반영)
