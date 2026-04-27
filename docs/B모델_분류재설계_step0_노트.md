# B 모델(경매 낙찰가) 분류 재설계 — Step 0 노트

> **작성일**: 2026-04-27
> **모델 범위**: B (경매 낙찰가, `medium_parser.py` + `cleanse_artmarket.py` + `train_phase5_final.py`). A(1차 시장)는 본 작업 범위 외.
> **단계**: Step 0 = 분석/설계만. 코드 변경 없음.
> **산출물**: 본 노트 + `scripts/diff_medium_parser_baseline.py` (재현 스크립트)
> **재현**: `PYTHONPATH=src python3 scripts/diff_medium_parser_baseline.py` → `data/medium_parser_baseline_diff_<오늘>.csv` 생성 (gitignore: `*.csv`)

---

## 1. baseline 재집계 (Codex 지적 검증)

`data/k-artmarket 1차 데이터 정제 - 실험데이터분류(데이터 수정).csv` (6,049개 unique 재료 문자열, weighted 76,696건)을 현 `medium_parser.parse_medium()`으로 다시 돌렸다.

### 1.1 카운트 정정

| 지표 | 사용자 보고 | 실파일 카운트 | 비고 |
|---|---:|---:|---|
| 분류 미매칭 (비고 ≠ 빈) | 1,069 | **1,435** | 사용자가 본 1,069는 부분집합 가능성 |
| 학습 제외 (비고2 ≠ 빈) | 966 | **1,378** | 동일 |
| 총 unique 재료 | — | **6,049** | weighted 76,696 |
| 다중 도구 (콤마 구분) | — | **1,337** rows / 4,442 weighted | |
| 다중 지지체 | — | **42** rows / 269 weighted | |

→ **시트 설명과 실 행 카운트 차이가 큼**. ground truth 컬럼을 명확히 정의하지 않으면 Step 2 효과 측정 불가.

### 1.2 현 파서 vs 새 시트 일치율 (L1 기준)

| 차원 | unweighted | weighted |
|---|---:|---:|
| Medium 일치 | 59.8% | 53.3% |
| Support 일치 | 82.2% | 93.2% |

**Support는 거의 일치**. **Medium은 절반 이상 mismatch**인데, 분석 결과 **대부분 naming/leaf 차이**이지 진짜 오분류 아님:

### 1.3 Top medium mismatches (weighted)

| Parser | Sheet | weighted | 성격 |
|---|---|---:|---|
| 유화 | 유채 | 15,336 | **단순 명명 차이** |
| 아크릴 | 아크릴릭 | 7,104 | **단순 명명 차이** |
| 판화 | 석판 | 4,544 | **leaf 세분화** (parser는 L1, sheet는 leaf) |
| 인쇄/복제 | 오프셋 프린트 | 957 | leaf 세분화 |
| 사진/디지털 | 디지털 피그먼트 프린트 | 839 | leaf 세분화 |
| 판화 | 목판 | 589 | leaf 세분화 |
| 판화 | 에칭 | 407 | leaf 세분화 |
| 판화 | 메조틴트 | 345 | leaf 세분화 |
| 연필/드로잉 | 연필 | 328 | leaf 세분화 |
| 연필/드로잉 | 펜 | 322 | leaf 세분화 |
| 연필/드로잉 | 색연필 | 148 | leaf 세분화 |
| 유화 | 오일 파스텔 | 159 | **진짜 mismatch** (오일파스텔은 드로잉 leaf인데 parser가 유화로 흡수) |
| 유화 | 아크릴릭 | 218 | **진짜 mismatch** (오분류) |
| 기타 | 디지털 프린트 | 177 | parser 미매칭, 시트는 매칭 |

→ **Top 10 mismatch 중 8개가 단순 명명/leaf 차이**. 즉 parser는 L1 수준에서는 충분히 동작하지만, **leaf 보존이 안 되어 새 시트의 정보를 못 받아오는 게 핵심 한계**.

### 1.4 Top support mismatches (weighted)

| Parser | Sheet | weighted | 성격 |
|---|---|---:|---|
| 기타 | 종이 | 1,899 | **parser 미매칭, 시트는 매칭** (raw에서 paper 키워드 못 잡음) |
| 종이 | 한지 | 603 | leaf 세분화 |
| 종이 | 장지 | 476 | leaf 세분화 |
| 기타 | 캔버스 | 429 | parser 미매칭 |
| 섬유 | 캔버스 | 387 | **분류 충돌** (시트는 캔버스, parser는 섬유로 흡수) |
| 목재 | 패널 | 244 | leaf 세분화 |
| 종이 | 보드 | 183 | leaf 세분화 |
| 목재 | 보드 | 181 | leaf 세분화 |

### 1.5 시트가 미매칭 처리했지만 parser는 매칭한 케이스 — **단 10건**

