# v3.4-2 step 4: saatchi 21,087 전수 enrichment 완료

작성일: 2026-05-01
배경: 코덱스 v3.4-2 step 4 권장 — 학습 데이터 saatchi 21,087 전수 enrichment + failure-only 2-pass retry.

---

## 1. 진행 (코덱스 6-step pilot-first)

| step | 내용 | 결과 |
|------|------|------|
| 1 | stratified 26건 검증 | Year Created 100% |
| 2 | parser + 18 단위 테스트 | smoke 26/26 |
| 3 | pilot 1,000건 | 99.6% fill, anti-bot 0 |
| **4** | **21,087 전수 + retry 2-pass** | **97.90% fill** ← 본 단계 |

---

## 2. 최종 결과

### 2.1 핵심 메트릭
| 메트릭 | 값 |
|--------|---:|
| n_total | 21,087 |
| **Year Created fill** | **20,644 / 21,087 = 97.90%** |
| extraction_source | `html_year_created`: 20,644 / `unresolved`: 443 |
| fetch_status | ok 20,644 / 5xx 416 / network_error 27 |
| isSoldOut: true | **5,949 (28.2%)** |
| isSoldOut: false | 14,695 (69.7%) |
| isSoldOut: missing | 443 (2.1%, 모두 fetch 실패) |
| anti-bot blocked | **0** |
| Year 분포 | min 1919, p10 2015, median 2021, p90 2025, max 2026 |

### 2.2 retry 결과 (코덱스 정책 그대로)
| pass | backoff | recovered | rate |
|------|--------:|----------:|-----:|
| pass 1 | 2-5s | **0 / 443** | 0% |
| pass 2 | 5-15s | **0 / 443** | 0% |

→ **transient 가 아니라 stable 실패군** (코덱스 P0 wording). 416 건은 5xx→5xx→5xx, 27 건은 network_error→network_error→network_error 로 고정. **artist/page cluster 단위 persistent fetch failure** 로 추정 (제거/비공개 가능성 높지만 policy 단정은 X). step 5 에서는 `has_year_made=0` 으로 처리.

### 2.3 운영 메트릭
- main pass: 4.85 hr (rate 0.88 req/s)
- retry pass 1+2: ~3.6 hr (backoff 평균 8.5s)
- 총: **약 8.5 hr** (코덱스 추정 7-8 hr 와 일관)

---

## 3. 핵심 finding

1. **97.90% fill rate 도달** — pilot 99.6% 보다 약간 낮은 이유: 21,087 전수에서 영구 5xx 가 더 많이 노출 (saatchi 측 작품 라이프사이클)
2. **fallback 사용 0** — 21,087 모두 primary regex (html_year_created) 매칭. parser drift 없음
3. **5,949 sold 검출 (28.2%)** — saatchi raw 의 avail-only 정의와 무관 (detail page 의 isSoldOut JSON 노출). v3.4-3 sold_ratio feature 의 데이터 이미 있음
4. **Year 분포 다양** (1919~2026, median 2021) — production 작품의 vintage 신호로 충분
5. **0% retry 회복** — 이번 실행 창 (2026-05-01 UTC 기준) 에서 transient 로 회복되지 않는 stable 실패군. 코덱스 P0: 443 실패가 19 artist_slug 에 집중 → "artist/page cluster persistent failure". saatchi 정책 단정은 X.

---

## 4. step 5 진행 권장 (설계 문서 6-step)

step 5 = **research ablation** ("year signal upper-bound 측정", 코덱스 권장 framing).

| step | 내용 | 상태 |
|------|------|:----:|
| 1 | step 4 완료 fill rate 확정 | ✅ |
| 2 | production feasibility 표 고정 | ⏭️ |
| 3 | 3 variant 학습 (V0 / V_year_only / V_full) | ⏭️ |
| 4 | primary = overall MdAPE, guardrail = cold / low_wc / saatchi_online | ⏭️ |
| 5 | V_year_only 무의미 → 중단 | ⏭️ |
| 6 | V_full 추가 이득 → v3.5 backlog (production scrape ops review) | ⏭️ |

### Production feasibility 표 (코덱스 step 5-2)
| Source | year_made 현재 수집? | scraper 변경 비용 | latency 영향 | feasibility |
|--------|:-------------------:|------------------:|-------------:|:-----------:|
| Saatchi | **X** (Constructor.io API 만) | detail page enrichment 추가 | +0.6-1 sec / req | **medium** (anti-bot 0) |
| Artsy | **X** (GraphQL 작가 정보만) | 별도 partnership / API | 큼 (anti-bot 강함) | **low** |

→ 본 ablation 결과 좋아도 **즉시 deploy 불가능**. v3.5 ops review 후 production scrape 변경 결정.

---

## 5. 산출물
- `scripts/saatchi_step4_full_enrich.py` — 전수 + retry 2-pass runner
- `model_test_results/v3_diagnostics/saatchi_step4_full_enrichment_raw.jsonl` — 21,087 + retry 결과 (~11MB, 21,973 rows)
- `model_test_results/v3_diagnostics/saatchi_step4_full_enrichment.json` — summary
- `docs/v3_4_2_step4_full_results.md` (본 문서)

---

## 6. 다음 단계
- step 5 ablation: merge module + 3 variant OOF + cohort 평가
- 코덱스 sanity check: 사용량 한도 초과로 5월 5일 이후 가능
- 자체 진행 후 코덱스 review 받기

본 step 4 결과 review 는 코덱스 사용량 한도 (5월 5일 14:54 KST 까지) 로 다음 사이클에 받음.
