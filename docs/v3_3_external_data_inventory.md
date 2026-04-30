# v3.3-3 외부 데이터 사전 검토 (External Data Inventory)

작성일: 2026-05-01
배경: 코덱스 v3.3-1 v2 + v3.3-2 v2 권고 — KT 라벨 정제 / work_count 분석은 모두 즉시 재학습 우선순위 낮음. v3.3 의 본질 해결은 **외부 데이터 (listing date / view count / sale ratio) feature 도입** 으로 회귀.

본 문서는 코드 변경 없이 **inventory + 수집 비용 추정 + leverage 가설** 만 정리. 실제 scraper 변경 / 모델 재학습은 v3.4 backlog.

---

## 1. 현재 보유 데이터 inventory (28,376 행, 65 컬럼)

### 1.1 시간 관련 signal (이미 보유)
| 컬럼 | dtype | non-null | 비고 |
|------|-------|---------:|------|
| `year_made` | float64 | 7,231 (25.5%) | 작품 제작년도 — **결측 다수** |
| `artist_birth_year` | float64 | 7,840 (27.6%) | 작가 출생년도 — **결측 다수** |
| `work_age` | float64 | full | year_made 또는 default 기반 |
| `career_age` | float64 | full | artist_birth_year 기반 |
| `vintage_premium` | float64 | full | 제작년도 cohort 의 가격 프리미엄 |
| `freshness_discount` | float64 | 28,313 | 신작 할인 |

### 1.2 engagement / authority signal (이미 보유)
| 컬럼 | dtype | 의미 | 비고 |
|------|-------|------|------|
| `ln_followers` | float64 | 작가 팔로워 수 (log) | full |
| `for_sale_ratio` | float64 | 판매중 / 전체 작품 비율 | full. **Saatchi 는 avail-only 수집이라 1.0 하드코딩** (코덱스 P1) |
| `request_ratio` | float64 | 작가별 "Price on request" 비율 (Artsy 만) | `prepare_primary_market_dataset.py:270` |
| `solo_count`, `group_count`, `fair_count` | int | 전시 횟수 | full |
| `gallery_city_count` | int | 작가가 노출된 갤러리 도시 수 | full |
| `gallery_tier` | category | 갤러리 등급 | full |
| `profile_completeness` | float64 | 작가 프로필 완성도 | full |
| `artist_total_works` | int | 작가 등록 작품 수 | full |

### 1.3 누락된 외부 신호 (수집 필요)
- **`listing_date`** (작품 등록 날짜): saatchi/artsy detail page 에 있을 가능성 — **현재 raw JSON 에 없음**
- **`view_count` / `impressions`**: saatchi 일부 노출 가능, artsy 비공개
- **`is_sold` / `sold_date`**: **현재 saatchi raw 자체가 avail-only** (`crawl_saatchi.py:22` 의 `original_availability_status=avail`) — sold prevalence 추정 불가. URL 'SOLD' 275 (30,607 중) 는 작품 제목 등 slug artifact (코덱스 P0).
- **`inquiry_count` / `favorite_count`**: saatchi/artsy 일부 노출
- **`days_listed`**: listing_date 기반 derived feature
- **price history / variant**: 작품 별 가격 변동 — 거의 비공개

### 1.4 갤러리 단위 신호 (이미 부분 보유)
- `gallery_tier`, `gallery_city_count`, `has_seoul`, `has_international` — 보유
- 갤러리별 sold ratio / 거래량 — **누락**

---

## 2. 수집 가능성 평가 (saatchi / artsy 별)

### 2.1 Saatchi
- Artwork detail page 가 detail JSON / HTML 노출
- 검토 필요: page HTML 에 다음 노출 여부:
  - **listing date / created_at** — 가능성 ★★★★ (대부분 아트마켓 platform 노출)
  - **view count** — 가능성 ★★ (saatchi 정책상 일부 노출, 작품마다 다름)
  - **sold status (current)** — 가능성 ★★★★★ (URL / page badge 명시)
  - **inquiry count** — 가능성 ★★ (작가에게만 노출 가능)
  - **favorite count** — 가능성 ★★★ (page UI 노출)
- 작품 수: saatchi 부분 (한국 작가 21,721) — fetch 가능
- 비용 추정: 21,721 행 × ~3 sec/req = ~18 시간 (rate limit 고려 안 함). 분산 + retry 시 1~2 일.

### 2.2 Artsy
- API / JSON 노출 적음, view count 비공개
- 가능성: listing date (★★★), sold status (★★★), view count (★)
- 작품 수: 7,640 — fetch 가능, 단 anti-bot 강함

### 2.3 KAP / printbakery (한국 갤러리)
- raw 데이터 적음, listing date 무. 우선 검토 외.

---

## 3. High-leverage feature 후보 (가설 + 우선순위)

코덱스 v3.3-1 v2 + v3.3-2 v2 발견 conditional:
- warm path 는 정상 (v3.3-1: MdAPE 7.5% / conformal 90.1%)
- cold + 저 work_count 작가 cohort 가 catastrophic (KT cold n=8 MdAPE 54.7%)
- v3.0 보고서 1.7: D10 saatchi 구조적 over-prediction (n=1,499)

### 3.1 후보 1: `listing_date` + `days_listed` (가장 high-leverage)
- **가설**: 오랜 기간 등록된 작품 = 시장 거부 신호. 가격 over-listing 가능.
- **leverage**: D10 saatchi over-prediction 의 일부 = high-priced + long-listed 작품
- **수집 비용**: saatchi 21,721 fetch (~18 시간), artsy 7,640 (~10 시간)
- **위험**: scraper 변경 필요, page HTML schema 변동 가능
- **우선순위**: ★★★★★ (가장 high-leverage)

