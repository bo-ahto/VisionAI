# A 모델(1차 시장) 분류 재설계 — Step 0 노트

> **작성일**: 2026-04-27
> **모델 범위**: A (1차 시장, primary_predictor + integrated_v3_*). B(경매 낙찰가)는 별 작업 (`docs/B모델_분류재설계_step0_노트.md`).
> **단계**: Step 0 = 분석/설계만. 코드 변경 없음.
> **산출물**: 본 노트 + `scripts/diff_primary_parser_baseline.py`

## 0. 작업 컨텍스트

- 사용자가 작업 범위를 A 모델로 확정 (2026-04-27).
- 작업 동기: 새 분류 시트 3종(지지체 36 + 도구 108 + 실험데이터 6,049)의 분류 체계를 A 모델 데이터에도 적용 + 입체 작품 학습 제외 강화.
- B 작업 산출물(`MANIFEST.md`, B Step 0 노트, `diff_medium_parser_baseline.py`)은 보존. B 모델이 잠정 중단이지만 분류 체계 자체는 valid.

## 1. A 모델 데이터 실태

### 1.1 Artsy (30,046 works)

```
category 분포:
  Painting              20,616 (68.6%)   ← 현재 학습 대상
  Sculpture              2,514 (8.4%)
  Mixed Media            2,452 (8.2%)
  Drawing/Collage/Paper  2,041 (6.8%)
  Photography              950 (3.2%)
  Print                    910 (3.0%)
  Installation             263
  Textile Arts              68
  Video/Film/Animation      66
  Other                     85

medium: 단일 영문 free-text. 4,008 unique (Painting only: 1,869)
Top: "Oil on canvas" 4,890 / "Acrylic on canvas" 3,823 / "Mixed media on canvas" 916
```

### 1.2 Saatchi (30,607 works)

```
category 분포:
  painting       23,773 (77.7%)   ← 현재 학습 대상
  photography     2,677
  drawing         1,773
  mixed media       890
  sculpture         677
  collage           326
  digital           269
  printmaking       138
  installation       84

materials: 분리 컬럼. 572 unique. Top: canvas 17,559 / paper 6,580 / other 1,287 / wood 736 / "canvas, wood" 307
mediums: 분리 컬럼. 1,795 unique. Top: acrylic 8,462 / oil 6,420 / watercolor 851 / "acrylic, oil" 591
다중 medium (콤마 포함): 10,295 (33.6%) — k-artmarket B 22%보다 훨씬 많음
```

### 1.3 현재 A 코드 분류기

- `scripts/prepare_primary_market_dataset.py:176`: `df = df[df["category"] == "Painting"]` — Painting만 학습
- `scripts/prepare_saatchi_dataset.py:217-219`: 동일 패턴
- `src/visionai/price_engine/api/primary_feature_builder.py:19-37`:
  - SUPPORT_RULES 6종 (canvas / linen / paper / panel / silk / metal)
  - MEDIUM_RULES 8종 (oil / acrylic / ink / watercolor / pigment / mixed / pastel / pencil)
  - 영문 substring first-match
- `src/visionai/price_engine/api/primary_predictor.py:157-160`: 영문 8 매체 전제 medium map

## 2. 새 시트 룰 적용 baseline (재현: `scripts/diff_primary_parser_baseline.py`)

### 2.1 측정값 (단순 substring 매칭)

| 데이터 | 전체 | Painting only |
|---|---|---|
| **ARTSY** support match | 75.4% | **88.0%** |
| **ARTSY** tool match | 89.7% | **96.3%** |
| **ARTSY** multi-tool (≥2 leaves) | 53.3% | — |
| **ARTSY** multi-support (≥2 leaves) | 68.5% | — |
| **ARTSY** Painting + 3D keyword sneak | — | **227 (1.1%)** |
| **SAATCHI** support match | 93.8% | **95.3%** |
| **SAATCHI** tool match | 96.2% | **98.3%** |
| **SAATCHI** multi-tool | 45.5% | — |
| **SAATCHI** multi-support | 89.7% | — |
| **SAATCHI** Painting + 3D keyword sneak | — | **107 (0.5%)** |

### 2.2 측정 방법론 한계 (note: 본 baseline은 lower bound)

