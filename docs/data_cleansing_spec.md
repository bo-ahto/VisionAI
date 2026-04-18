# 데이터 클렌징 명세서

> **작성일**: 2026-03-31
> **원본**: `k-artmarket 1차 데이터 정제 - k_artmarket_works_updated_s3.csv` (99,593건)
> **목표**: 명확하게 정리된 피처 + 확장된 매체 분류 + 호수 추출

---

## 1. 출력 스키마

### 기본 피처 (12개)

| # | 피처명 | 타입 | 설명 |
|---|--------|------|------|
| 1 | `idx` | int | 클렌징 후 0부터 순차 부여 |
| 2 | `img_file_name` | str | S3 이미지 URL (없으면 img_src에서 생성) |
| 3 | `name_kor` | str | 한글 작가명 (영문만 있으면 매핑/음역) |
| 4 | `name_eng` | str | 영문 작가명 (한글만 있으면 매핑/음역) |
| 5 | `title` | str | 작품 제목 |
| 6 | `materials` | str | 원본 재료 문자열 (정규화 후) |
| 7 | `ho` | float | 호수 — F타입 기준 연속값 (내부적으로 F/P/M/S 매칭 후 F 환산) |
| 8 | `price` | int | 낙찰가 (원화) |
| 9 | `source` | str | 경매사명 (정규화) |
| 10 | `sale_date` | str | 판매일 (YYYY-MM-DD) |
| 11 | `year_created` | str | 제작연도 (추후 수집, 현재 빈 문자열) |
| 12 | `uci` | str | 고유 식별자 |

### 파생 피처 (클렌징 시 함께 생성, 7개)

| # | 피처명 | 타입 | 생성 방법 |
|---|--------|------|-----------|
| 13 | `medium_category` | str | materials → 17개 매체 분류 (확장) |
| 14 | `support_category` | str | materials → 8개 지지체 분류 (확장) |
| 15 | `width_cm` | float | 가로 (cm 통일, inch→cm 변환) |
| 16 | `height_cm` | float | 세로 (cm 통일) |
| 17 | `surface_area` | float | width × height (cm²) |
| 18 | `artist_nationality` | str | 작가 국적 추정 (KR/JP/WS/UN) |
| 19 | `edition_number` | int/NaN | 판화 에디션 수 (size_raw에서 추출) |

> **제거된 피처** (중복 최소화):
> - ~~`source_type`~~ → `source`로 충분
> - ~~`is_sculpture`~~ → 그림류만 대상
> - ~~`ho_type`~~ → `ho`에 F기준 환산값으로 통합
> - ~~`is_foreign_artist`~~ → `artist_nationality`(KR/JP/WS/UN)로 대체
> - ~~`is_print`~~ → `medium_category`(판화/실크스크린/인쇄)로 구분 가능
> - ~~`material_language`~~ → `source`와 높은 상관 (중복)
> - ~~`title_has_hanja`~~ → 학습 시 title NLP 피처에서 생성 (클렌징 단계 불필요)
> - ~~`has_image`~~ → 이미지 피처 단계에서 추가

---

## 2. 피처별 정리 규칙

### 2.1 idx — 새로 부여

```
원본 idx 무시 → 클렌징 완료 후 0부터 순차 부여
```

### 2.2 img_file_name — S3 URL 보존

```
1순위: img_file_name (S3 URL, 99.7%)
2순위: img_src에서 fileId 추출 → S3 URL 생성
  https://k-artmarket.kr/...?fileId=FILE_ID00253365
  → https://nant-art-database.s3.ap-northeast-2.amazonaws.com/k_artmarket/FILE_ID00253365.jpg
```

### 2.3 name_kor / name_eng — 상호 채움

```
Step 1: 데이터 내 매핑 테이블 구축
  같은 작가가 다른 행에서 (name_kor + name_eng) 쌍으로 등장
  → {name_kor: name_eng} 및 {name_eng: name_kor} 양방향 매핑

Step 2: 매핑으로 채움
  name_kor 없고 name_eng 있음 → 매핑에서 name_kor 조회
  name_eng 없고 name_kor 있음 → 매핑에서 name_eng 조회

Step 3: 매핑 실패 시 음역 생성
  한글 → 영문: 한글 로마자 변환 (예: 김환기 → Kim Hwanki)
  영문 → 한글: 영문 음역 (예: Park Seo-Bo → 박서보) — 정확도 한계, 매핑 우선

Step 3.5: 성씨 로마자 변형 정규화 (매핑 구축 전)
  이/Lee/Yi/Rhee → 이, 김/Kim → 김, 박/Park/Pak → 박, 정/Jung/Chung → 정 등

Step 4: 둘 다 없는 경우
  title 있음 → name_kor="작가미상", name_eng="unknown"
  title도 없음 → 행 제거
```

### 2.4 artist_nationality — 국적 추정

