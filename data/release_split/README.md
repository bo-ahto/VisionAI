# Track 3 Release Split — 데이터 사용 가이드

영구 분리된 학습/평가 데이터. Codex 검수 통과 (Hybrid 분리).

## 📦 파일 구성

| 파일 | rows | 작가 | 비중 | 용도 |
|---|---:|---:|---:|---|
| `track3_train.csv` | 34,629 | 1,932 | 86.3% | **학습 전용** |
| `track3_test_warm.csv` | 1,685 | 1,685 | 4.2% | **Warm-start 평가** (학습된 작가의 신규 작품) |
| `track3_test_cold.csv` | 3,823 | 200 | 9.5% | **Cold-start 평가** (진짜 신규 작가) |
| `split_metadata.json` | — | — | — | 분리 정보 |

**Test 총량**: 5,508 rows (13.7%)

## 🔒 Leakage 방지 규칙 (반드시 준수)

### 분리 보장
- `train` ∩ `test_cold` 작가 = **0** (완전 분리, 검증됨)
- `test_warm` 작가는 모두 `train`에 ≥1건 남아 있음 (warm 평가 가능)

### 학습 시 필수 프로토콜
1. **`track3_train.csv`만 fit에 사용** — test 데이터 절대 보지 말 것
2. **모든 transform은 train만 보고 fit**:
   - Categorical vocabulary (artist_name_ko, medium 등)
   - Scaler (log_area, estimated_ho 등)
   - Bucket 경계 (ho_bucket 등)
   - Target encoding 등 aggregate feature
3. **Test는 fitted transform으로 transform만** (재학습 X)

### 잘못된 예 (절대 금지)
```python
# ❌ 잘못된 방법: 전체 보고 fit
df_all = pd.concat([train, test_warm, test_cold])
df_all["artist_name_ko"] = df_all["artist_name_ko"].astype("category")  # ← leakage!

# ❌ 잘못된 방법: artist 작품수 전체에서 계산
artist_works = df_all.groupby("artist_name_ko").size()  # ← leakage!
```

### 올바른 예
```python
# ✅ Categorical fit은 train만 보고
train_cats = pd.Categorical(train["artist_name_ko"]).categories
dtype = pd.CategoricalDtype(categories=train_cats)
train["artist_name_ko"] = train["artist_name_ko"].astype(dtype)
test_warm["artist_name_ko"] = test_warm["artist_name_ko"].astype(dtype)  # train 카테고리만

# ✅ Aggregate feature는 train만 보고 계산
artist_works = train.groupby("artist_name_ko").size().to_dict()
train["artist_works_log"] = np.log1p(train["artist_name_ko"].map(artist_works).fillna(0))
test_warm["artist_works_log"] = np.log1p(test_warm["artist_name_ko"].map(artist_works).fillna(0))
# test_cold는 unseen 작가 → 0
test_cold["artist_works_log"] = np.log1p(test_cold["artist_name_ko"].map(artist_works).fillna(0))
```

## 📊 분포 정보

### Source 분포

| Source | train | test_warm | test_cold |
|---|---:|---:|---:|
| Saatchi | 23,163 (67%) | 756 (45%) | 2,925 (77%) |
| Artsy | 9,247 (27%) | 703 (42%) | 634 (17%) |
| Artue | 2,219 (6%) | 226 (13%) | 264 (7%) |

⚠️ **test_warm은 source 분포가 train과 다름** — "artist-held-out warm probe" 성격 (각 작가별 1건씩 무작위 빼서 작가 다양성 우선).
⚠️ **test_cold는 Artsy 비중 17%로 낮음** — covariate shift 가능. **per-source metric** 함께 보고 권장.

### 가격 분포 (KRW, median)

| Set | median | Q25 | Q75 |
|---|---:|---:|---:|
| train | 2,787,600 | 1,214,400 | 6,900,000 |
| test_warm | 2,898,000 | 1,242,000 | 7,000,000 |
| test_cold | **2,249,400** | 828,000 | 5,444,100 |

⚠️ **test_cold price median이 train보다 낮음** (2.25M vs 2.79M) — cold 작가는 low/mid에 더 분포됨. **covariate shift** 가능성, 성능이 더 낮게 나올 수 있음.

### Cold 작가 stratification (seed=42)

| Group | 기준 | train pool | cold test 선정 |
|---|---|---:|---:|
| low | 작품 ≤2건 | 516명 | 100명 (50%) |
| mid | 작품 3-10건 | 820명 | 60명 (30%) |
| high | 작품 >10건 | 796명 | 40명 (20%) |
| **합계** | | **2,132명** | **200명** |

## 🎯 평가 프로토콜

### 권장 metric
- **median APE** (primary) — outlier robust
- **MAPE**
- **RMSE (log)**
- **Within-30%** — 실용 정확도
- **Within-50%**

### 권장 보고 형식
```
[Warm-start] (test_warm n=1,685)
  median APE: XX.X% / W30: XX.X%
  per-source: artsy XX.X / saatchi XX.X / artue XX.X

[Cold-start] (test_cold n=3,823)
  median APE: XX.X% / W30: XX.X%
  per-source: artsy XX.X / saatchi XX.X / artue XX.X

[Overall] (warm + cold)
  median APE: XX.X% (보조 지표)
```

→ **반드시 Warm / Cold 분리 보고** (단일 평균 metric은 두 시나리오의 다른 난이도를 가림).

### 평가 시 운영 라우팅 시뮬레이션
- 실 운영 모델은 `train_count >= 1` → Warm, `== 0` → Cold 라우팅
- 평가도 동일: test_warm에는 Warm 모델, test_cold에는 Cold 모델 적용

## 📋 Schema (모든 CSV 공통, 22 columns)

| Column | Type | 학습 input? |
|---|---|---|
| `artist_name_ko` | str | ★ (Warm), ✗ (Cold) |
| `medium_category` | str | ★ |
| `support_category` | str | ★ |
| `has_depth` | int | △ (제거 가능, PR11 결과) |
| `depth_cm` | float | △ |
| `width_cm` | float | △ |
| `height_cm` | float | △ |
| `area_cm2` | float | △ |
| `log_area` | float | ★ |
| `estimated_ho` | float | ★ |
| `orientation` | str | ★ |
| `is_outlier` | int | (이미 0만 포함) |
| `source_platform` | str | ★ (PR5 Artsy +45.5% bias) |
| `price_amount_raw` | float | — |
| `price_currency_raw` | str | — |
| `price_krw` | float | — |
| `was_converted` | int | — |
| `price_krw_unified` | int | (raw target) |
| `ln_price_krw_unified` | float | **target (학습용)** |
| `source_listing_id` | str | (메타) |
| `artist_entity_id_raw` | str | (메타) |
| `artist_name_raw` | str | (메타) |

추가 derive (학습 시 직접 생성, train만 보고):
- `medium_ho_bucket` = medium × ho_bucket interaction
- `aspect_ratio` = log(width / height)
- `artist_works_log` = log1p(train 작가 작품 수)

## 📁 생성 코드

`scripts/track3/split_for_release.py` — seed=42, 재현 가능.

## ⚠️ 알려진 한계

1. **listing-price prediction** (시장가치 아님)
2. **시간 split 없음** — temporal validation 불가
3. **>100M Cold** 작품은 사실상 예측 불가 (운영 시 비공개 권장)
4. **Source 정보 없음** → ±20-45% 오차 가능 (Artsy 마크업)
5. **test_warm은 작가당 1건만** → 작가별 신뢰도 낮음 (overall만 의미)
6. **test_cold는 covariate shift 가능** (price/source 분포가 train과 약간 다름)
