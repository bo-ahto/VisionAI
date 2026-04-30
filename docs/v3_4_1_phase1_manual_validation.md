# v3.4-1 Phase 1: saatchi/artsy detail page manual 검증

작성일: 2026-05-01
배경: 코덱스 v3.3-3 권장 — "현재 raw 로는 sold/listing 추정 불가, v3.4-1 에서 feasibility 부터 검증"

---

## 1. 방법

### Saatchi
- 5 sample artwork URL (가격대 다양: low / mid / high / ultra / extra_high)
- 검증 방법: `curl` raw HTML fetch + UA header → regex / Python 으로 field 추출
- 작품 URLs:
  1. https://www.saatchiart.com/art/Photography-Going-Bananas-10/920928/9784037/view (749K KRW)
  2. https://www.saatchiart.com/art/Photography-ANIMA-MUNDI/2551795/13655555/view (1.2M)
  3. https://www.saatchiart.com/art/Mixed-Media-bananas-apples-and-books-2ch-ed-1-5/1712575/8105154/view (9.5M)
  4. https://www.saatchiart.com/art/Painting-Collection/1694193/12580909/view (22.3M)
  5. https://www.saatchiart.com/art/Painting-rest-space-forest/2044725/9980579/view (6.1M)

### Artsy
- 1 sample 시도: https://www.artsy.net/artwork/yujin-ju-breath-into-bloom
- WebFetch + curl 모두 **403 Forbidden** (anti-bot 차단)

---

## 2. Saatchi 검증 결과 (5 sample 일관성 검증)

| 필드 | 노출 비율 | 추출 형식 | 비고 |
|------|---------:|----------|------|
| **`Year Created`** | **5/5 (small sample)** | `<h5>Year Created:</h5>...<p>YYYY</p>` | regex 추출 가능. 추출값: 2012, 2020, 2020, 2020, 2022. **coverage claim X — feasibility confirmed only** (코덱스 P0) |
| **`isSoldOut`** | 5/5 (100%) | JSON `"isSoldOut":false` | 현재 fetch 가 avail-only 라 모두 false. 다른 작품 fetch 시 sold 추출 가능. |
| **`isReserved`** | 5/5 (100%) | JSON `"isReserved":false` | 위와 동일 |
| **`availability` (schema.org)** | 5/5 (100%) | `"availability":"http://schema.org/InStock"` | InStock / OutOfStock 구분 |
| **`isOriginal`** | 5/5 (100%) | JSON `"isOriginal":true` | 원작/edition 구분 신호 |
| `listing_date` / `posting_date` / `created_at` / `addedAt` | **0/5 (0%)** | NOT FOUND | 페이지 어디에도 없음 |
| `view_count` | **0/5 (0%)** | NOT FOUND | `reviewCount: 9453` 은 사이트 전체 reviews (작품별 X) |
| `favorite_count` / `likes` / `saves` | **0/5 (0%)** | NOT FOUND | `"likes":0` 은 generic schema field, 의미 없음 |
| `inquiry_count` | 0/5 (0%) | NOT FOUND | - |
| 작가 join date | 0/5 (0%) | NOT FOUND | 작가 detail page 별도 확인 필요 (별 작업) |

### 핵심 발견 — Saatchi (small sample feasibility 수준)
1. **`Year Created` 5 sample 모두 검출 → feasibility confirmed** (전체 coverage claim X, 추가 stratified sample 20~30건 검증 필요 — 코덱스 P0)
2. **listing_date / view / favorite 가 detail page 에 일관되게 부재** → 코덱스 v3.3-3 우선순위 1번 (listing_date ★★★★★) 은 현 수집 경로에서 **low-feasibility**
3. **isSoldOut / isReserved 노출 가능** — 다만 이건 saatchi crawler 를 `availability=all` 로 변경해서 sold 작품도 함께 가져와야 의미 (현재 avail-only)
4. **Saatchi crawler 가 원래 Year Created 를 못 가져온 이유** = source mismatch (Constructor.io API 레이어 / inventory feed 에는 없고 detail page rendered HTML 에만 있는 field 가능성). 버그 X, 데이터 소스 한계 (코덱스 P1).

---

## 3. Artsy 검증 결과

| 필드 | 결과 |
|------|------|
| 모든 필드 | **검증 실패 (HTTP 403 Forbidden)** |