- 단순 substring 매칭으로 측정. 실 PR1 파서는 `on X` 패턴, 토큰화, leaf 충돌 해소 등 더 정교한 로직 필요.
- **False positive 알려진 케이스**: 종이 leaf의 keyword에 `canvas paper`가 있어 영문 단어 추출 시 `canvas` 자체도 종이 leaf로 매칭됨 → multi-support 부풀림 (특히 Saatchi 89.7%).
- 따라서 위 매칭률은 "단순 substring으로도 이만큼은 잡힌다"의 하한치. 정교한 파서로는 더 잘 잡되 충돌 해소가 핵심.

### 2.3 입체 sneak-in 후보 (Painting 카테고리 안 3D 키워드)

**Top 케이스 (Artsy)**:
- 23건: `Glass, Gold leaf, Acrylic on canvas` ← 평면(아크릴 회화)이지만 glass 객체 부착
- 21건: `Acrylic on canvas, carving with colors` ← carving 키워드, 부조 가능성
- 16건: `Oil on canvas, Carved frame on wood` ← 액자가 carved일 뿐 작품은 평면 (false positive)
- 14건: `Glass, Acrylic on canvas` ← Glass 객체 부착 (평면 vs 입체 모호)
- 14건: `Oil on canvas, Carved frame on resin` ← 액자만 carved
- 12건: `Stainless steel on canvas` ← 평면이지만 표면 처리
- 12건: `Oil on canvas, carved frame on wood` ← 액자 carved
- 11건: `Acrylic on glass` ← 유리에 회화. 평면 vs 입체 경계
- 10건: `Porcelain, acrylic on canvas` ← 자기 객체 부착
- 7건: `Ceramic, mixed media` ← 세라믹 입체 가능성 큼
- 6건: `Scratched and painted on stainless steel` ← 평면 금속 회화

**Top 케이스 (Saatchi)**:
- 8건: `acrylic, ink, glass` ← 유리 객체
- 7건: `acrylic` (단독, 다른 컬럼에서 sneak 키워드?) ← 확인 필요
- 6건: `other, plaster` ← 석고는 평면 가능

**해석**:
- 절대 다수가 액자(`Carved frame`)의 carved 키워드 false positive — 작품은 평면
- 진짜 입체 의심: `Glass, Gold leaf, Acrylic on canvas`, `Porcelain, acrylic on canvas`, `Ceramic, mixed media`, `Stainless steel on canvas` 등 "객체 부착" 케이스 ~100건
- 처리 방향: `Carved frame` 단어 패턴은 false 처리, 진짜 sneak 후보(porcelain/ceramic/glass-object/stainless-steel)는 평면/입체 경계로 보고 학습 포함 vs 제외 사용자 결정 필요

### 2.4 미매칭 (Painting + tool 못 잡음)

| 데이터 | medium | 건수 |
|---|---|---:|
| Artsy | `Mixed media` | 191 |
| Saatchi | `other` | 156 |
| Saatchi | `watercolor` | 91 (영문 단어 매칭 안 됨? 확인 필요) |
| Artsy | `Mixed Media` | 81 |
| Artsy | `Pigments naturels sur toile` | 48 (불어) |
| Artsy | `Fibers and mixed media` | 30 |
| Artsy | `Mixed media on panel` | 26 |
| Artsy | `Mixed media (mother of pearl) on wood` | 25 |
| Saatchi | `mixed media` | 25 |
| Artsy | `Watercolor and gouache on Arches` | 23 |
| Artsy | `Plaster & gouache on wood panel` | 13 |

**해석**:
- "mixed media" 단독은 시트의 `혼합재료` leaf로 잡혀야 하지만 keyword에 `mixed media`가 직접 없음 → 시트 keyword 보강 필요
- "watercolor" 매칭 실패는 단순 매칭 버그 가능성 (수채 leaf keyword 확인 필요)
- 불어/특수 표기는 일부 수기 매핑 또는 제외

## 3. 사용자 결정 사항 (B 노트 §6에서 가져옴, A 적용)

Codex 권고 + 사용자 확정 (2026-04-27):

| # | 항목 | 결정 (B와 동일 적용) |
|---|---|---|
| 1 | 입체 제외 기준 | 도구 ∈ {조각, 도자, 옻칠, 목공예} OR 지지체 ∈ {없음, 금속, 플라스틱, 목재} OR 키워드 OR 시트 마커 |
| 2 | 금속 + 평면 매체 | 제외 |
| 3 | 다중 도구 primary | raw-first + 마감/가공 secondary 강제 |
| 4 | 다중 지지체 | raw 첫번째 우선 |
| 5 | value_grade | 모델 입력 영구 제외, 메모성 메타로 보존 |
| 6 | PR 분리 | PR1 머지 진행 |

