# v3.4-2 step 3: pilot 1,000건 enrichment 결과

작성일: 2026-05-01
배경: 코덱스 v3.4-2 step 2 권장 hybrid sampling — 650 target cohort + 350 stratified random.

---

## 1. 방법

### 1.1 Hybrid sampling (코덱스 권장)
- **Target cohort 650**: cold artists 우선 + low work_count + price=0 + 매체 편중 방지
- **Stratified random 350**: medium × price band × artist activity bucket

### 1.2 실제 sample 분포 (1,000건)
| Target reason | n | 비고 |
|---------------|--:|------|
| cold_artist | 500 | 학습 데이터 cold 작가 작품 |
| fill_diversity | 150 | target 부족분 + 매체 다양성 |
| stratified_random | 292 | 균등 quota |
| stratified_fill | 58 | stratified 부족분 |

추가 분포:
- Medium: oil 288, acrylic 277, ink 126, other 125, watercolor 122, ...
- Price band: low 230 / mid 435 / high 225 / ultra 110
- Work count bucket: 1-2 (190), 3-4 (312), 5-9 (38), 10+ (460)
- Warm/Cold: 498/502
- Unique artists: 447

---

## 2. 결과 (model_test_results/v3_diagnostics/saatchi_pilot_enrichment.json)

### 2.1 핵심 메트릭
| 메트릭 | 값 |
|--------|---:|
| **Year Created fill** | **996/1000 (99.6%)** |
| extraction_source | `html_year_created`: 996 / `unresolved`: 4 |
| fetch_status | ok 996, 5xx 3, network_error 1 |
| isSoldOut: true | **208** (= sold 작품도 detail page 노출) |
| isSoldOut: false | 788 |
| isSoldOut: missing | 4 (모두 fetch 실패) |
| anti-bot blocked | **0** |
| price_zero_flag | 0 (학습 데이터 sample 에 price=0 부재) |
| Year 분포 | min 1998, p10 2013, median 2019, p90 2025, max 2026 |

### 2.2 Target reason 별 fill rate
| Reason | n | fill | blocked |
|--------|--:|----:|--------:|
| stratified_fill | 58 | 100.0% | 0 |
| fill_diversity | 150 | 100.0% | 0 |
| cold_artist | 500 | 99.8% | 0 |
| stratified_random | 292 | 99.0% | 0 |

### 2.3 운영 메트릭
- Rate: 0.88 req/s (network 응답 시간 포함, rate limit sleep 0.6 sec)
- Total elapsed: 1,128 sec (≈ 18.8 min)
- 추정 (21,721 행): **0.88 req/s × 21,721 ≈ 6.9 hr**

---

## 3. Close framing (코덱스 권장 wording)

> Saatchi 학습 대상 21,721 row 에 대해 전수 enrichment 진행 가능. 1,000-sample pilot 에서
> Year Created fill rate 99.6% 를 확인했으며, 미수집분은 주로 transient fetch failure
> 로 추정된다. 전수 실행 시 retry pass 를 포함하면 대부분 회복 가능할 것으로 본다.

### 3.1 결론
- **parser robustness confirmed** (1,000 sample 통과, fallback 사용 0)
- **blocking risk absent** (anti-bot 차단 0)
- **remaining risk = transient fetch reliability** (5xx 3 + network_error 1 = 0.4%)

### 3.2 Risk track 분리 (코덱스 P0)
> price=0 systematic validation 은 raw corpus (30,607) 기준 별도 pipeline-risk 항목으로
> 분리. 현재 production training population (21,087) 에서는 관측되지 않으므로
> full-population enrichment gating factor 는 아님.

→ price=0 caveat (step 1 의 26 sample 4건 발견) 는 raw corpus 측 별도 backlog.

---

## 4. Step 4 진행 권장안 (코덱스)

| 항목 | 권장 |
|------|------|
| **Cohort** | 학습 데이터 saatchi 21,087 우선 전수 (production-relevant) |
| **Run mode** | 전체 1차 수집 → 실패건만 2회 retry pass |
| **Retry 대상** | 5xx, network_error, timeout |
| **Retry 정책** | pass 1: 2-5s backoff, pass 2: 5-15s backoff |
| **Non-retry** | 404 / explicit not found |
| **Append-safe** | jsonl incremental (재시작 안전) |
| **Success criterion** | 최종 unresolved 를 residual transient bucket 으로 고정 후 step 5 진입 |

비용 추정:
- 1차 본수집: ~7 hr (21,087 × 0.6 sec rate limit)
- retry pass 1+2: ~10 min (실패건 ~80~200건 × 5-15s)
- 총 ~7-8 hr (시간대 분산 권장)

raw remainder 30,607 - 21,087 = 9,520 건 은 research only, step 5 후 결정.

---

## 5. 산출물
- `scripts/saatchi_pilot_sampler.py` — hybrid sampling
- `scripts/saatchi_pilot_enrich.py` — enrichment runner + summary
- `model_test_results/v3_diagnostics/saatchi_pilot_sample_urls.json` — 1,000 URL list
- `model_test_results/v3_diagnostics/saatchi_pilot_enrichment_raw.jsonl` — raw 결과 1,000 row (608KB)
- `model_test_results/v3_diagnostics/saatchi_pilot_enrichment.json` — summary
- `docs/v3_4_2_step3_pilot_results.md` (본 문서)

---

## 6. 5-step 진행도 갱신
- ✅ step 1: stratified 26건 검증 (코덱스 권장 wording 적용)
- ✅ step 2: parser 구현 (18 단위 테스트 + smoke 26/26)
- ✅ **step 3: pilot 1,000건 (99.6% fill)** — 본 단계 close
- ⏭️ step 4: 21,087 전수 enrichment + failure-only 2-pass retry (~7-8 hr)
- step 5: 모델 재학습 + 3축 + 2 slice ablation (D10 saatchi_online + career_age recompute)
