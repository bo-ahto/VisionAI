# 갤러리 티어 매핑 커버리지 + 가격 분리도 분석 (Phase 1A v2)

> 코덱스 리뷰 반영본. v1의 결정적 결함(Saatchi 강제 재코딩, 가격 분리도 미측정,
> Tier D 매핑 미구현)을 보정하고 Phase 1B 진행 판단을 재구성.

- 협력자 리스트: **118** 갤러리/기관 (NaN 1건 제외)
- Artsy 학습 데이터: **7,289** 작품 / 66 갤러리 (입체 제외 후)
- Saatchi 학습 데이터: **21,087** 작품 (Saatchi Art 단일 — source='saatchi'로 별도 처리)

## 1. Artsy 매칭 결과

- 매칭된 갤러리: **41/66** (62%)
- 매칭된 작품: **6,902/7,289** (94.7%)
- 미매칭 Top 30 = **387** 건 = 미매칭의 **100.0%** / Artsy 전체의 **5.3%**

현재 94.7%는 **lookup의 하한**이지 Phase 1B의 상한이 아님. Top 30 검수만으로 80%+ 추가 매핑 가능성.

### 매칭된 갤러리 (작품 수 내림차순)

| Artsy 영문명 | 한글 매칭 | Tier | Class | 작품 수 |
|---|---|:---:|---|---:|
| Art Spoon | 아트스푼 | Tier D | 기타 | 659 |
| Gallery Grimson | 갤러리 그림손 | Tier B | 갤러리 | 574 |
| Suppoment Gallery | 써포먼트 갤러리 | Tier B | 갤러리 | 550 |
| Kimreeaa Gallery | 김리아갤러리 | Tier C | 하이-엔드 라이징/이머징 | 507 |
| Keumsan Gallery | 금산갤러리 | Tier B | 갤러리 | 485 |
| The Trinity Gallery | 더 트리니티 갤러리 | Tier D | 갤러리 | 465 |
| MOOWOOSOO Gallery | 무우수갤러리 | Tier D | 갤러리 | 365 |
| Objecthood | 오브제후드 | Tier C | 갤러리 | 271 |
| Art in Dongsan | 아트인동산 | Tier D | 갤러리 | 250 |
| GalleryMEME | 갤러리밈 | Tier B | 갤러리 | 239 |
| Gallery Playlist | 갤러리 플레이리스트 | Tier C | 갤러리 | 227 |
| Galerie GAIA | 갤러리 가이아 | Tier B | 갤러리 | 202 |
| Kuns Gallery | 쿤스 갤러리 | Tier D | 갤러리 | 160 |
| art.ness | 아트니스 | Tier D | 기타 | 138 |
| THEO | 띠오 | Tier C | 갤러리 | 136 |
| Genuine Global Company | 제뉴인글로벌컴퍼니 | Tier D | 기타 | 109 |
| LYNN Fine Art Gallery | 린파인아트 갤러리 | Tier B | 갤러리 | 103 |
| Art Sohyang | 아트소향 | Tier C | 하이-엔드 라이징/이머징 | 103 |
| IdeelArt | 아이딜아트 | Tier D | 기타 | 102 |
| Space776 | 스페이스776 | Tier B | 갤러리 | 101 |
| CDA | 씨디에이 | Tier C | 갤러리 | 100 |
| Dohing Art | 도잉아트 | Tier B | 갤러리 | 83 |
| Gallery Planet | 갤러리 플래닛 | Tier C | 하이-엔드 라이징/이머징 | 83 |
| CHOI&CHOI | 초이앤초이 갤러리 | Tier B | 갤러리 | 81 |
| BHAK | BHAK(비에이치에이케이) | Tier C | 하이-엔드 라이징/이머징 | 78 |
| Gallery We | 갤러리위 | Tier B | 갤러리 | 72 |
| Combineworks Seoul | 컴바인웍스 갤러리 | Tier C | 갤러리 | 71 |
| AVO | 에이뷔오 | Tier C | 갤러리 | 66 |
| UARTSPACE | 유아트스페이스 | Tier B | 갤러리 | 64 |
| galerie bruno massa | 갤러리 브루노 마사 | Tier D | 갤러리 | 62 |
| Art Works Paris Seoul Gallery | 아트웍스 파리 서울 갤러리 | Tier D | 갤러리 | 59 |
| ROY Gallery | 로이갤러리 | Tier C | 갤러리 | 58 |
| SPACE SO | 스페이스 소 | Tier D | 갤러리 | 58 |
| oaoa | 오에이오에이 | Tier C | 갤러리 | 55 |
| Gallery Ichon | 이촌화랑 | Tier D | 갤러리 | 53 |
| CYLINDER | 실린더 | Tier C | 하이-엔드 라이징/이머징 | 39 |
| Leehwaik Gallery | 이화익갤러리 | Tier B | 갤러리 | 33 |
| SPACE Willing N Dealing | 스페이스 윌링앤딜링 | Tier C | 하이-엔드 라이징/이머징 | 23 |
| ThisWeekendRoom | 디스위켄드룸 | Tier C | 하이-엔드 라이징/이머징 | 9 |
| FOUNDRY SEOUL | 파운드리 서울 | Tier C | 하이-엔드 라이징/이머징 | 8 |
| Artside Gallery | 아트사이드 갤러리 | Tier C | 하이-엔드 라이징/이머징 | 1 |