```
4개 그룹: KR (한국) / JP (일본) / WS (서양) / UN (미상)

판정 순서:
1. 유명 작가 DB 매칭 (국적 확정) → 정확도 100%
2. 한글명 기반:
   - 2~4글자 + 한국 성씨 → KR
   - 5글자+ 음역 패턴 (카타카나식: OO OO) → JP 또는 WS
   - "작가미상" → UN
3. 영문명 기반:
   - 한국 성씨 로마자 (Kim, Lee, Park, Choi, ...) → KR
   - 일본 이름 패턴 (Takashi, Yayoi, -mura, -shita, ...) → JP
   - 나머지 → WS
4. 둘 다 없음 → UN

한국 성씨 DB (48종):
  Kim, Lee, Park, Choi, Jung, Cho, Kang, Yoon, Jang, Lim, Han, Oh,
  Seo, Shin, Kwon, Hwang, Ahn, Song, Yoo, Hong, Jeon, Ko, Moon, Yang,
  Son, Bae, Baek, Huh, Nam, Ryu, Ha, Woo, Kwak, Chun, Min, Byun, Noh,
  Yi, Rhee, Pak, Chung, Jeong, Yun, Im, Paik, Whang, Pyo, ...
```

### 2.5 materials — 정규화

```
Step 1: 한국어 약어 풀기
  지본채색 → 종이에 채색       지본묵서 → 종이에 먹    지본수묵 → 종이에 수묵
  견본채색 → 비단에 채색       견본수묵 → 비단에 수묵   견본자수 → 비단에 자수
  마본 → 마포에              면본 → 면에

Step 2: 영문 소문자 통일
  "Oil on Canvas" → "oil on canvas"

Step 3: 매체 분류 (17개)
Step 4: 지지체 분류 (8개)
```

### 2.6 ho — 호수 추출 (핵심)

```
Step 1: size_raw에서 직접 호수 파싱
  "20호" → ho=20
  "50F" → ho=50
  "100P" → 100호P의 F환산값 (면적 기준 area_to_ho_f)
  (0.1% 해당)

Step 2: width × height → ho_size.md 테이블 정확 매칭
  F/P/M/S 4개 타입 전체와 비교 (±2cm 허용)
  매칭 성공 → 해당 호수를 F환산값으로 출력
  예: 72.7 × 60.6 → 20호F → ho=20.0
  예: 100.0 × 72.7 → 40호P → F환산 ho=area_to_ho_f(7,270)≈29.5

Step 3: 정확 매칭 실패 → 면적 기반 F타입 보간
  area = width × height → area_to_ho_f(area) → 연속값
  예: 5,000cm² → ho≈17.3

Step 4: width/height 없음 → size_raw 파싱 후 Step 2-3 반복

Step 5: aspect ratio 검증
  매칭된 호수의 기대 비율과 실제 비율이 >30% 차이 시 → 면적 보간(Step 3)으로 대체

Step 6: 모두 실패 → ho=NaN
```

### 2.7 price — 가격 변환

```
문자열 "1,500,000" → 정수 1500000
쉼표 제거 → int 변환
0 이하 또는 NaN → 행 제거 (미낙찰)
```

### 2.8 source — 경매사명 정규화

```
25종 → 10종:
  "케이" → "케이옥션"
  "헤럴드 아트데이" / "HERALD ARTDAY AUCTION" → "헤럴드아트데이"
  "라이즈" → "라이즈아트"
  "꼬" → "꼬모옥션"
  "마이" / "마이아" → "마이아트옥션"
  "대구 신세계 문화홀 8층" → "기타"
  "서울옥션 3월 22일..." → "서울옥션" (auction_name에서 경매사 추출)
  "2022년 9월 183회 온라인" → 연도+회차에서 경매사 추정 또는 "기타"
```

### 2.9 unit 처리 — cm 통일

```
cm (99.95%) → 그대로
in (46건) → × 2.54 변환
m (2건) → × 100 변환
```

---

## 3. 매체 분류 확장 (8 → 17 카테고리)

### 3.1 medium_category (17개)

