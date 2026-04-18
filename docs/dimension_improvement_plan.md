# 크기(호수) 처리 개선안 (v1.0)

> **작성일**: 2026-03-30
> **기반**: Codex 리뷰 MAJOR 4건 + 한국 캔버스 호수 규격표 분석

---

## 1. 현재 문제 진단

### 1.1 호수 상수 132의 왜곡

현재 `size_ho = surface_area / 132`로 변환하는데, 실제 호수 체계와 크게 괴리됩니다:

| 실제 호수 | F 면적 (cm²) | /132 결과 | 오차 |
|----------|------------|----------|------|
| 10호 | 2,412 | **18.3** | +8.3 (83% 과대) |
| 20호 | 4,406 | **33.4** | +13.4 (67% 과대) |
| 40호 | 8,030 | **60.8** | +20.8 (52% 과대) |
| 100호 | 21,135 | **160.1** | +60.1 (60% 과대) |

**문제**: 132는 실제 1호 면적(358.7cm²)과도 맞지 않고, 호수당 평균 면적(~210cm²)과도 다릅니다. "호수"라는 이름으로 쓰기에 부적절합니다.

### 1.2 40호 hinge 위치 불일치

`size_ho_above40 = max(0, size_ho - 40)`에서 40은 "40호"를 의미하지만:
- 132 기준 40 = **5,280cm²** → 실제 25호F(5,228cm²)와 거의 일치
- 실제 40호F = **8,030cm²** → 132 기준 **60.8**

**결론**: hinge가 실제 40호(8,030cm²)가 아닌 **~25호(5,228cm²) 부근**에 놓여 있습니다.

### 1.3 결측 대체 미연결

`impute_surface_area()`가 정의만 있고 실제 파이프라인에서 호출되지 않습니다. 대신 `fillna(0)` → `size_ho = 0`으로 처리되어 "크기 0인 작품"으로 학습됩니다.

### 1.4 3D 깊이 정보 손실

3D 작품(조각, 설치)도 `height × width`만 사용하여 깊이(depth)가 반영되지 않습니다.

---

## 2. 한국 캔버스 호수 규격표

### 2.1 F/P/M/S 타입

| 타입 | 의미 | 비율 | 주 용도 |
|------|------|------|--------|
| F (Figure) | 인물형 | 가장 넓음 | **가장 일반적** |
| P (Paysage) | 풍경형 | 중간 | 풍경화 |
| M (Marine) | 해경형 | 가장 좁음 | 파노라마 |
| S (Square) | 정사각형 | 1:1 | 현대미술 |

### 2.2 면적 대비 호수 관계 (F 타입)

```
면적/호수 비율:
  1호: 358.7cm²/호
  10호: 241.2cm²/호
  20호: 220.3cm²/호
  40호: 200.8cm²/호
  100호: 211.3cm²/호
  → 평균 약 210cm²/호 (10호 이상)
```

호수와 면적은 **선형이 아니라 비선형(로그적)** 관계입니다:
- 소형(1~10호): 호당 면적이 불규칙
- 중형 이상(10~100호): 호당 ~210cm²로 수렴

### 2.3 버킷 기준

| 버킷 | 호수 | 면적 (cm²) |
|------|------|-----------|
| 소형 | 0~10호 | < 2,720 |
| 중형 | 12~30호 | 2,720~7,320 |
| 대형 | 40~100호 | 7,320~22,000 |
| 초대형 | 120호+ | ≥ 22,000 |

---

## 3. 개선안

### 3.1 방안 A: 면적 → 실제 호수 근사 매핑 (권장)

F 타입 규격표를 기반으로 면적 → 호수 보간(interpolation) 함수를 구현합니다.

```python
import numpy as np

# F 타입 호수 ↔ 면적 매핑 (공식 규격)
HO_F_TABLE = {
    0: 252, 1: 359, 2: 462, 3: 601, 4: 808, 5: 950,
    6: 1301, 8: 1724, 10: 2412, 12: 3030, 15: 3450,
    20: 4406, 25: 5228, 30: 6608, 40: 8030, 50: 10629,
    60: 12639, 80: 16311, 100: 21135, 120: 25265,
    150: 41323, 200: 50239,
}

_HO_KEYS = np.array(sorted(HO_F_TABLE.keys()))
_AREA_VALS = np.array([HO_F_TABLE[k] for k in _HO_KEYS])

def area_to_ho_f(surface_area: float) -> float:
    """면적(cm²) → F 타입 기준 호수 보간."""
    if surface_area <= 0:
        return 0.0
    return float(np.interp(surface_area, _AREA_VALS, _HO_KEYS))
```

