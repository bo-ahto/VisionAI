# data/ MANIFEST

> **목적**: 두 가격 예측 모델(A: 1차 시장 / B: 경매 낙찰가)의 데이터 경계를 명시한다.
> **방식**: 비파괴 — 파일명/위치 그대로, 라벨만 부여한다.
> **작성**: 2026-04-27 (codex 검증 통과 / commit 21406fa 모델 경계 기준)

## 모델 정의

| 코드 | 모델 | 상태 | 학습 데이터 |
|---|---|---|---|
| **A** | 1차 시장 (primary, 갤러리 가격) | 배포 중 | Artsy 7,551 + Artue 2,756 = 10,307건 |
| **B** | 경매 낙찰가 (auction) | 잠정 중단 | k-artmarket 99,593건 |

**배포 코드 경로**:
- A: `prepare_primary_market_dataset.py` → `predict_primary_market.py` → `primary_server.py` / `primary_predictor.py` / `primary_feature_builder.py`
- B: `cleanse_artmarket.py` → `train_phase5_final.py` → `api/server.py` / `estimate_generator/*` / `medium_parser.py`

## 컬럼 정의

| 컬럼 | 값 |
|---|---|
| `for` | `primary` / `auction` / `—` (양 모델에 직접 입력 아님) |
| `owner` | `A` / `B` / `—` |
| `stage` | `raw` (원본 크롤) / `seed` (수집기 입력) / `intermediate` (중간 산출) / `training` (학습 입력) / `serving` (서빙 입력) / `eval` (평가) / `manual` (수기 작업본·룩업) / `archived` (사용처 없음) / `meta` |
| `active` | 코드에서 read되는가 |

---

## 신규 파일 prefix 규칙

향후 추가되는 파일은 다음 prefix를 우선한다:
- `auction_*` — B 모델 입력
- `primary_*` — A 모델 입력
- `raw_*` — 원본 크롤
- `seed_*` — collector 입력
- `eval_*` — 평가/골든셋
- `deprecated_*` — archive 예정

---

## A. 1차 시장 (primary, owner=A)

| path | stage | active | produced_by | consumed_by | notes |
|---|---|:---:|---|---|---|
| `artsy_kr_artworks.json` | training | ✓ | github.com/JRVector9/artsy-crawler/crawl_artsy_complete.py | scripts/prepare_primary_market_dataset.py | A 핵심 입력 |
| `artsy_kr_artist_shows.json` | training | ✓ | github.com/JRVector9/artsy-crawler/crawl_artsy_complete.py | scripts/prepare_primary_market_dataset.py | A 전시 피처 |
| `saatchi_kr_artists.json` | raw | ✓ | github.com/JRVector9/saatchi-crawler/crawl_saatchi.py | scripts/prepare_saatchi_dataset.py | Saatchi seed |
| `saatchi_kr_artworks.json` | raw | ✓ | github.com/JRVector9/saatchi-crawler/crawl_saatchi.py | scripts/prepare_saatchi_dataset.py | A 보조 학습 |
| `saatchi_kr_artworks.csv` | intermediate | ✓ | github.com/JRVector9/saatchi-crawler/crawl_saatchi.py | (csv 형식, 추가 다운스트림 없음) | |
| `saatchi_cleaned.csv` | intermediate | ✓ | scripts/prepare_saatchi_dataset.py | (parquet 형식이 메인) | |
| `saatchi_cleaned.parquet` | serving | ✓ | scripts/prepare_saatchi_dataset.py | src/visionai/price_engine/api/primary_server.py | A 서빙 시 read |
| `primary_market_dataset.csv` | intermediate | ✓ | scripts/prepare_primary_market_dataset.py | (parquet 형식이 메인) | |
| `primary_market_dataset.parquet` | training/serving | ✓ | scripts/prepare_primary_market_dataset.py, prepare_saatchi_dataset.py | scripts/prepare_saatchi_dataset.py, src/visionai/price_engine/api/primary_server.py | A 학습+서빙 입력 |
| `primary_market_predictions.csv` | eval | ✓ | scripts/predict_primary_market.py | (수기 검토용) | A 예측 산출 |
| `1차 시장 데이터 - 1차시장(경매x, 갤러리판매금액) 작업본.csv` | manual | ✗ | (수기) | (수기) | 1차 시장 작업본, 코드 미사용 |
| `primary_market_gap_analysis.csv` | archived | ✗ | (과거 분석 산출) | (none) | 분석 결과물 |
| `saatchi_integrated_predictions.csv` | archived | ✗ | (과거 산출) | (none) | |
| `saatchi_predictions.csv` | archived | ✗ | (과거 산출) | (none) | |
| `saatchi_predictions.parquet` | archived | ✗ | (과거 산출) | (none) | |
| `saatchi_new_artist_ids.json` | archived | ✗ | (과거 산출) | (none) | |
| `artue - 테스트가격x.csv` | archived | ✗ | (수기) | (none) | |
| `artue_테스트_가격포함.csv` | archived | ✗ | (수기) | (none) | |
| `artue_final_predictions.csv` | archived | ✗ | (과거 산출) | (none) | |
| `artue_prediction_comparison.csv` | archived | ✗ | (과거 산출) | (none) | |
| `artue_price_predictions.csv` | archived | ✗ | (과거 산출) | (none) | |