| 카테고리 | 인식 패턴 (한/영) | 예상 건수 |
|----------|-------------------|-----------|
| **유화** | 유채, oil | 18,538 |
| **수묵** | 수묵, 먹, 묵서, ink, Korean ink | 22,380 + 2,086 |
| **아크릴** | 아크릴, acrylic | 8,281 |
| **수채** (NEW) | 수채, watercolor, 과슈, gouache, aquarelle | ~1,935 |
| **채색** | 채색, 담채, color on, 분채, 암채, 석채 | 4,857 + 300 |
| **판화** | 석판화, lithograph, 에칭, etching, 목판화, woodcut, 메조틴트, mezzotint, 드라이포인트, drypoint, 아쿼틴트, aquatint, 콜라그래프, 믹소그라피 | 9,900 + 1,500 |
| **실크스크린** (NEW) | 실크스크린, silkscreen, 스크린프린트, screenprint, 세리그라프, serigraph | ~2,100 |
| **혼합재료** | 혼합, mixed media | 5,630 |
| **사진/디지털** | 사진, 디지털, c-print, C-프린트, 람다, lambda, photograph, digital, 지클레이, giclee, 잉크젯, inkjet | 1,046 + 500 |
| **연필/드로잉** (NEW) | 연필, pencil, 색연필, colored pencil, 콩테, conte, 파스텔, pastel, 목탄, charcoal, 숯, 크레용, crayon, 그라파이트, graphite, 흑연, 볼펜, ballpoint, 마커, marker, 펜, pen | ~2,300 |
| **조각** (NEW) | 브론즈, bronze, 청동, 대리석, marble, 화강암, granite, 레진, resin, 캐스트, cast, carved | ~2,000 |
| **도자** (NEW) | 도자, 자기, ceramic, porcelain, 백자, 세라믹, stoneware, terracotta | ~400 |
| **목공예** (NEW) | 소나무, 오동나무, 괴목, 은행나무, 나무에, carved on wood, painting on wood | ~1,200 |
| **섬유** (NEW) | 자수, embroidery, 타피스트리, tapestry, 직물, fabric, needlework | ~200 |
| **인쇄/복제** (NEW) | 오프셋, offset, 인쇄, 프린트(단독), 포스터 | ~1,300 |
| **옻칠/래커** (NEW) | 옻칠, lacquer, urushi, 나전, 칠기 | ~100 |
| **기타** | 위 모든 패턴 미매칭 | ~5% 목표 |

### 3.2 support_category (8개)

| 카테고리 | 인식 패턴 | 기본값 매핑 |
|----------|-----------|------------|
| **캔버스** | 캔버스, canvas, 린넨, linen | — |
| **종이** | 종이, paper, 지본, 한지, Korean paper | 판화→종이, 실크스크린→종이, 인쇄→종이 |
| **비단** | 비단, silk, 견본, 견 | — |
| **목재** | 목재, wood, 나무, 패널, panel, 보드 | — |
| **금속** | 금속, 알루미늄, aluminum, 철, iron, steel, 스틸 | — |
| **섬유** (NEW) | 면, cotton, 마포, 광목, 패브릭, fabric | — |
| **없음** (NEW) | — | 조각→없음, 도자→없음 |
| **기타** | 미매칭 | — |

### 3.3 분류 우선순위 규칙

```
1. 한국어 약어 풀기 (지본→종이에, 견본→비단에)
2. 영문 소문자 통일
3. 매체 분류 — 우선순위 순:
   유화 > 아크릴 > 수채 > 수묵 > 채색 > 연필/드로잉 > 판화 > 실크스크린 >
   인쇄/복제 > 사진/디지털 > 혼합재료(+콜라주) > 조각 > 도자 > 옻칠/래커 > 목공예 > 섬유 > 기타
4. 지지체 분류 — 명시적 매칭 우선, 없으면 매체 기본값
```

---

## 4. 비미술 클렌징

기존 `data_cleanser.py` 6개 카테고리 유지:

| 카테고리 | 판정 기준 |
|----------|-----------|
| 이벤트 | 재료 없음 + 항공권/숙박권/식사권/상품권 |
| 주류 | 재료 없음 + 위스키/테이스팅 |
| 명품 | Birkin/Rolex 또는 (재료 없음 + "가방") |
| 보석 | 18K/14K/다이아몬드 |
| 도자공예 | 재료가 ^도자기/^자기$/분청/옹기 (나전/칠기는 옻칠/래커 매체로 분류되므로 제외) |
| 목공예 | 재료가 순수 목재명만 |

---

## 5. 추후 수집 피처

> 클렌징 단계에서는 **중복 최소화 원칙**에 따라 파생 피처를 최소화.
> 아래 피처는 별도 데이터 수집 후 추가.

| 피처 | 출처 | 설명 |
|------|------|------|
| `year_created` | 별도 수집 | 제작연도 |
| `artist_birth_year` | KAWF/Artsy | 생년 |
| `is_deceased` | KAWF/Artsy | 작고 여부 |
| `gallery_tier` | KIAF | 소속 갤러리 등급 |

---

## 6. 처리 파이프라인

```
원본 CSV (99,593건)
  ↓
1. 헤더 정리 (첫 행 중복 제거)
  ↓
2. 비미술 클렌징 (이벤트/주류/명품/보석/도자공예/목공예)
  ↓
3. 가격 필터 (price ≤ 0 제거)
  ↓
4. 작가명 상호 채움 (매핑 → 음역 → 미상)
  ↓
5. materials 정규화 (약어 풀기 → 소문자 → 분류)
  ↓
6. 단위 통일 (inch→cm, m→cm) — 호수 추출 전 필수
  ↓
7. 크기/호수 추출 (width×height → ho_size.md 매칭)
  ↓
8. 경매사명 정규화
  ↓
9. 파생 피처 생성 (artist_nationality, edition_number)
  ↓
10. idx 재부여 + 중복 제거 (uci 기반)
  ↓
클렌징 완료 CSV
```
