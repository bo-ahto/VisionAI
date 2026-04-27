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

### 2.3 확정 규칙 (사용자 확정 2026-04-27)

```
EXCLUDE if any of:
  1. sheet_tool_l1 ∈ {조각, 도자, 옻칠, 목공예}
  2. sheet_support ∈ {없음, 플라스틱, 목재, 금속}      ← 사용자 보수적 선택
  3. raw 문자열에 키워드: 조각|carved|sculpture|입체|bronze|brons|돌\b|stone\b|ceramic|porcelain|terracotta|타피스트리|tapestry
  4. 시트 비고2에 '학습 제외' 마커가 명시
```

**근거**:
- 사용자 결정 (2026-04-27): 평면 패널 회화 보존(Codex 권고)보다 입체 오포함 방지를 우선. 목재 단독 = 제외, 금속 단독 = 제외.
- 따라서 `support=금속 + tool=평면 매체` 케이스도 제외 (사용자 확정).
- `support=섬유 + tool=태피스트리`는 sheet_tool 규칙이 잡지 않으므로 raw 키워드(`tapestry|타피스트리`)로 보강.

### 2.4 영향 평가

baseline diff 기준:
- `sheet_support ∈ {없음, 금속, 목재, 플라스틱}` = 932 rows / 4,478 weighted (전체의 5.8% / 5.8%)
- `sheet_tool ∈ {조각, 도자, 옻칠, 목공예}` = 433 rows / 2,667 weighted
- 둘 union 기대 = 약 1,000~1,300 rows (공통 다수)
- 학습 데이터 손실 약 6%, 회화 위주 학습 품질 향상 기대.

---

## 3. 다중 매체 — primary 선정 규칙 초안

### 3.1 분포

- 다중 도구: 1,337 rows / 4,442 weighted (예: `유채, 아크릴릭`, `아크릴릭, 혼합재료`)
- 다중 지지체: 42 rows / 269 weighted (예: `한지, 캔버스`)

### 3.2 확정 규칙 (Codex 권고 + 사용자 확정 2026-04-27)

**도구 primary 선정** (Codex Q3 권고):
```
1순위: 특수 마감/가공(디아섹, 금박, 엠보싱 등)은 다른 생성 매체가 있으면
       primary 금지. has_special_finish=1 플래그 + secondary로 보존.
2순위: raw 문자열 등장 순서 (raw-first) — 가격 정보적 근거 있음
3순위: 동률·라벨만 매핑된 경우에만 도메인 우선순위표
       (회화/드로잉 > 판화 > 사진/디지털 > 혼합 매체 > 특수 마감/가공 > 없음)
```

**시트 row order 규칙은 폐기** (가격 정보적 근거 부족, Codex 지적).

예시:
- `유채, 아크릴릭` → raw-first → **`유채` primary**, secondary=[`아크릴릭`]
- `아크릴릭, 혼합재료` → raw-first → **`아크릴릭` primary**, secondary=[`혼합재료`]
- `pigment print, diasec` → 디아섹은 마감/가공 → **`디지털 피그먼트 프린트` primary**, has_special_finish=1, secondary=[`디아섹`]
- `캔버스에 유채, 아크릴, 혼합재료` → primary=`유채` + secondary=[`아크릴릭`, `혼합재료`] + secondary_count=2

**지지체 primary 선정** (사용자 확정 Q4):
- 다중 지지체 42건은 raw 문자열 등장 순서 우선 (예: `캔버스 위 한지` → primary=`캔버스`, secondary=[`한지`])

**검증 (선택)** — 데이터 기반 ablation으로 정책 재검토 가능:
- 정책 후보: `raw-first` (확정안), `domain-order`, `row-order`
- secondary multihot 고정, primary만 바꿔 OOF MdAPE/W30 비교
- 가격 통계는 정책 선택용 offline ablation까지만 사용 (runtime 규칙은 leakage)

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

## 4. value_grade — 영구 모델 입력 제외 (사용자 확정 + Codex 권고)

### 4.1 분포 (Codex 측정)

108행 중 81행에 등급값 있음:

| 등급 | 행 수 |
|---|---:|
| A | 21 |
| S | 14 |
| B+ | 13 |
| A+ | 11 |
| B | 9 |
| S+ | 4 |
| C | 2 |
| 가산점 | 2 |
| C+ | 1 |
| D | 1 |
| 변동 | 1 |
| C~D | 1 |
| A~A+ | 1 |
| (빈 셀) | 27 |

**비-ordinal 값 5종**(변동/가산점/C~D/A~A+ 등)이 섞여 있어 단순 ordinal 변환 불가.

### 4.2 처리 방침 (사용자 확정 2026-04-27)

협력자 출처 확인 없이 처리한다. Codex 권고대로 **모델 입력 영구 제외**.

