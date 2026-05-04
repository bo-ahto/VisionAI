# Ablation: gallery_tier_v4 피처 incremental gain (2026-05-04)

## 배경

- Top30 갤러리 검수 (`data/top30_피드백.csv`) → v4 갤러리 리스트 (88+30=118건) 생성
- v3 → v4 매핑 후 Artsy 매칭률: **13.2% → 94.7%** (작품 6,902/7,289)
- B/E ratio CI [0.694, 1.122] (1 포함) — univariate 분리는 약함
- 코덱스 자문대로 게이트는 "분리도"가 아니라 **OOF MdAPE 개선**으로 판정

## 실험 설계

| 항목 | 값 |
|---|---|
| Baseline | CB_FEATURES_BASE (32) — 기존 gallery_tier 피처 포함 |
| Treated | CB_FEATURES_BASE + gallery_tier_v4 (33) |
| 모델 | CatBoost (1000 iter, depth 6, lr 0.05) |
| CV | KFold 5-fold (warm), GroupKFold 5-fold (cold start) |
| 데이터 | 28,376건 (Artsy 7,289 + Saatchi 21,087, filtered) |
| Saatchi 매핑 | 모두 Tier E (온라인 플랫폼) |

## 결과

### KFold 5-fold (warm — 같은 작가의 다른 작품)

| Subset | n | MdAPE base | MdAPE +v4 | Δ MdAPE | Δ W30 |
|---|---:|---:|---:|---:|---:|
| Overall | 28,376 | 17.82 | 17.78 | **-0.04** | -0.05 |
| Artsy | 7,289 | 16.99 | 17.49 | **+0.50** | +0.12 |
| Saatchi | 21,087 | 18.15 | 17.91 | **-0.24** | -0.11 |

### GroupKFold 5-fold (cold start — 새 작가)

| Subset | n | MdAPE base | MdAPE +v4 | Δ MdAPE | Δ W30 |
|---|---:|---:|---:|---:|---:|
| Overall | 28,376 | 40.76 | 40.08 | **-0.68** ✅ | +0.26 |
| Artsy | 7,289 | 33.35 | 32.80 | **-0.55** ✅ | +1.20 |
| Saatchi | 21,087 | 43.15 | 43.38 | +0.23 | -0.06 |

### Feature Importance (full-data CatBoost)

| Feature | Importance |
|---|---:|
| gallery_tier_v4 | **0.76** |
| gallery_tier (existing) | 0.43 |
| ratio (v4 / existing) | **1.75x** |

## 해석

### 1. Cold start 에서 일관된 개선
- Overall MdAPE: 40.76 → 40.08 (**-0.68**)
- Artsy MdAPE: 33.35 → 32.80 (**-0.55**), W30 +1.20%p
- 신규 작가에 대해 갤러리 신호가 가격 예측에 기여

### 2. Warm 에서는 mixed
- Saatchi 개선 (-0.24)
- Artsy 악화 (+0.50) — warm 작가는 작가 자체 가격 신호가 강해 갤러리 신호가 noise로 작용 가능성

### 3. Feature importance: gallery_tier_v4 > 기존 gallery_tier
- v4 (0.76) 가 기존 (0.43) 보다 1.75x — 모델이 v4를 더 강하게 사용
- 단 importance 와 OOF MdAPE 개선은 다른 측정. mixed 결과 해석에 부합

### 4. univariate 분리 약함에도 불구하고 cold start 개선
- 코덱스 자문 §2 가 옳았음: "약한 univariate 분리여도 다른 피처와의 상호작용으로 CV 성능이 좋아질 수 있다"

## 판정 (잠정)

| 항목 | 결과 |
|---|---|
| Cold start (신규 작가 라우팅) | **도입 권고** — Artsy/Overall 모두 일관된 개선 |
| Warm (기존 작가 라우팅) | **도입 보류** — Artsy 악화 (+0.50) |
| 단일 피처 도입 vs replace | 현재는 add-on. `gallery_tier`(기존 자동) 와 `gallery_tier_v4`(검수 기반) 공존 가능 |

## 권장 후속 작업

### 즉시 가능
1. **CatBoost cold-start branch에만 gallery_tier_v4 도입**
   - 서빙 라우팅 (artist_count<5) 에 한해 v4 피처 사용
   - Warm 라우팅 (XGBoost) 은 baseline 유지 → Artsy regression 회피
2. **Saatchi 매핑 재검토**
   - 현재 모두 Tier E → Saatchi 내부에서 신호 0
   - 'Saatchi'는 source 피처로 이미 식별되므로 v4를 다른 값으로 매핑할 필요는 없음

### 추가 검증 필요
3. **하이퍼파라미터 재튜닝**
   - 현재 baseline 하이퍼는 32 features 기준 — 33 features 환경에서는 재튜닝하면 warm artsy regression 해소될 수 있음
4. **292건 데이터로 외부 holdout 검증**
   - 이번 cycle 학습엔 미포함이지만, gallery_tier_v4 도입 모델의 1차 시장 일반화 능력 측정 가능
5. **본 마이그레이션 데이터 도착 후 재실행**
   - 추가 미매칭 갤러리 검수 → v5 → 동일 ablation 재측정

## 운영 도입 (별도 PR)

코덱스 자문 §2: "오프라인 ablation"과 "실배포 가능성"을 분리.
- 오프라인 OOF 결과는 cold start 도입 권고를 지지
- 실배포: `src/visionai/price_engine/api/primary_predictor.py` feature contract 변경 필요
- 본 PR 범위는 **오프라인 검증까지** — 실배포는 별도 결정/PR

## 산출물

- `data/art_gallery_tier_list_v4.csv` (118건)
- `data/gallery_alias_map.csv` (43건, 영문→한글)
- `scripts/build_gallery_tier_v4.py`
- `scripts/ablation_gallery_tier_v4.py`
- `model_test_results/ablation_gallery_tier_v4.json` (raw metrics)
- `model_test_results/gallery_tier_coverage_report.md` (v4 매칭 분석)