**장점**: 실제 호수 체계 반영, 비선형 관계 자동 처리
**효과**: `area_to_ho_f(8030) = 40.0` (정확), 기존 `8030/132 = 60.8` (부정확)

> **범위**: 위 보간은 **F 타입 기준**입니다. K-Auction 데이터에서 대부분의 회화가 F 타입이므로 F 기준 근사가 합리적이나, P/M/S 타입의 경우 같은 호수에도 면적이 다릅니다 (예: 20F=4,406cm², 20P=3,853cm², 20M=3,635cm²). 호수 직접 표기("20P")가 있으면 해당 타입 테이블을 사용하고, cm만 있으면 F 기준으로 근사합니다.

### 3.2 방안 B: ln(surface_area) + CatBoost 비선형 (간단)

호수 변환을 아예 하지 않고, CatBoost의 트리 분할에 맡깁니다.

```python
df["ln_surface_area"] = np.log(df["surface_area"].clip(lower=1))
# size_ho, size_ho_above40 제거
# CatBoost가 자동으로 최적 분할점을 찾음
```

**장점**: 가장 간단, 상수/hinge 논쟁 불필요
**단점**: 한국 시장의 호수 기반 가격 체계를 명시적으로 반영하지 않음

### 3.3 방안 C: 하이브리드 (가장 완전)

```python
# 1. 면적 기반 연속 피처 (주)
df["ln_surface_area"] = np.log(df["surface_area"].clip(lower=1))
df["long_side_cm"] = df[["height_cm", "width_cm"]].max(axis=1)
df["short_side_cm"] = df[["height_cm", "width_cm"]].min(axis=1)

# 2. 실제 호수 근사 (보조)
df["estimated_ho"] = df["surface_area"].apply(area_to_ho_f)

# 3. 크기 버킷 (범주형)
df["size_bucket"] = pd.cut(
    df["surface_area"],
    bins=[0, 2720, 7320, 22000, float("inf")],
    labels=["소형", "중형", "대형", "초대형"],
)

# 4. orientation (방향)
df["orientation"] = np.where(
    df["aspect_ratio"] > 1.2, "portrait",
    np.where(df["aspect_ratio"] < 0.83, "landscape", "square")
)
```

---

## 4. 결측 대체 개선

### 현재 → 개선

| 항목 | 현재 | 개선 |
|------|------|------|
| 결측 대체 | `fillna(0)` | `impute_surface_area()` 실연결 |
| 대체 기준 | 전체 중앙값 | is_3d × auction_type × medium_category 조건부 |
| 불확실성 | is_size_imputed (있지만 미활용) | 대체 시 is_size_imputed=True 강제 |

```python
# 개선된 결측 대체
def impute_surface_area_v2(
    df: pd.DataFrame,
    area_col: str = "surface_area",
) -> pd.DataFrame:
    """조건부 중앙값 대체 (is_3d x auction_type x medium_category)."""
    out = df.copy()
    # 결측 + 0 모두 대체 대상
    needs_impute = out[area_col].isna() | (out[area_col] <= 0)
    # 유효 데이터만으로 중앙값 계산
    valid = out[~needs_impute]

    for group_cols in [
        ["is_3d", "타입", "medium_category"],  # 1순위
        ["is_3d", "medium_category"],           # 2순위
        ["medium_category"],                    # 3순위
    ]:
        still_needs = needs_impute & (out[area_col].isna() | (out[area_col] <= 0))
        if not still_needs.any():
            break
        medians = valid.groupby(group_cols)[area_col].median()
        for idx in out[still_needs].index:
            key = tuple(out.loc[idx, group_cols])
            if key in medians.index:
                out.loc[idx, area_col] = medians[key]
                out.loc[idx, "is_size_imputed"] = True

    # 최종 fallback: 전체 중앙값
    global_median = valid[area_col].median()
    final_missing = out[area_col].isna() | (out[area_col] <= 0)
    out.loc[final_missing, area_col] = global_median
    out.loc[final_missing, "is_size_imputed"] = True

    return out
```

> **주의**: 그룹 키는 설명 표(is_3d × auction_type × medium_category)와 일치합니다. `0`도 결측으로 처리하며, 각 단계에서 그룹 중앙값이 없으면 다음 단계로 fallback합니다.

---

## 5. 3D 작품 개선

### 현재 → 개선

```python
# 현재: 3D도 height × width (깊이 무시)
surface_area = height * width

# 개선: 3D 전용 피처 추가
if is_3d:
    df["depth_cm"] = third_dimension  # 파싱 시 보존
    df["bbox_volume"] = height * width * depth
    df["max_plan_dim"] = max(height, width, depth)
```