```
archival pigment print in colors on wooden skate deck → parser=(목재, 사진/디지털)
pigment print on paper → parser=(종이, 사진/디지털)
... (전부 pigment print 변형)
```
→ Codex 지적("archival pigment print는 시트에서 미매칭이지만 현 파서가 이미 잡음")이 **대규모는 아님** (10건/소량 weight). 다만 시트의 미매칭 라벨 자체가 부분 outdated.

### 1.6 parser '기타'이지만 시트는 라벨 있음 — **130건**

| count | raw | sheet leaf |
|---:|---|---|
| 153 | `printed on paper` | 디지털 프린트 (종이) |
| 83 | `캔버스에 안료` | 안료 (캔버스) |
| 22 | `종이에 잉크` | 수묵 (종이) — 시트는 잉크=수묵으로 매핑 |
| 16 | `giclée print on canvas` | 지클레이 프린트 (캔버스) — é 액센트 |
| 15 | `패브릭에 전사` | 전사 (섬유) |
| 14 | `실크 스크린` | 실크스크린 (종이) — 띄어쓰기 |
| 12 | `종이에 매직` | 마커 (종이) |
| 11 | `embroidered on silk` | 자수 (비단) |
| 11 | `나무 패널에 밀랍화기법` | 밀랍화 (패널) |
| 10 | `spray paint on canvas` | 스프레이 (캔버스) |
| 8 | `acylic on canvas` | 아크릴릭 (캔버스) — 오타(acrylic) |

→ **새 시트 룰을 적용하면 줄어들 미매칭의 대부분이 여기**. printed/giclée/패브릭/매직/실크 스크린 띄어쓰기/오타 등.

---

## 2. 입체 제외 기준 — Codex 권고 검증

### 2.1 baseline

| 후보 기준 | rows | weighted | '학습 제외' 마커 있음 | 마커 없음 |
|---|---:|---:|---:|---:|
| sheet_support ∈ {없음, 금속, 목재, 플라스틱} | 932 | 4,478 | 119 | **813** |
| sheet_tool ∈ {조각, 도자, 옻칠, 목공예} | 433 | 2,667 | — | — |

**813개가 학습 제외 마커 없음** — 즉 사용자가 제안한 "지지체 단독 규칙"으로 자르면 813개 중 일부 평면 회화도 잘릴 수 있다. Codex 지적과 일치.

### 2.2 평면 회화인데 '제외 후보 지지체'에 걸리는 케이스 (예시)

`data/medium_parser_baseline_diff_20260427.csv` 검색 결과:

- `mixed media on wood` — 회화. 지지체=목재.
- `패널에 유채` — 평면. 지지체=목재(패널).
- `하드보드에 유채` — 평면. 지지체=목재(보드).
- `알루미늄 패널 + 회화` 패턴 — 지지체=금속이지만 평면.

### 2.3 제안 — 단계적 제외 규칙

```
EXCLUDE if any of:
  1. sheet_tool_l1 ∈ {조각, 도자, 옻칠, 목공예}
  2. sheet_support ∈ {없음, 플라스틱}
  3. raw 문자열에 키워드: 조각|carved|sculpture|입체|bronze|brons|돌\b|stone\b|ceramic|porcelain|terracotta|타피스트리|tapestry
  4. 시트 비고2에 '학습 제외' 마커가 명시
KEEP (애매하면 보존):
  - sheet_support = '목재' 단독 (위 1·3·4 미해당) → 평면 패널 회화 가능성
  - sheet_support = '금속' 단독 (위 1·3·4 미해당) → 평면 알루미늄/스테인리스 패널 회화 가능성
```

**근거**: Codex 검증 + 보수적 보존.

### 2.4 불확실 케이스 (사용자 결정 필요)

- **`support=금속` + `tool=평면 매체(회화/판화 등)`** — 이걸 학습에 포함할지 제외할지 결정 필요. 한국 작가 중 알루미늄 패널 회화는 소수지만 존재 (이배·서도호 등 패턴).
- **`support=목재` + `tool=조각`** — 명시적으로 EXCLUDE (위 규칙 1).
- **`support=섬유` + `tool=자수/태피스트리`** — 자수는 평면 회화로 간주, 태피스트리는 입체. 시트 도구로 결정.

---

## 3. 다중 매체 — primary 선정 규칙 초안

### 3.1 분포

- 다중 도구: 1,337 rows / 4,442 weighted (예: `유채, 아크릴릭`, `아크릴릭, 혼합재료`)
- 다중 지지체: 42 rows / 269 weighted (예: `한지, 캔버스`)

### 3.2 제안 — 결정론적 우선순위 규칙

**도구 primary 선정**:
```
1순위: 시트 대분류 우선순위
       회화/드로잉 > 판화 > 사진/디지털 > 혼합 매체 > 특수 마감·가공 > 없음
2순위: 동일 대분류 내 — 시트 row order (시트 작성 순서 = 작가/큐레이터 의도)
3순위: 안정성을 위한 alphabetical leaf name
```