## 2. Tier 분포 (Artsy-only, 학습 데이터)

| Tier | Default | Default % | +D-fallback | +D-fallback % |
|:---:|---:|---:|---:|---:|
| Tier A | 0 | 0.0% | 0 | 0.0% |
| Tier B | 2,587 | 35.5% | 2,587 | 35.5% |
| Tier C | 1,835 | 25.2% | 1,835 | 25.2% |
| Tier D | 2,480 | 34.0% | 2,867 | 39.3% |
| Tier E | 387 | 5.3% | 0 | 0.0% |

- **Default**: 협력자 리스트 정확 매칭만 적용. 미매칭은 모두 Tier E.
- **+D-fallback**: 미매칭 + commercial gallery type → Tier D로 떨어뜨리는 sensitivity rule ("한국화랑협회 회원/지역 중소" 카테고리 라벨이 데이터에 직접 없으므로 추정 규칙).

## 3. 가격 분리도 (핵심) — Artsy-only Default 매핑

**이게 Phase 1B 의미 여부의 결정적 지표.** 커버리지가 낮아도 매칭된 Tier가 가격을 의미 있게 분리한다면 가치가 있고, 반대로 분리가 약하면 매핑을 늘려도 의미가 없다.

| Tier | n | median (KRW) | 95% CI | Q25 | Q75 | ln_mean | ln_std |
|:---:|---:|---:|---|---:|---:|---:|---:|
| Tier A | 0 | - | - | - | - | - | - |
| Tier B | 2,587 | 6,900,000 | [6,624,000 ~ 7,521,000] | 3,036,000 | 16,560,000 | 15.818 | 1.228 |
| Tier C | 1,835 | 3,146,400 | [2,760,000 ~ 3,312,000] | 1,380,000 | 7,314,000 | 15.010 | 1.196 |
| Tier D | 2,480 | 2,760,000 | [2,760,000 ~ 2,856,600] | 1,380,000 | 6,900,000 | 14.931 | 1.238 |
| Tier E | 387 | 7,590,000 | [6,113,400 ~ 9,936,000] | 2,645,500 | 24,150,000 | 15.981 | 1.536 |

### 해석

- **Tier B vs E**: median 6,900,000 vs 7,590,000 = **0.91x**. 95% CI 겹침. 표본 충분 → underpowered.
- **Tier C vs E**: median 3,146,400 vs 7,590,000 = **0.41x**. 95% CI 비겹침. C 라벨은 가격 신호로 약함 — 협력자가 정의한 'Tier C 하이엔드 라이징/이머징' 분류가 실제 거래 가격과 직접 연결되지 않음.

## 4. 기존 `gallery_tier` 피처와의 교차표

기존 `gallery_tier`는 `city_count + avg_price + work_count` 휴리스틱 (estimate_gallery_tier in scripts/prepare_primary_market_dataset.py:116). v3 Tier가 같은 신호인지 다른 축인지 검증.

| v3 \ existing | existing=2 | existing=3 | existing=4 | existing=5 |
|:---:|:---:|:---:|:---:|:---:|
| v3=Tier B | 1232 | 1355 | 0 | 0 |
| v3=Tier C | 466 | 1189 | 163 | 17 |
| v3=Tier D | 523 | 1298 | 659 | 0 |
| v3=Tier E | 58 | 235 | 92 | 2 |

v3 Tier E와 Tier C 모두 기존 gallery_tier 여러 값에 걸쳐 있다면 **다른 축**. 한 값에 집중되면 **중복 신호**.