> **주의**: `artue_*`는 A의 실서비스 평가용으로 작성됐지만 현재 코드에서 read되지 않는다. 학습 입력 아님. A 모델 보고서 (`docs/primary_market_final_report.md:4`)에서 "Artue 2,756건"은 **과거 학습에 포함된 데이터**이며 현재 파일은 archived.

---

## B. 경매 낙찰가 (auction, owner=B)

| path | stage | active | produced_by | consumed_by | notes |
|---|---|:---:|---|---|---|
| `k-artmarket 1차 데이터 정제 - k_artmarket_works_updated_s3.csv` | raw | ✓ | (외부 크롤·수기 정제) | scripts/cleanse_artmarket.py, extract_clip_embeddings.py, extract_image_embeddings.py | B 원본 입력 (99,593건) |
| `k-artmarket 1차 데이터 정제 - k_artmarket_works.csv` | archived | ✗ | (구버전) | (none) | s3 버전이 후속 |
| `k-artmarket 1차 데이터 정제 - 지지체(바탕재) 분류.csv` | training | ✗ | (수기) | (Step 0 작업 예정) | **신규 분류 시트 36행, 곧 medium_parser에 반영** |
| `k-artmarket 1차 데이터 정제 - 도구_기법 분류.csv` | training | ✗ | (수기) | (Step 0 작업 예정) | **신규 분류 시트 108행, 곧 medium_parser에 반영** |
| `k-artmarket 1차 데이터 정제 - 실험데이터분류(데이터 수정).csv` | training | ✗ | (수기) | (Step 0 작업 예정) | **6,056 unique 재료 문자열, 분류 미매칭/학습 제외 라벨링** |
| `k-artmarket-cleansed.csv` | intermediate | ✓ | scripts/cleanse_artmarket.py | (known 버전이 학습용) | B 클렌징 산출 |
| `k-artmarket-cleansed-known.csv` | training | ✓ | (cleanse + 작가 known 필터) | scripts/train_phase5_final.py, extract_clip_embeddings.py, extract_image_embeddings.py | B 학습 입력 |
| `preprocessed_features.parquet` | training/serving | ✓ | (전처리 산출) | scripts/check_gate.py, experiment_*.py, generate_predictions.py, run_pipeline.py, run_shadow.py, train_model.py, validate_model.py, src/visionai/price_engine/api/server.py | B 모델 핵심 피처 |
| `macro_session.csv` | training | ✓ | scripts/collectors/collect_macro_data.py | scripts/train_phase5_*.py (5개), src/visionai/price_engine/features/macro_indicators.py, tests/price_engine/test_gate_report.py | B 거시경제 피처 |
| `clip_embeddings.npy` | intermediate | ✓ | scripts/extract_clip_embeddings.py | (pca 형식이 학습용) | |
| `clip_embeddings_index.csv` | training | ✓ | scripts/extract_clip_embeddings.py | scripts/train_phase5_final.py | |
| `clip_embeddings_pca.npy` | training | ✓ | (pca 변환) | scripts/train_phase5_final.py | |
| `image_embeddings_raw.npy` | intermediate | ✓ | scripts/extract_image_embeddings.py | (pca 형식이 학습용) | 428MB |
| `image_embeddings_index.csv` | training | ✓ | scripts/extract_image_embeddings.py | scripts/train_phase5_final.py | |
| `image_embeddings_pca128.npy` | archived | ✗ | (구 PCA) | (none) | 27MB, 이전 PCA 차원 |
| `image_embeddings_pca32.npy.bak` | archived | ✗ | (백업) | (none) | |
| `artist_profiles.csv` | training | ✓ | Crawler/KADA/crawl_kada.py, Crawler/KAP/crawl_kap.py, Crawler/Wikipedia/* (enwiki/kowiki), scripts/collectors/integrate_external* | scripts/train_phase5_with_profiles.py, src/visionai/price_engine/estimate_generator/hedonic_features.py | B 작가 메타 join |
| `artsy_artist_profiles.csv` | training | ✓ | github.com/JRVector9/artsy-crawler/collect_artsy_profiles.py | scripts/train_phase5_with_profiles.py | B 학습용 (이름은 artsy지만 reader는 B) |
| `artsy_global_stats.csv` | training | ✓ | (수기·외부 산출) | src/visionai/price_engine/features/hedonic_stats.py | B 헤도닉 글로벌 통계 |
| `ho_size.md` | training | ✓ | (수기 룩업) | scripts/cleanse_artmarket.py | 호수↔사이즈 룩업 |
| `shadow_logs/` | eval | ✓ | scripts/run_shadow.py, src/visionai/price_engine/experiments/shadow_recorder.py | shadow_scorer.py, run_shadow.py, tests/price_engine/test_shadow.py | B shadow 실험 로그 |
| `k-auction-works-20260325.csv` | training | ✓ | (외부 데이터) | scripts/run_pipeline.py, train_estimate_models.py, train_phase5_*.py (4개), train_v2_engine.py, diagnose_gap.py, merge_artmarket_data.py, scripts/collectors/* (5개) | B 학습 + collector seed (양쪽 사용) |
| `kada_artist_profiles_unique.csv` | seed | ✓ | (외부) | Crawler/Kartmarket/crawl_kartmarket_prices.py | B 크롤러 입력 |
| `난트기준_재료분류.csv` | manual | ✗ | (수기) | (medium_parser 룰의 참조 문서) | 구 분류 매트릭스 96행 |
| `크롤링_난트매핑.csv` | manual | ✗ | (수기) | (medium_parser 룰의 참조 문서) | 6,057 원본 → 정규화 사전 |
| `material_mapping_table.csv` | archived | ✗ | (수기) | (none) | 신규 분류 시트로 대체됨 |
| `k-auction-works-merged.csv` | archived | ✗ | scripts/merge_artmarket_data.py | (none) | merge 산출, 이후 read 없음 |
| `k-auction-artists-20260325.csv` | archived | ✗ | (외부) | (none) | works만 사용 중 |
| `kartmarket_auction_prices.csv` | archived | ✗ | Crawler/Kartmarket/crawl_kartmarket_prices.py | (none) | crawler 산출, 후속 read 없음 |
| `kartmarket_auction_prices.json` | archived | ✗ | Crawler/Kartmarket/crawl_kartmarket_prices.py | (none) | ⚠ `merge_artist_data.py`는 `kada_kartmarket_prices.json`을 읽음 — **이름 체인 단절** |
| `kada_artist_auction_prices.csv` | archived | ✗ | (외부) | (none) | |
| `kada_artist_auction_prices.json` | archived | ✗ | (외부) | (none) | |
| `kada_artist_profiles.csv` | archived | ✗ | Crawler/KADA/crawl_kada.py | (none) | |
| `kada_artist_profiles.json` | archived | ✗ | Crawler/KADA/crawl_kada.py | (none) | |
| `kada_artists_korean.json` | manual | ✓ | (외부) | scripts/merge_artist_data.py | manual integration input |
| `kada_artsy_cv.json` | manual | ✓ | (외부) | scripts/merge_artist_data.py | manual integration input |
| `kada_kartmarket_prices.json` | manual | ✓ | (외부, ⚠ crawler 출력 이름과 다름) | scripts/merge_artist_data.py | manual integration input |
| `kada_integrated_dataset.json` | manual | ✓ | scripts/merge_artist_data.py | scripts/merge_artist_data.py (output-only로 보임) | merge 결과물 |
| `kartmarket_artists_for_artsy.json` | archived | ✗ | (수기) | (none) | 매핑 보조, 코드 미사용 |
| `kap_artist_profiles.csv` | archived | ✗ | Crawler/KAP/crawl_kap.py | (none) | |
| `kap_artist_profiles.json` | manual | ✓ | Crawler/KAP/crawl_kap.py | scripts/merge_artist_data.py | manual integration |

---

## C. 미분류 / 수집기 전용 (for=—)

수집기(crawl/scrape)에서만 read/write되며 두 모델 어느 쪽에도 직접 학습 입력으로 들어가지 않는다.

| path | stage | active | produced_by | consumed_by | notes |
|---|---|:---:|---|---|---|
| `artist_slug_mapping.csv` | seed | ✓ | (수기) | github.com/JRVector9/artsy-crawler/expand_artsy_mapping.py | crawler 입력 매핑 |
| `artist_slug_mapping_expanded.csv` | seed | ✓ | github.com/JRVector9/artsy-crawler/expand_artsy_mapping.py, expand_artsy_english.py | github.com/JRVector9/artsy-crawler/collect_artsy_profiles.py, scrape_artsy_expanded.py | crawler 확장 매핑 |
| `artsy_auctions.csv` | intermediate | ✓ | github.com/JRVector9/artsy-crawler/scrape_artsy_auctions.py, scrape_artsy_expanded.py | (none) | crawler 산출, 후속 없음 |
| `artsy_auctions_test.csv` | archived | ✗ | github.com/JRVector9/artsy-crawler/test_scrape.py | (none) | 테스트 픽스처 |
| `artsy_korean_artists.json` | intermediate | ✗ | github.com/JRVector9/artsy-crawler/crawl_artsy_graphql.py | (none) | 구 크롤 (kr_* 가 후속) |
| `artsy_korean_artworks.json` | intermediate | ✗ | github.com/JRVector9/artsy-crawler/crawl_artsy_graphql.py | (none) | 구 크롤 |
| `artsy_korean_artist_shows.json` | intermediate | ✗ | github.com/JRVector9/artsy-crawler/crawl_artsy_graphql.py | (none) | 구 크롤 |
| `artsy_kr_artists.json` | intermediate | ✗ | github.com/JRVector9/artsy-crawler/crawl_artsy_complete.py, crawl_artsy_full.py | (none) | shows/artworks가 후속 read |
| `artsy_kr_artists_full.csv` | intermediate | ✗ | github.com/JRVector9/artsy-crawler/crawl_artsy_complete.py, crawl_artsy_full.py | (none) | |
| `artsy_kr_artists_full.json` | intermediate | ✗ | github.com/JRVector9/artsy-crawler/crawl_artsy_complete.py, crawl_artsy_full.py | (none) | |
| `artsy_kr_artworks.csv` | intermediate | ✗ | github.com/JRVector9/artsy-crawler/crawl_artsy_complete.py, crawl_artsy_full.py | (none) | json이 후속 read |
| `artsy_new_mappings.csv` | intermediate | ✗ | github.com/JRVector9/artsy-crawler/expand_artsy_mapping.py | (none) | |
| `artsy_new_profiles.csv` | intermediate | ✗ | github.com/JRVector9/artsy-crawler/scrape_artsy_profiles_bulk.py | (none) | |
| `artsy_scrape_targets.csv` | seed | ✓ | (수기) | github.com/JRVector9/artsy-crawler/scrape_artsy_expanded.py | crawler 타겟 |
| `enwiki_profiles.csv` | intermediate | ✓ | Crawler/Wikipedia/scrape_enwiki_profiles.py | (artist_profiles 통합 경유) | |
| `kowiki_profiles.csv` | intermediate | ✓ | Crawler/Wikipedia/scrape_kowiki_profiles.py | (artist_profiles 통합 경유) | |
| `wikidata_korean_artists.csv` | archived | ✗ | (외부) | (none) | |
| `ecos_macro.csv` | intermediate | ✗ | (제거됨 — 구 collect_ecos_data.py) | (macro_session이 후속) | |
| `macro_monthly.csv` | intermediate | ✗ | scripts/collectors/collect_macro_data.py | (macro_session이 후속) | |
| `merged_artist_profiles.csv` | archived | ✗ | (구 산출) | (none) | |
| `merged_artist_profiles.json` | archived | ✗ | (구 산출) | (none) | |
| `artists_missing_birthyear.csv` | archived | ✗ | (수기) | (none) | |
| `artsy_artist_cv.csv` | archived | ✗ | (구 산출) | (none) | |
| `artsy_artist_cv.json` | archived | ✗ | (구 산출) | (none) | |
| `experiment_artists_with_prices.csv` | archived | ✗ | (구 실험) | (none) | |
| `experiment_artists_with_prices.json` | archived | ✗ | (구 실험) | (none) | |

---

## D. 골든셋 (eval, 사용 보류)

| path | stage | active | notes |
|---|---|:---:|---|
| `골든셋.xlsx` | archived | ✗ | 코드 read 없음 |
| `골든셋_프린트.xlsx - 시트 1 - printbakery_cate367_deta.csv` | archived | ✗ | printbakery 기반 |
| `미술품 가격 예측 AI 골든셋(가격포함).xlsx` | archived | ✗ | |
| `미술품 가격 예측 AI 골든셋(정답 제거 2) - (1차 작업) 미술품 가격 예측 AI 골든셋 템플릿의 사본의 사본.csv` | archived | ✗ | |
| `golden_set_comparison.csv` | archived | ✗ | |
| `golden_set_holdout_test.csv` | archived | ✗ | |
| `golden_set_insample_test.csv` | archived | ✗ | |
| `golden_set_predictions.csv` | archived | ✗ | |
| `printbakery_predictions.csv` | archived | ✗ | 코드 read 없음 |
| `printbakery_predictions.parquet` | archived | ✗ | |
| `printbakery_predictions_v2.csv` | archived | ✗ | |
| `printbakery_predictions_v2.parquet` | archived | ✗ | |
| `1차 - 테스트가격x.csv` | archived | ✗ | 1차 시장 테스트 픽스처 후보 |

> 골든셋·printbakery는 1차 시장(A) 평가용으로 작성됐으나 현재 코드에서 read되지 않는다. 평가 파이프라인 복원 시 owner=A로 승격 필요.

---

## E. 메타

| path | stage | notes |
|---|---|---|
| `VERSION` | meta | works/artists 데이터 SHA + 생성일 (2026-03-26 기준) |

---

## 알려진 문제

1. **`kartmarket_auction_prices.json` ↔ `kada_kartmarket_prices.json` 이름 체인 단절**
   - `Crawler/Kartmarket/crawl_kartmarket_prices.py:192-203`은 `kartmarket_auction_prices.json` 작성
   - `merge_artist_data.py:28`은 `kada_kartmarket_prices.json` read
   - 두 파일은 **다른 파일** — manual integration이 의도된 동작인지 확인 필요

2. **artsy/artue 파일명이 모델 소속을 보장하지 않는다**
   - `artsy_artist_profiles.csv`, `artsy_global_stats.csv`는 B(경매) 학습 입력
   - `artsy_kr_artworks.json`, `artsy_kr_artist_shows.json`만 A(1차 시장) 학습 입력

3. **archived 49개 파일** — 5GB+의 차지. 별 PR로 `data/_archive/` 이동 검토 가능 (현재 PR 범위 외).

4. **신규 분류 시트 3개 (지지체/도구/실험데이터)** — 현재 코드에 reader 없음. Step 0 작업으로 `medium_parser.py`에 반영 예정.

5. **artsy-crawler 저장소 정리 (2026-07-06)** — `crawl_artsy_complete.py`(당시 구버전/중복), `crawl_artsy_graphql.py`(구 크롤), `collect_artsy.py`, `collect_artsy_profiles.py`, `scrape_artsy_profiles_bulk.py`, `expand_artsy_english.py`, `expand_artsy_mapping.py`, `scrape_artsy_auctions.py`, `scrape_artsy_expanded.py`, `test_scrape.py` 9종을 제거하고 `crawl_artsy_full.py`만 유지. 위 표에서 이 스크립트들을 produced_by로 참조하는 행(주로 archived/intermediate ✗)은 **데이터 계보 기록으로만 남아있으며 해당 스크립트는 더 이상 존재하지 않는다.**

6. **ECOS 크롤러 제거 (2026-07-06)** — `collect_ecos_data.py` 삭제. 산출물(`ecos_macro.csv`, `macro_monthly.csv`)이 이미 intermediate ✗(비활성)였고, 실제 학습용 매크로 피처(`macro_session.csv`)는 `collect_macro_data.py`(로컬 K-Auction 통계 기반, ECOS 미의존)에서 생성되어 영향 없음.

7. **artsy-crawler: crawl_artsy_full.py → crawl_artsy_complete.py 재교체 (2026-07-06)** — 병렬 작업 사본(VisionAI2)에서 2026-06-23에 증분 수집 기능(`--baseline-csv`, `--full-refresh`, 기존 artwork_id 스킵)이 추가된 `crawl_artsy_complete.py`를 발견, 5번 항목에서 제거했던 `crawl_artsy_full.py`를 이 버전으로 교체. 출력 파일(`artsy_kr_artworks.json`, `artsy_kr_artist_shows.json` 등)은 동일하게 유지되어 핵심 입력에 영향 없음. 현재 artsy-crawler에는 `crawl_artsy_complete.py` 1개만 존재.