예시:
- `유채, 아크릴릭` → 둘 다 회화/드로잉 ∋ 유성 → row order로 `유채`(L86 회화/드로잉/유성) primary
- `아크릴릭, 혼합재료` → 회화/드로잉 vs 혼합 매체 → 대분류 우선 → `아크릴릭` primary, secondary=`혼합재료`
- `pigment print, diasec` → 사진/디지털 vs 특수 마감·가공 → 대분류 우선 → `디지털 피그먼트 프린트` primary, secondary=`디아섹`

**지지체 primary 선정**:
- 다중 지지체 42건은 대부분 `캔버스 위 한지` 같은 layered 표기. 문자열 첫번째를 primary로 단순화. (검토 필요)

**값 표현**:
```python
@dataclass
class MediumResult:
    medium_l1: str          # 회화/드로잉, 판화, ...
    medium_leaf: str        # 유채, 석판, ...
    mediums: list[str]      # ["유채", "아크릴릭"] 또는 ["유채"]
    has_multimedia: bool
    support_l1: str         # 종이, 섬유, ...
    support_leaf: str       # 한지, 캔버스, ...
    supports: list[str]
    has_multisupport: bool
    is_excluded_for_training: bool
    exclude_reason: str | None  # "tool_3d" / "support_excluded" / "keyword_3d" / "sheet_marker"
```

호환 컬럼 (단일 스칼라 가정 다운스트림 보호):
- `medium_category` ← `medium_l1` (기존 17종 라벨 매핑)
- `support_category` ← `support_l1`

---

## 4. value_grade — 사용 보류 (Codex 권고)

### 4.1 우려

`도구_기법 분류.csv`의 `가치 등급` 컬럼 분포:
- 정상 등급값: `S+`, `S`, `A+`, `A`, `B+`, `B`, `C+`, `C`, `D` — ordinal 가능
- **비-ordinal 값**: `변동`, `가산점`, `C~D`, `A~A+`, `D~`, 빈 셀 다수

### 4.2 출처 미확인 → 누설 위험

- 등급이 가격 통계/시장 거래 평균 기반이면 **명백한 leakage** (등급 만든 사람이 이미 가격을 보고 매김)
- 기법 자체의 희소성/기술 난이도 기반이면 **OK**, 다만 검증 필요
- 작가별 가격 보정 기반이면 **부분 leakage**

### 4.3 결정 — Step 1까지는 사용하지 않음

- value_grade를 모델 피처로 추가하는 작업은 **Step 3 (선택)** 으로 분리
- 출처 확인되면 Step 3 진행, 확인 안 되면 영구 보류

### 4.4 사용자/협력자에 확인할 질문

> 도구/기법 분류 시트의 `가치 등급` 컬럼은:
> - 누가 매겼는가? (개인 큐레이터/시장 데이터/외부 references)
> - 어떤 기준인가? (a) 기법 자체의 희소성·기술 난이도 (b) 시장 거래 평균가 (c) 작가별 가격 통계 보정 (d) 기타
> - `변동`, `가산점`, `C~D`, `A~A+`는 어떻게 해석해야 하는가?

---

## 5. PR 분리 (Codex 권고)

| PR | 범위 | 위험 | 의존 |
|---|---|---|---|
| PR1 (parser 계약) | `MediumResult` 확장, `medium_parser.py` 룰 갱신, 호환 컬럼 유지, 신 시트 기반 leaf 보존, 학습 제외 플래그, 테스트 보강 | 낮음 (호환 컬럼 유지) | — |
| PR2 (데이터 재생성) | `cleanse_artmarket.py`로 `k-artmarket-cleansed[-known].csv` 재생성, 단일값 → list/leaf 컬럼 추가 | 중 (재학습 입력 변경) | PR1 |
| PR3 (B 모델 피처/학습) | `train_phase5_final.py` + `hedonic_features.py` + `hedonic_stats.py` + `artist_similarity.py` 멀티핫·leaf 사용, 재학습 | 높음 (모델 성능 영향) | PR2 |
| PR4 (선택, value_grade) | 출처 검증 후 ordinal/categorical feature 추가 | 보류 | PR3 + 출처 확인 |

---

## 6. 사용자 결정 사항 (정리)

이번 사이클에 답이 필요한 항목:

1. **입체 제외 기준** — §2.3 제안(목재·금속 보존, 도구·키워드 우선) 채택할지?
2. **`support=금속 + tool=평면 매체`** 케이스 — 학습 포함 vs 제외?
3. **다중 도구 primary 선정 규칙** — §3.2 제안(대분류 우선 → row order) 채택할지?
4. **다중 지지체** — `캔버스 위 한지` 같은 layered 표기는 첫번째 우선으로 단순화할지?
5. **value_grade** — §4.4 질문을 협력자에게 확인 후 다시 다룰지?
6. **PR 분리 일정** — PR1만 먼저 머지하고 PR2/3은 별 사이클로 갈지?

---

## 7. 다음 행동

1. 본 노트 + diff CSV 커밋 (현 사이클)
2. 사용자 결정 6건 받기
3. 결정 받으면 PR1 작성 시작 (`MediumResult` 확장 + 새 룰 + 호환 컬럼 + 테스트)
