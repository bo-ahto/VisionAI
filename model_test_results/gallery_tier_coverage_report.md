# 갤러리 티어 매핑 커버리지 분석 (Phase 1A)

- 협력자 리스트: 89 갤러리/기관
- Artsy 데이터: 7,640 작품 / 66 갤러리
- Saatchi 데이터: 21,721 작품 (Saatchi Art 단일)

## Artsy 매칭 결과

- 매칭된 갤러리: **11/66** (17%)
- 매칭된 작품: **999/7,640** (13.1%)

### 매칭된 갤러리 (작품 수 내림차순)

| Artsy 영문명 | 한글 매칭 | Tier | Class | 작품 수 |
|---|---|:---:|---|---:|
| Kimreeaa Gallery | 김리아갤러리 | Tier C | 하이-엔드 라이징/이머징 | 515 |
| Art Sohyang | 아트소향 | Tier C | 하이-엔드 라이징/이머징 | 103 |
| BHAK | BHAK(비에이치에이케이) | Tier C | 하이-엔드 라이징/이머징 | 92 |
| Gallery Planet | 갤러리 플래닛 | Tier C | 하이-엔드 라이징/이머징 | 92 |
| CHOI&CHOI | 초이앤초이 갤러리 | Tier B | 갤러리 | 81 |
| CYLINDER | 실린더 | Tier C | 하이-엔드 라이징/이머징 | 41 |
| Leehwaik Gallery | 이화익갤러리 | Tier B | 갤러리 | 33 |
| SPACE Willing N Dealing | 스페이스 윌링앤딜링 | Tier C | 하이-엔드 라이징/이머징 | 23 |
| ThisWeekendRoom | 디스위켄드룸 | Tier C | 하이-엔드 라이징/이머징 | 10 |
| FOUNDRY SEOUL | 파운드리 서울 | Tier C | 하이-엔드 라이징/이머징 | 8 |
| Artside Gallery | 아트사이드 갤러리 | Tier C | 하이-엔드 라이징/이머징 | 1 |

### Tier 분포 (Artsy)

| Tier | 작품 수 | 비중 |
|:---:|---:|---:|
| Tier A | 0 | 0.0% |
| Tier B | 114 | 1.5% |
| Tier C | 885 | 11.6% |
| Tier D | 0 | 0.0% |
| Tier E | 6,641 | 86.9% |

### Class 분포 (Artsy)

| Class | 작품 수 | 비중 |
|---|---:|---:|
| 미분류 | 6,641 | 86.9% |
| 하이-엔드 라이징/이머징 | 885 | 11.6% |
| 갤러리 | 114 | 1.5% |

## Saatchi

Saatchi Art 단일 — 갤러리 개념 미적용, 모두 Tier E (온라인 플랫폼)

## 통합 (Artsy + Saatchi)

### Tier 분포

| Tier | 작품 수 | 비중 |
|:---:|---:|---:|
| Tier A | 0 | 0.0% |
| Tier B | 114 | 0.4% |
| Tier C | 885 | 3.0% |
| Tier D | 0 | 0.0% |
| Tier E | 28,362 | 96.6% |

## 미매칭 갤러리 Top 30 (Artsy)

| 영문명 | 작품 수 | 비고 |
|---|---:|---|
| Art Spoon | 707 | — |
| Gallery Grimson | 587 | — |
| Suppoment Gallery | 553 | — |
| Keumsan Gallery | 548 | — |
| The Trinity Gallery | 469 | — |
| MOOWOOSOO Gallery | 379 | — |
| Art in Dongsan | 279 | — |
| Objecthood | 273 | — |
| GalleryMEME | 244 | — |
| Gallery Playlist | 231 | — |
| Galerie GAIA | 202 | — |
| Kuns Gallery | 161 | — |
| THEO | 156 | — |
| art.ness | 155 | — |
| Space776 | 111 | — |
| Genuine Global Company | 109 | — |
| CDA | 107 | — |
| LYNN Fine Art Gallery | 105 | — |
| IdeelArt | 102 | — |
| Dohing Art | 85 | — |
| Gallery We | 72 | — |
| Combineworks Seoul | 71 | — |
| AVO | 66 | — |
| UARTSPACE | 64 | — |
| SPACE SO | 64 | — |
| galerie bruno massa | 62 | — |
| Art Works Paris Seoul Gallery | 59 | — |
| ROY Gallery | 58 | — |
| Gallery Ichon | 57 | — |
| oaoa | 55 | — |

## 결론 — Phase 1B 진행 판단

- **Artsy 매칭 비중**: 13.1% (999/7,640)
- **통합 Tier A~D**: 999 / 29,361 (3.4%)
- **Tier A**: 0건  /  **Tier D**: 0건
- **Tier B**: 114건  /  **Tier C**: 885건
- **Tier E**: 28,362건 (96.6%)

### 판정: **Phase 1B (피처 도입) 보류 권장**

근거:
1. **Tier A/D = 0건** — 분류 5단계 중 2단계가 학습 데이터에 존재하지 않음. 사실상 binary 신호(`Tier B/C` vs `Tier E`)로 축소됨.
2. **Tier E = 96.6%** — 통합 데이터의 96.6%가 미분류로 떨어짐 (Saatchi 21,721건 + Artsy 미매칭 6,641건). 압도적 대다수가 같은 값이면 모델이 신호로 학습할 정보량이 거의 없음.
3. **Artsy 메인스트림 부재** — Tier A 갤러리(국제갤러리, 가나아트, 갤러리현대 등)는 Artsy 데이터셋에 등록되어 있지 않음(Frieze/Art Basel 메인 갤러리들은 별도 채널 사용). 협력자 리스트의 핵심 변별력이 학습 데이터에 반영되지 않음.
4. **이미 `gallery_tier` 피처 존재** — `primary_predictor.py`의 기존 `gallery_tier` (galleries_count 기반 휴리스틱)가 동일 신호의 일부를 이미 학습 중. v3 매핑 추가 효과는 한계.

### 대안

- **A. 데이터 확장**: Artsy 외 채널(갤러리 자체 사이트, 아트뉴스, 미술시장 데이터) 수집으로 Tier A 갤러리 데이터를 확보한 후 재시도.
- **B. 협력자 검수**: 미매칭 Top 갤러리 30개에 대해 협력자가 한글명 매핑 또는 Tier 부여를 추가 검토 (현재 매핑 11개 → 30~40개로 확장 가능성).
- **C. 다른 P0 액션 우선**: `MdAPE_개선_액션플랜_20260427.md`의 다른 항목 (career-stage v2, source-split-models, cold-start-data-enrichment)을 먼저 진행.

### 다음 단계 권장

- 본 리포트를 협력자에게 공유 → 미매칭 Top 갤러리 매핑 검수 요청
- 그 사이 P0 다른 항목(career-stage v2 등)부터 진행
