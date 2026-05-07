# Stage 5A — Source Scorecard (Week 1 결과)

> **작성일**: 2026-05-07 (Week 1 종료)
> **사전등록**: `docs/stage5a_acquisition_prereg_20260507.md` §3 5축 scorecard
> **방법**: WebFetch (robots.txt) + WebSearch (한국 작가 sample, 4 source × 1-3 query)
> **샘플 작가**: Stage 4 depth ≥25 + test-eligible 12명 중 top 3 (do-you-hwang / bae-joon-sung / kwon-hye-jo) + 글로벌 인지도 비교군 (Lee Ufan)

> ⚠️ **Honest caveat**: 본 평가는 Week 1 정성 feasibility — 정량 cover %, corr 측정은 5B 이후. 코덱스 권고대로 `정량 관찰` vs `정성 해석` 분리 표기.

## 1. 한 줄 요약 (의사결정자용)

> **본질**: Stage 4 모집단 = Artsy primary market (신진/중견 작가 1차 판매) ↔ Auction archives = **secondary market (재판매, 시장 확립 작가)**. **Source-task fit 실패** (source quality 실패 X — 코덱스).
>
> **Sample (depth ≥25 작가 6명)**: 모든 auction (Seoul / K / Sotheby's / Christie's) cover **0/6** (Lee Ufan 비교군은 모두 cover ✓, 패턴 명확). → **Auction-first 경로 사실상 REJECT**.
>
> **Artsy CV** (이미 url 가용 1,925) 만 **BORDERLINE** — coverage / cost / legal 모두 ✓ 이지만 **핵심 약점 = price directness ✗** (Stage 4 의 핵심 가설 = 가격 결정 요인 직접 해결 X). → 사전등록 §6.2 보류 적용 (Week 2-3 추가 검토).

## 2. 핵심 발견 3