Artsy 는 anti-bot 정책으로 단순 curl/WebFetch fetch 차단. 검증 가능한 옵션:
- (a) Artsy 공식 API + 인증 (partnership 필요)
- (b) Selenium / Playwright + browser session
- (c) 별도 service / proxy

→ **Artsy listing_date / view 검증은 본 Phase 1 범위 밖**. 진행은 partnership / authenticated API 필요.

---

## 4. 결론 + 우선순위 갱신

### 4.1 Phase 1 의 결정적 finding
1. **`year_made` 보충은 Saatchi 단순 fetch 로 가능** — 21,721 row, ~2 sec/req, rate limit 고려 시 1~2일 작업
2. **`listing_date` 는 Saatchi detail page 에 없음** — 코덱스 v3.3-3 의 ★★★★★ 후보가 단순 fetch 로 불가
3. **Artsy 는 별도 partnership/API 필요** — 가까운 시일 내 진행 어려움

### 4.2 v3.4 우선순위 재평가

코덱스 v3.3-3 inventory 의 우선순위가 본 Phase 1 결과로 갱신됨:

| 후보 | v3.3-3 우선순위 | Phase 1 후 갱신 | 사유 |
|------|:---------------:|:---------------:|------|
| `listing_date` | ★★★★★ | **★★** (achievable X) | Saatchi detail page 부재, Artsy anti-bot |
| **`year_made` 보충** | ★★★★ | **★★★★★** (feasible 입증) | Saatchi 100% 안정 노출 |
| `is_sold` / `sold_ratio` | ★★ | ★★★ (위로 이동) | Saatchi `availability=all` 변경으로 가능 |
| `view_count` / `favorite_count` | ★ | ★ (변화 X) | Saatchi 노출 X |
| Artsy 외부 신호 | - | partnership 후 |
| Saatchi 작가 join date | - | ★★ | 작가 detail page 별도 확인 필요 |

### 4.3 v3.4-2 추천 (코덱스 권장 5-step pilot-first 워크플로우)

**v3.4-2: Saatchi year_made 결측 보충 + 모델 재학습 ablation** (2~3 주):
1. **추가 stratified sample 검증 20~30건** (medium/category/edition/photography/sculpture/sold/reserved 별) — `Year Created` 라벨 변형 / 예외 검증
2. **detail parser 구현** — saatchi crawler 보강 (regex + JSON `__NEXT_DATA__` fallback)
3. **pilot batch 500~1,000건 재수집** — fill rate / parse failure / latency / block rate 확인
4. **fill rate 만족 시 21,721 row 확장** — rate limit 분산 (1~2일)
5. **모델 재학습 + 3-축 ablation** (코덱스 P1):
   - 전체 성능 변화
   - cold / low-work-count cohort 변화 (catastrophic 50%+ MdAPE cohort 가 줄어드는지)
   - `has_year_made=0/1` flag 자체의 기여 분리

**중요 caveat (코덱스 P1)**: year_made 보충이 cold/저 work_count catastrophic cohort 를 줄일지는 **미검증** — strong claim 금지. vintage_premium / work_age / artist maturity proxy signal 강화 가능성은 높음.

**v3.4-3 (별도 트랙)**: Saatchi crawler `availability=all` 변경 (sold 작품 포함) — sold_ratio_per_artist signal 추가. v3.4-2 결과 보고 결정.

**Artsy partnership / API 검토** = 별도 비기술 트랙 (영업/계약 협의). 현재 스프린트 결정에 섞지 말 것 (코덱스 P2).

### 4.4 Code 변경 미리 보기 (v3.4-2 시 참고)
```python
# scripts/crawl_saatchi.py 보강 예시 (detail page fetch + year extraction)
import re

YEAR_CREATED_PATTERN = re.compile(
    r'<h5>Year Created:</h5></div><div[^>]*><p>(\d{4})</p>'
)

def fetch_year_created(artwork_url: str) -> int | None:
    """Saatchi detail page 에서 Year Created 추출 (5 sample 100% 검증)."""
    resp = http_get(artwork_url, headers=BROWSER_UA)
    m = YEAR_CREATED_PATTERN.search(resp.text)
    return int(m.group(1)) if m else None
```

---

## 5. 산출물
- `docs/v3_4_1_phase1_manual_validation.md` (본 문서)
- 다음 단계: v3.4-2 가능 (year_made 보충 작업), 또는 v3.3 close + 한 페이지 plan 정리