| 시도 | 결정 | 사유 |
|---|---|---|
| (a) categorical 사용 | ✗ | 누설 미해결 (등급 만든 사람이 이미 가격을 보고 매겼을 가능성) |
| (b) ordinal 변환 + missing | ✗ | 누설 가림 |
| (c) 빈도 inverse 대체 피처 | ✗ | value_grade 활용이 아님. 별도 희소성 피처로 분리해야 함 |
| (d) 메모성 메타데이터 보존 | ✓ | **확정** — `MediumResult.value_grade_note` 로 raw 그대로 보존, 모델 입력 X |

### 4.3 향후 (Step 3 선택)

만약 출처 확인되어 활용을 재검토할 경우:
- 원본 `value_grade` 값 자체를 모델에 넣지 않음
- 대신 별도 binary/group 피처로 재해석:
  - `special_finish_bonus` — 디아섹·금박·은박 등 마감 가산점 명시 케이스
  - `process_uncertain` — `변동`/`가산점` 등 등급 불명 케이스
  - `rare_technique` — S/S+ 등급에 한해 별도 binary

### 4.4 정리 산출물

- 룰 사전 빌드 시 `value_grade`는 raw 보존 컬럼으로만 유지
- `medium_parser.py` 출력에는 포함하지 않음
- 시트 자체는 그대로 유지 (`data/k-artmarket 1차 데이터 정제 - 도구_기법 분류.csv`)

---

## 5. PR 분리 (Codex 권고)

| PR | 범위 | 위험 | 의존 |
|---|---|---|---|
| PR1 (parser 계약) | `MediumResult` 확장, `medium_parser.py` 룰 갱신, 호환 컬럼 유지, 신 시트 기반 leaf 보존, 학습 제외 플래그, 테스트 보강 | 낮음 (호환 컬럼 유지) | — |
| PR2 (데이터 재생성) | `cleanse_artmarket.py`로 `k-artmarket-cleansed[-known].csv` 재생성, 단일값 → list/leaf 컬럼 추가 | 중 (재학습 입력 변경) | PR1 |
| PR3 (B 모델 피처/학습) | `train_phase5_final.py` + `hedonic_features.py` + `hedonic_stats.py` + `artist_similarity.py` 멀티핫·leaf 사용, 재학습 | 높음 (모델 성능 영향) | PR2 |
| PR4 (선택, value_grade) | 출처 검증 후 ordinal/categorical feature 추가 | 보류 | PR3 + 출처 확인 |

---

## 6. 사용자 결정 사항 (확정 2026-04-27)

| # | 항목 | 결정 |
|---|---|---|
| 1 | 입체 제외 기준 | **목재 단독, 금속 단독 = 제외** (사용자 보수 선택, Codex 권고와 다름) |
| 2 | `support=금속 + tool=평면` | **제외** (1과 일관) |
| 3 | 다중 도구 primary | **raw-first** (Codex 권고). 마감/가공은 secondary 강제. row-order 폐기 |
| 4 | 다중 지지체 | **raw 첫번째 우선** |
| 5 | value_grade | **모델 입력 영구 제외**, 메모성 메타데이터로만 보존 |
| 6 | PR 분리 | **PR1 머지 진행** |

---

## 7. A 모델(1차 시장) 입체 처리 — 사용자 추가 요청 확인

사용자: "A 모델에서도 입체 작품 학습 제외 분류 필요한지 확인"

### 7.1 현재 상태 (코드 grep 결과)

- **이미 입체는 자동 제외 중**: `scripts/prepare_primary_market_dataset.py:176-177`
  ```python
  df = df[df["category"] == "Painting"]
  df = df[df["price_krw"].notna() & (df["price_krw"] > 0)]
  ```
  → Artsy `category` 컬럼이 `Painting`인 것만 학습. Sculpture, Photography, Print, Mixed Media, Drawing 등 모두 제외됨.

- **배포 코드도 회화 중심**:
  - `primary_feature_builder.py:28-37` — MEDIUM_RULES 8종(oil/acrylic/ink/watercolor/pigment/mixed/pastel/pencil) 모두 회화 매체
  - `primary_predictor.py:159-160` — medium 매핑 동일

### 7.2 보고서 vs 코드 불일치 (Codex 발견)

`docs/primary_market_final_report.md:5`:
> 카테고리: Painting, Mixed Media, Drawing/Collage/Paper, Photography, Print

→ 코드는 **Painting only**, 보고서는 **5개 카테고리**라 명시. **보고서 stale**.

### 7.3 결론 및 후속 작업