1. **Auction = 시장 확립 작가 한정**: Lee Ufan (Sotheby's 10+ lots, Seoul Auction 다수) vs Bae Joon Sung / Do-you Hwang / Lee 외 신진작가 (모든 auction 검색 결과 0)
2. **Stage 4 cohort 와 mismatch**: Stage 4 warm 120명 = 비교적 신진/중견 (Artsy primary market) → auction secondary market 과 본질적 cohort 차이
3. **Christie's = anti-bot**: WebFetch / Google site search 모두 차단 — acquisition cost 매우 높음 (API 협상 / scraping infra 필요)

## 3. 5축 Scorecard (사전등록 §3)

| Source | 1. Coverage (한국 sample) | 2. Price directness | 3. Integration cost | 4. Legal risk | 5. Incremental signal | Provisional |
|---|---|---|---|---|---|---|
| **Seoul Auction** | ✗ (Stage 4 신진 0/3 hit / Lee Ufan ✓) | ✓ 직접 (낙찰가) | △ (HTML 파싱) | △ ALLOW-LIKELY (robots: `/mypage/` 만 차단) | △ Auction price anchor (단, Stage 4 cohort 거의 없음) | **REJECT** (coverage ✗) |
| **K-Auction** | ✗ (Stage 4 신진 0/1 hit / 김창열·이배 등 cover) | ✓ 직접 | △ (KA-Search URL 확인 `/Home/Search?key=`) | △ ALLOW-LIKELY (robots 제한 X) | △ 동일 | **REJECT** (coverage ✗) |
| **Christie's** | (측정 X — anti-bot) | ✓ 직접 | ✗ 매우 높음 (Cloudflare anti-bot, Google site search 차단) | ✗ LEGAL-REVIEW (TOS 미확인 + 접근 차단) | △ 글로벌 cover (단, Stage 4 cohort 거의 없음 추정) | **REJECT** (integration + legal ✗) |
| **Sotheby's** | ✗ (Lee Ufan ✓ 10+ lots / Stage 4 신진 0) | ✓ 직접 | △ (crawl-delay 15s 큼) | △ ALLOW-LIKELY (robots: PDF/api만 차단) | △ 동일 | **REJECT** (coverage ✗) |
| **Artsy CV** (이미 url 가용 1,925) | ✓ 100% cover (Artsy 모집단 = Stage 4 모집단 동일) | ✗ 정성 (CV / shows count, 가격 X) | ✓ 매우 낮음 (이미 url 보유) | ✓ ALLOW-LIKELY (robots: 검색 query 일부 차단, artist 페이지 허용) | △ Provenance / exhibition signal (가격 직접성 X) | **BORDERLINE** |

### 3.1 평가 라벨 정의 (코덱스 권고)
- **PASS-ready**: 5축 모두 실질적으로 양호, 법적 red flag 없음
- **BORDERLINE**: 4축 양호 또는 legal 미확정
- **REJECT**: coverage 부족 / directness 약함 / access blocked

## 4. Sample Evidence (정량 관찰)

### 4.1 Seoul Auction 검색 결과
| 작가 | 결과 | 출처 |
|---|---|---|
| do-you-hwang (황도유) | **0 hits** (Stage 4 train 218건) | site:seoulauction.com 검색 |
| bae-joon-sung (배준성) | **0 hits** (Stage 4 train 86건) | 동일 |
| kwon-hye-jo (권혜조) | **0 hits** (패턴 확정) | 동일 |
| changmin-lim (임창민) | **0 hits** | OR 검색 |
| lee-in-seob (이인섭) | **0 hits** | OR 검색 |
| yoo-suntai (유선태) | **0 hits** | OR 검색 |
| **Lee Ufan (이우환, 비교군)** | **다수 hits** (private sale / contemporary art lot) | https://www.seoulauction.com/auction/live/1037/62 |
| → Stage 4 sample 6/6 모두 0 hits → cover **0%** (95% CI [0%, 39%], n=6) |

### 4.2 K-Auction 검색 결과
| 작가 | 결과 | 출처 |
|---|---|---|
| bae-joon-sung (배준성) | **0 hits** | site:k-auction.com 검색 |
| 김창열 / 이배 / 우국원 | **다수 hits** (KA-Search URL 패턴 확인) | https://www.k-auction.com/Home/Search?key=... |

### 4.3 Sotheby's
| 작가 | 결과 | 출처 |
|---|---|---|
| Lee Ufan (비교군) | **artist page + 10+ lots** (HK / 글로벌 sales 다수) | https://www.sothebys.com/en/artists/lee-ufan |
| Stage 4 신진 | (sample X — Lee Ufan 다수 cover 후 패턴 확정) | — |

### 4.4 Christie's
| 항목 | 결과 |
|---|---|
| WebFetch robots.txt | **fetch 실패** ("Claude Code is unable to fetch from www.christies.com") |
| site search Lee Ufan | **0 hits** (Google indexing 차단 추정) |
| → Anti-bot / Cloudflare 가능성 → **integration cost ✗ + legal LEGAL-REVIEW** |

### 4.5 Artsy CV (정성)
- `data/artsy_kr_artists_with_links.csv` (1,925 작가 모두 `url_cv` 가용)
- robots.txt: 검색 query 일부 차단, artist 페이지 자체 허용
- 단, **CV 페이지의 정량 feature 추출 미검증** (5B 이후 NLP / parsing 필요)
- 본 prereg §4.2 의 정량화 규칙 사전 제한: 단순 count (solo / group / fair / institution) 만 사용

## 5. Provisional 판정 결과

| Source | Provisional 라벨 | 사유 |
|---|---|---|
| Seoul Auction | **REJECT** | Coverage ✗ (Stage 4 cohort 미스매치, 시장 확립 작가만) |
| K-Auction | **REJECT** | Coverage ✗ (동일) |
| Christie's | **REJECT** | Integration cost ✗ + Legal LEGAL-REVIEW (anti-bot) |
| Sotheby's | **REJECT** | Coverage ✗ (글로벌 cover 가능하나 Stage 4 cohort 거의 없음) |
| **Artsy CV** | **BORDERLINE** | Coverage ✓ (모집단 동일) / directness ✗ / cost ✓ / legal ✓ / signal △ |

## 6. 사전등록 §6 의사결정 적용

### 6.1 사전등록 §6.1 PASS 조건
- "1+ source 가 5축 모두 ✓ 또는 2+ source 가 4축 ✓ (BORDERLINE)"
- **현 결과**: Artsy CV 만 BORDERLINE 1건 → **PASS 미달**

### 6.2 사전등록 §6.2 BORDERLINE
- "PASS source 0 + BORDERLINE 1 — 후속 1주 검토" 적용 가능
- 또는 **§6.3 REJECT** = "모든 candidate REJECT" — Artsy CV 가 BORDERLINE 이라 §6.3 까지는 가지 X

→ **본 cycle 판정**: **§6.2 보류** (Stage 5A Week 2-3 추가 검토)

## 7. Week 2-3 액션 (코덱스 권고)

### 7.1 Artsy CV 정량 feasibility 확장
- 5B 이전: 1,925 작가 의 url_cv 페이지 random 5명 fetch → CV 구조 / parsing 가능성 검증
- 단순 count (solo / group / fair / institution) feature 추출 가능성
- 단, **가격 anchor 부재** = Stage 4 의 핵심 가설 (feature 부족 = 가격 결정 요인) 직접 해결 X

### 7.2 새 source 후보 검토 (사전등록 외)
- 코덱스 권고: "현 cohort = Artsy primary market (신진/중견)" → auction (secondary market) mismatch
- 후보:
  * **Galerie 직접 데이터** (Kukje / 학고재 / Hyundai Gallery 등 한국 주요 갤러리) — 작가 매물 history (Stage 4 cohort 와 일치 가능성 높음)
  * **Artsy followers / 매출 history** (Artsy 자체 데이터 활용 — 가격 anchor 미흡하나 시장 활동 신호)
  * **미술품 가격 지수** (Artprice / Artnet — paid, license 비용)
- → **사전등록 외 source 추가 = deviation log 필수** (HARK 회피)

### 7.3 의사결정 분기 (코덱스 권고)
| 시나리오 | 액션 |
|---|---|
| Artsy CV 만 BORDERLINE → 단독 진행 | 5B 진행 (단, 가격 anchor 부재 caveat 명시) |
| 새 source 후보 추가 (galerie 등) | 사전등록 deviation log 등록 + Week 2-3 추가 feasibility |
| 모든 source 부적합 | Stage 5 자체 보류 / 운영 calibration 만 채택 (단기 트랙 작업 4) |

## 8. Stage 5A Week 1 결론

> **본질적 mismatch 발견**: Auction archives = secondary market (시장 확립 작가) ↔ Stage 4 cohort = primary market (신진/중견). 사전등록 1순위 source 모두 REJECT.

### 8.1 사전등록 vs 실측 차이 (deviation)
- **사전등록 §4.1 1순위**: K-Auction / Seoul Auction (한국 전문 + 한국 작가 cover 자연 높음 가정)
- **실측**: 한국 auction 도 시장 확립 작가만 cover, Stage 4 cohort cover **0/6** (≈ 0%)
- **분류 (5A 절차)**: **minor** — 사전등록 § 6.2 보류 적용 (정상 흐름)
- **분류 (5C 영향, 별도)**: **실질적 제약** — F1 (auction price anchor) family 실현 불가 → 5C primary Δ ≤ -2.0%p PASS 확률 낮음 (코덱스)
- **deviation log entry**: `docs/methodology_deviation_log.md` 2026-05-07 추가

### 8.2 다음 단계 권고
1. **Artsy CV** 정량 feasibility 확장 (Week 2)
2. **새 source 후보** 검토 (Galerie / Artsy 시장 활동 / Artprice) — sponsorship / license 검토 필요
3. **§6.2 보류 유지** — 1주 추가 검토 후 PASS 또는 REJECT 재판정

### 8.3 5C prereg 영향
- 5C 의 placeholder feature dictionary 는 변경 없음 (auction price anchor / market activity / provenance family 모두 유지)
- 단, **F1 (auction anchor) 실현 가능성 ✗** → 5B 진행 시 F2/F3 만 가능
- F1 가능성 X 시 Stage 5C primary 가설 (Δ ≤ -2.0%p) 어려울 수 있음 → 사용자 / 의사결정자 검토 필요

## 9. 산출물

- 본 scorecard: `docs/stage5a_source_scorecard_20260507.md` (1페이지 요약 + 부록)
- 사전등록 §9 산출물 표 갱신 (예정 → 완료)
- Deviation log entry: `docs/methodology_deviation_log.md` (Week 1 발견 minor)

## 10. 코덱스 자문 이력

| 차수 | 내용 |
|---|---|
| 2026-05-07 (사전 자문) | Week 1 진행 method (sample 9명 / source 우선순위 / scorecard 형식) |
| 2026-05-07 (본 결과) | Auction REJECT + Artsy CV BORDERLINE → §6.2 보류 |
| Week 2 (예정) | Artsy CV 정량 feasibility + 새 source 후보 검토 자문 |