**A 모델 특화 추가 결정**:
- A 모델 학습 범위: **Painting only 유지** (옵션 α, Codex 권고)
- 입체 sneak-in 추가 검증: Painting 카테고리 안 medium에 3D 키워드 검사
- Mixed Media 등 다른 카테고리 확장: **본 PR 범위 외** (별 PR에서 다룰 사안)
- 보고서 stale 정정 (`primary_market_final_report.md:5` "5 카테고리" → "Painting 단일"): **별 PR**

## 4. PR1 범위 (A 전용)

### 4.1 신규 모듈 (Codex 권고 Q6 옵션 Y)

`src/visionai/price_engine/preprocessing/primary_medium_parser.py` 신규 생성:

```python
@dataclass
class PrimaryMediumResult:
    # 호환 (기존 다운스트림 보호)
    medium_category: str         # 기존 8 영문 라벨 호환 (oil/acrylic/...)
    support_type: str            # 기존 6 영문 라벨 호환 (canvas/paper/...)
    # 신규 — 시트 기반 계층
    medium_l1: str               # 회화/드로잉, 판화, 사진/디지털 등
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
    # 메모 (모델 입력 X)
    value_grade_note: str | None
```

API:
```python
def parse_artsy_medium(medium_str: str, category: str | None = None) -> PrimaryMediumResult: ...
def parse_saatchi_medium(materials: str, mediums: str, category: str | None = None) -> PrimaryMediumResult: ...
```

### 4.2 파서 로직

**Artsy 파싱**:
- `, and, with, on` 기준 토큰화
- `<X> on <Y>` 패턴 → primary tool=X, primary support=Y
- 시트 keyword 매칭 (한/영 혼합, leaf 충돌 해소: longer-match wins)
- 다중 tool: comma-separated, raw-first primary
- 입체 sneak 검출: `Carved frame` 등 false positive 패턴 명시 화이트리스트

**Saatchi 파싱**:
- `materials` → support 매칭 (분리된 구조 직접 사용)
- `mediums` → tool 매칭
- comma-separated 다중 → list 보존, raw-first primary
- `other` → "기타", 빈 문자열 → "missing"

### 4.3 호출 포인트

- `scripts/prepare_primary_market_dataset.py:213-215`: 영문 free-text → 새 파서 호출
- `scripts/prepare_saatchi_dataset.py:265-268`: materials/mediums → 새 파서 호출
- `src/visionai/price_engine/api/primary_feature_builder.py:91-94`: 추론 경로도 새 파서 호출 (호환 컬럼은 그대로 출력 → 모델 재학습 전 안전)

### 4.4 입체 sneak-in 처리

- Painting 카테고리에 들어 있어도 medium에 다음 키워드 있으면 `is_excluded_for_training=True`:
  - **High confidence 3D**: `bronze`, `porcelain`, `ceramic`, `stoneware`, `terracotta`, `sculpture`, `installation`
  - **Mid confidence**: `glass` (Acrylic on glass 등 평면 가능, 사용자 결정), `stainless steel` (평면 가능)
  - **False positive 화이트리스트**: `Carved frame`, `frame on wood/resin` — 액자만 carved이므로 작품은 평면
- 키워드별 confidence 등급 + 사용자 final 결정 → confidence high 자동 제외, mid는 별 플래그로 보존

### 4.5 테스트

- 단일/다중 매체 케이스
- 4가지 입체 제외 규칙
- special_finish 처리
- leaf 보존 (한지/장지/캔버스/패널)
- 호환 컬럼 (medium_category, support_type) 변경 없음
- Carved frame false positive 화이트리스트
- baseline 재실행 검증 (Painting tool match 96% → 98%+ 기대)

### 4.6 PR1에 들어가지 않는 것

- A 모델 학습 재실행 — PR2
- 5 카테고리 확장 — 별 PR (보고서 정정 포함)
- B 모델 작업 (이미 보존됨, 별도)
- value_grade 모델 입력화 — PR4 (선택)
- archived 49개 파일 이동 — 별 PR

### 4.7 추정 변경 규모

- 신규 파서 모듈: ~300 LOC
- 시트 룰 빌더: ~100 LOC
- 호출 포인트 변경 (3 파일): ~30 LOC
- 테스트: ~250 LOC
- 총 ~700 LOC

## 5. 다음 행동

1. 본 노트 + diff 스크립트 커밋 (현 사이클)
2. 사용자 검토 후 PR1 진입 결정
3. PR1 진입 시 새 브랜치 권장: `feature/primary-medium-parser` (현 `feature/data-manifest`와 분리)