### 3.2 후보 2: `is_sold_current` + `sold_ratio_per_artist` (low-leverage)
- **가설**: 작가별 판매율 / 작품별 sold 여부 = 시장 수요 신호
- **leverage**: 'for_sale_ratio' 이미 보유. **Saatchi 가 avail-only 수집이라 sold_ratio 는 incremental 이 아니라 새 데이터셋 수준** (코덱스 P1). `crawl_saatchi.py` 에서 `availability=all` 로 변경 + sold 작품 별도 fetch + 작가 단위 ratio 재계산.
- **수집 비용**: saatchi crawler 재설계 + sold 작품 추가 fetch (작가 단위 sold 분포 알 수 없으나 avail 21,721 의 1.5~3배 추정) + 가격 데이터 검증 (sold 가격은 noise 가능)
- **위험**: 새 데이터셋 학습 + 평가 사이클 비용
- **우선순위**: ★★ (한 단계 하향)

### 3.3 후보 3: `view_count` (low-leverage if 일부만 노출)
- **가설**: page view 수 = popularity signal → 가격 검증
- **leverage**: 작가 팔로워 (ln_followers) 와 강하게 상관 → incremental 가치 작음
- **수집 비용**: saatchi 페이지 마다 다름, 노출 여부 sample 검증 필요
- **위험**: 결측 다수 가능
- **우선순위**: ★ (검증 후 결정)

### 3.4 후보 4: `gallery_sold_volume` (low-leverage)
- **가설**: 갤러리 별 거래량 = gallery_tier 의 정량화
- **leverage**: gallery_tier 이미 보유 — incremental 작음
- **수집 비용**: 갤러리 외부 데이터 (KAP API 등) — 구조화 데이터 X
- **우선순위**: ★ (보류)

### 3.5 후보 5: `year_made` 결측 — detail/artist page 기반 추가 수집 가능성 검증 (코덱스 P1 wording 정정)
- **현재**: 7,231 / 28,376 (25.5%) 만 있음 → 결측 75% (Saatchi 파이프라인이 명시적 NaN 설정 — `prepare_saatchi_dataset.py:290`)
- **결측 = 임의 결측 X, source 구조 결측** (코덱스 P0). 내부 raw 만으로는 보충 거의 불가.
- **leverage**: vintage_premium / work_age signal 강화. cold 작가 prediction 에 큰 영향 가능.
- **수집 비용**: saatchi detail page 재크롤 (year_made 노출 여부 sample 검증 필요). artsy 는 별도.
- **위험**: 일부 작품 year 데이터 자체 부재 (작가 미기재)
- **추가 caveat (코덱스 P2)**: `year_made` 결측 자체가 신호일 수 있음 (Saatchi/Artsy source proxy 또는 비공개 작가 proxy). 보충 후에도 `has_year_made` flag 별도 유지 권장.
- **우선순위**: ★★★★ (high-leverage, 단 detail page 수집 가능성 검증 후 결정)

---

## 4. 권장 진행 순서 (v3.4 backlog)

### Phase 1: scraper 검증 (1~2 일)
1. saatchi 페이지 sample 10개 manual 확인 — listing_date / sold badge / view count / favorite 노출 여부
2. artsy 페이지 sample 10개 확인 — 동일
3. 비용 정확 추정 (rate limit 포함)

### Phase 2: 가장 high-leverage feature 1개 수집 + ablation (1~2 주)
- `listing_date` 우선 (Phase 1 검증 통과 시)
- 또는 `year_made` 결측 보충 (외부 fetch 없이 내부 데이터로 채우기 가능 시)

### Phase 3: feature 추가 후 모델 재학습 + paired comparison (1 주)
- v3.3-3 ablation: with vs without 새 feature
- target metric: cold + 저 work_count cohort MdAPE

### Phase 4: 추가 feature (Phase 2~3 결과 보고 결정)
- sold ratio / view count 등 incremental 가치 평가

---

## 5. 결론 + 다음 단계 (코덱스 v3.3-3 close framing)

**현재 단계 결론** (코덱스 권장 wording):
> **현재 raw 데이터로는 sold/listing 추정 불가**. Saatchi crawler 가 `availability=avail` 만 fetch 하므로 sold prevalence 자체를 알 수 없음. year_made 75% 결측도 source 구조 결측 (Saatchi 파이프라인이 명시적 NaN 설정). 따라서 **v3.4-1 에서 feasibility 부터 검증**.

**다음 단계 (P1 권장)**:
1. **v3.4-1 Phase 1 manual 검증** (1~2일, 가장 적절):
   - saatchi/artsy 페이지 sample 10개 visit
   - listing_date / view count / favorite / year_made 노출 여부 + 안정성 확인
   - 가장 큰 불확실성 = "수집 가능성"이므로 leverage 가설보다 우선 검증
2. **fallback: year_made 보충 검증** (Phase 1 결과 listing_date 부재/불안정 시 즉시 이어):
   - detail/artist page 기반 year_made 추가 수집 가능성 검증
   - 코덱스 P2: 보충 후에도 `has_year_made` flag 별도 유지

**Phase 1 결과 후 결정**:
- listing_date 안정 노출 → Phase 2 listing_date 수집 + ablation
- listing_date 불안정 → year_made 보충 우선
- 둘 다 어려움 → v3.3 close + 다른 방향 (모델 측 변경 / quantile regression / segment-specific model)

**산출물**:
- `docs/v3_3_external_data_inventory.md` (본 문서)
- 후속 v3.4 backlog 항목으로 `docs/primary_market_pricing_plan_v3.md` 갱신 검토 (별도 작업)