| 항목 | 결정 |
|---|---|
| 현재 A 모델 입체 처리 | **이미 제외** (Painting only 필터로 자동) |
| 별도 입체 필터 추가 필요? | **현 단계 불필요** — Painting 필터가 그 역할 |
| Mixed Media 재진입 시 | **그때 입체 필터 추가** 필요 (Mixed Media는 평면/입체 혼재) |
| 보고서 정정 필요 | **TODO** — `primary_market_final_report.md` "5개 카테고리" 표현을 "Painting 단일 카테고리"로 수정. **본 PR 범위 외, 별 사이클** |

### 7.4 A 모델 작업 향후 권장 (참고)

만약 A 모델 카테고리 확장 (Painting + Mixed Media + Drawing/Collage/Paper)할 경우:
- B 모델의 분류 재설계 결과(평면/입체 플래그)를 A 모델에도 적용 가능
- 단 A는 영문 8종 분류기(`primary_feature_builder.py`)를 별도로 사용 → 동기화 작업 필요
- 본 PR 범위는 **B 전용**. A 모델 확장은 별 PR.

---

## 8. 다음 행동 — PR1

### 8.1 PR1 범위 (확정)

**브랜치**: `feature/data-manifest`에 이어서 (또는 `feature/medium-parser-v2` 분리 — 사용자 선택)
**대상**: B 모델 (`medium_parser.py` + 클렌징 파이프라인 출력 컬럼)

**변경 항목**:

1. **`MediumResult` 확장** (`src/visionai/price_engine/preprocessing/medium_parser.py`):
   ```python
   @dataclass
   class MediumResult:
       # 호환 (기존 다운스트림 보호)
       medium_category: str         # = medium_l1, 17종 라벨
       support_category: str        # = support_l1, 8종 라벨
       # 신규 — 계층 + 멀티
       medium_l1: str
       medium_leaf: str             # 시트 leaf (~100종)
       mediums: list[str]           # primary + secondary
       has_multimedia: bool
       has_special_finish: bool     # 디아섹·금박 등
       support_l1: str
       support_leaf: str
       supports: list[str]
       has_multisupport: bool
       # 학습 제외 플래그
       is_excluded_for_training: bool
       exclude_reason: str | None   # tool_3d / support_excluded / keyword_3d / sheet_marker
       # 메모성 (모델 입력 X)
       value_grade_note: str | None
   ```

2. **새 룰 사전 빌드** — 신규 시트 3종을 파싱해서 leaf-level 룰 사전 생성:
   - `_TOOL_LEAVES`: leaf → (대분류, 중분류, 가치등급) 매핑 (108행)
   - `_SUPPORT_LEAVES`: leaf → (대분류, 중분류) 매핑 (36행)
   - `_KEYWORD_TO_TOOL_LEAF`: keyword → leaf (시트 4번째 컬럼 keyword)
   - `_KEYWORD_TO_SUPPORT_LEAF`: keyword → leaf

3. **`parse_medium()` 로직 갱신**:
   - raw 분할 (콤마 분리)
   - 각 토큰을 leaf-level 매칭 (keyword 사전 우선, 한국어 약어 풀기)
   - primary 선정: raw-first + special-finish 분리
   - 입체 제외 평가: §2.3 4가지 규칙
   - L1 호환 컬럼 채우기

4. **클렌징 파이프라인 출력 컬럼** (`scripts/cleanse_artmarket.py`):
   - 기존 `medium_category`, `support_category` 유지
   - 신규 `medium_l1`, `medium_leaf`, `mediums_json`, `support_l1`, `support_leaf`, `supports_json`, `has_multimedia`, `has_special_finish`, `is_excluded_for_training`, `exclude_reason`, `value_grade_note` 추가

5. **테스트 보강** (`tests/price_engine/test_medium_parser.py`):
   - 단일/다중 매체 케이스
   - 입체 제외 4가지 규칙 각각
   - special_finish 처리 (디아섹/금박)
   - leaf 보존 (한지/장지/패널/보드)
   - 호환 컬럼 (medium_category, support_category) 변경 없음

6. **Step 0 baseline 재실행** — PR1 적용 후 Medium L1 일치율 변화 확인. 기대: 53.3% → 90%+ (leaf 보존 + naming 동기).

### 8.2 PR1에 들어가지 않는 것

- **B 모델 학습 재실행** — PR2
- **`hedonic_features.py`/`hedonic_stats.py`/`artist_similarity.py` 멀티핫 적용** — PR3
- **A 모델 변경 (1차 시장)** — 별 PR (보고서 정정 포함)
- **value_grade 모델 입력화** — PR4 (선택, provenance 확인 후)
- **archived 49개 파일 `_archive/` 이동** — 별 PR

### 8.3 PR1 추정 변경 규모

- 신규 룰 사전 (시트 파싱): ~150 LOC
- `parse_medium()` 로직: ~100 LOC 변경
- `cleanse_artmarket.py` 출력 컬럼: ~30 LOC 변경
- 테스트 보강: ~200 LOC
- 총 ~500 LOC, 단일 파일 모듈 하나에 집중