---

## 6. 호수 직접 표기 파서 추가

현재 dimension_parser.py에 호수 **단독** 표기("20호", "20F")를 파싱하는 패턴이 없습니다.
`"72.7×60.6cm (20호)"`처럼 cm 병기 시에는 2D 패턴으로 파싱되지만, 호수만 있는 경우는 미지원입니다.

```python
# 추가 패턴
_PAT_HO = re.compile(r"(\d+)\s*호")
_PAT_HO_TYPE = re.compile(r"(\d+)\s*([FPMSfpms])")

# HO_TO_CM 매핑 테이블 (F/P/M/S 4타입)
HO_TO_CM = {
    # ho: {"F": (h, w), "P": (h, w), "M": (h, w), "S": (h, w)}
    1:  {"F": (22.7, 15.8), "P": (22.7, 14.0), "M": (22.7, 12.0), "S": (15.8, 15.8)},
    10: {"F": (53.0, 45.5), "P": (53.0, 40.9), "M": (53.0, 33.4), "S": (45.5, 45.5)},
    20: {"F": (72.7, 60.6), "P": (72.7, 53.0), "M": (72.7, 50.0), "S": (60.6, 60.6)},
    30: {"F": (90.9, 72.7), "P": (90.9, 65.1), "M": (90.9, 60.6), "S": (72.7, 72.7)},
    40: {"F": (100.0, 80.3), "P": (100.0, 72.7), "M": (100.0, 65.1), "S": (80.3, 80.3)},
    50: {"F": (116.8, 91.0), "P": (116.8, 80.3), "M": (116.8, 72.7), "S": (91.0, 91.0)},
    100: {"F": (162.2, 130.3), "P": (162.2, 112.1), "M": (162.2, 97.0), "S": (130.3, 130.3)},
    # ... 전체 테이블은 ref_size.md 참조
}

# "20호" → F 기준, "20F/20P/20M/20S" → 해당 타입 기준
```

---

## 7. 권장 실행 순서

| 순서 | 작업 | 난이도 | 효과 |
|------|------|--------|------|
| **1** | `impute_surface_area()` 파이프라인 연결 | 낮음 | 결측 0 문제 해결 |
| **2** | `ln(surface_area)` 피처 추가 | 낮음 | 비선형 자동 처리 |
| **3** | `area_to_ho_f()` 보간 함수 구현 | 중 | 정확한 호수 변환 |
| **4** | `size_bucket` 범주형 추가 | 낮음 | 소/중/대/초대형 구분 |
| **5** | `orientation` 피처 추가 | 낮음 | 가로/세로 정보 복원 |
| **6** | 호수 직접 표기 파서 추가 | 중 | "20호" 패턴 지원 |
| **7a** | DimensionResult에 depth_cm 필드 추가 (파서 선행) | 낮음 | 3D depth 저장 |
| **7b** | 3D 전용 피처 분리 (bbox_volume 등) | 중 | 깊이 정보 반영 |
| **8** | 40호 hinge 재검증/대체 | 중 | 정확한 변곡점 또는 제거 |

---

## 8. 검증 방법

```bash
# 개선 전후 비교
PYTHONPATH=src python3 -c "
# 1. 기존 size_ho vs 개선 estimated_ho 비교
# 2. MdAPE ablation: size_ho 제거 → ln_surface_area + estimated_ho
# 3. Feature importance 비교
"

# 테스트
pytest tests/price_engine/test_dimension_parser.py -v
pytest tests/price_engine/test_hedonic_features.py -v
```

---

## 부록: 호수별 면적 데이터 (F 타입)

| 호수 | H (cm) | W (cm) | 면적 (cm²) | 면적/호수 |
|------|--------|--------|-----------|----------|
| 1 | 22.7 | 15.8 | 359 | 358.7 |
| 5 | 34.8 | 27.3 | 950 | 190.0 |
| 10 | 53.0 | 45.5 | 2,412 | 241.2 |
| 20 | 72.7 | 60.6 | 4,406 | 220.3 |
| 30 | 90.9 | 72.7 | 6,608 | 220.3 |
| 40 | 100.0 | 80.3 | 8,030 | 200.8 |
| 50 | 116.8 | 91.0 | 10,629 | 212.6 |
| 100 | 162.2 | 130.3 | 21,135 | 211.3 |
| 200 | 259.1 | 193.9 | 50,239 | 251.2 |

> 10호 이상에서 호당 면적은 ~210cm²로 수렴. 132cm²는 이 어떤 값과도 맞지 않음.