## 5. Saatchi (별도 처리)

- 작품 수: 21,087
- 기존 `gallery_tier`: **3** (단일값)
- price median: **2,608,200 KRW** (Q25 1,104,000 ~ Q75 6,085,800)
- ln_mean: 14.855

> 온라인 플랫폼 — 갤러리 개념 미적용. 기존 파이프라인은 source='saatchi'로 분리 처리.

Artsy median과 Saatchi median을 직접 비교하는 것은 source 효과 + tier 효과가 섞여 있어 부적절.
**v1 보고서의 통합 96.6% Tier E 수치는 source 효과로 희석된 결과이므로 폐기.**

## 6. 미매칭 Top 30 — 협력자 검수 후보 리스트

이 30개를 협력자가 한글명/Tier 확정 시 Artsy unmatched의 **100.0%**, 전체의 **5.3%**가 재평가됨. **ROI 가장 높은 후속 작업.**

| 순위 | 영문명 | 작품 수 | 추정 한글 (검수 필요) | 리스트 등재? |
|---:|---|---:|---|:---:|
| 1 | WEART | 46 | ? | NO |
| 2 | Gallery Mondeouvert | 46 | ? | NO |
| 3 | KWANHOON GALLERY | 41 | ? | NO |
| 4 | Aither | 33 | ? | NO |
| 5 | Art Space 3 | 31 | ? | NO |
| 6 | Gallery JJ | 30 | ? | NO |
| 7 | GALLERY82 | 23 | ? | NO |
| 8 | PAGEROOM8 | 23 | ? | NO |
| 9 | The Untitled Void | 17 | ? | NO |
| 10 | Gallery Vit | 16 | ? | NO |
| 11 | collast | 12 | ? | NO |
| 12 | Akunst Gallery | 12 | ? | NO |
| 13 | GALLERY MAC | 9 | ? | NO |
| 14 | Punto Blu | 8 | ? | NO |
| 15 | GALLERY SERENE SPACE | 7 | ? | NO |
| 16 | SARAHCROWN    New York | 7 | ? | NO |
| 17 | FIM | 5 | ? | NO |
| 18 | LKIF Gallery | 5 | ? | NO |
| 19 | Luan & Co. | 3 | ? | NO |
| 20 | Sarah Hong Gallery | 3 | ? | NO |
| 21 | HORI ART SPACE | 3 | ? | NO |
| 22 | Gallery Jinsun | 3 | ? | NO |
| 23 | ATELIER AKI | 2 | ? | NO |
| 24 | Gallery Save | 1 | ? | NO |
| 25 | UNAW Gallery | 1 | ? | NO |

추정 한글명 중 'NO' 표시는 협력자 리스트(88건)에 없음을 의미. 즉 **이름 표기 차이가 아니라**, 
이들이 협력자 리스트에 등록 안 된 갤러리. 협력자가 리스트를 확장하거나 Tier D/E를 명시해야 함.

## 결론 — Phase 1B 진행 판단

v1의 "보류 권장" 결론은 **철회**. 보유 데이터로는 결정 자체가 불가능.

### 핵심 근거

- **Tier B vs E**: 6,900,000 vs 7,590,000 = 0.91x — 신호 있음, 표본 부족 (B=2587건)
- **Tier C vs E**: 3,146,400 vs 7,590,000 = 0.41x — 가격 분리 약함
- **Top 30 미매칭이 81%** 점유 → 검수 후 그림이 크게 바뀔 가능성 높음
- 기존 `gallery_tier`와 v3는 다른 축 (cross-tab 참고)

### ROI 우선순위 (코덱스 권장)

1. **A. 협력자 검수** (1순위) — Top 30 unmatched 한글명/Tier 확정 → Artsy 81% 재평가
2. **C. 다른 P0 우선** (2순위) — 검수 결과 나오기 전까지 career-stage v2 / source-split 등 진행
3. **B. Artsy 외 데이터** (3순위) — 검수 + 가격 분리도 확인 후, 신호 약하면 그때 착수

### 재판정 트리거

- 검수 후 매핑이 30+ 도달하고 Tier B 표본이 300+ 늘어나면 → ablation 진행
- Tier B의 가격 분리(2x+)가 검수 후에도 유지되면 → Phase 1B 진행
- 검수 후에도 Tier C가 E와 분리 안 되면 → Tier C 라벨은 학습 신호로 사용 X (B만 binary)
