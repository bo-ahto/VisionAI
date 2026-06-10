# Cold 가격 예측 트랙 최종 보고서

- 작성일: 2026-06-10 (최종판 — 실험 17건 + artifact 5종 전체 반영)
- 범위: Cold(train에 작가 이력이 없는 작품) 가격 예측 — 로드맵 수립, 전 경로 실험, 운영 동결, 수집 파일럿까지
- 지표 표기: MdAPE / MAPE / p95_APE. 평가: validation cold 2,753행(작가 172) / fixed test cold 3,099행(작가 200)
- 대원칙: 0604는 Warm 시험 제출 전용(전면 사용 금지) / test 후보 선택 금지(최종 1회) / 실험별 전용 폴더 + 단일 재현 스크립트

## 1. 요약

하루에 Cold 개선의 전 경로(보정층·콘텐츠 신호·base 피처·tier 확장·모델 조합·base 학습·수집 확대)를 17개 실험으로 전수 검증했다. **최종 서빙 체계 = v0.3(점 예측) + v0.4(신뢰도/검수 정책, 미커버 상수 fallback 활성) + v0.5(raw-input p95 방어 blend)** 이며, 현재 보유 데이터와 현행 보정 공식 기준으로 열린 개선 경로는 0건이다(수집 확대도 파일럿에서 ROI 없음 확인). 재시도 조건은 "실제 cold 운영 트래픽의 잔차 확보 시"로 명시했다.

| 최종 모델 | 환경 | test 성능 |
|---|---|---|
| **v0.3 체인** (점 예측 최고) | 검색 스냅샷 가용 | **0.4098 / 0.8493 / 2.3465** |
| v0.5 blend (p95 방어) | raw-input 전용 | 0.4822 / 1.1790 / 3.6490 |
| v0.2 (참조 기준) | raw-input 전용 | 0.4852 / 1.1771 / 4.1223 |

## 2. 최고 성능 모델 상세 — v0.3 체인의 피처와 보정 로직

v0.3은 단일 모델이 아니라 **"상류 Quantile 모델 + 3단 보정"** 체인이다. 각 층이 서로 다른 오차 원인을 직교적으로 방어한다(PP-COLD-DEFENSE1에서 가산성 검증, redundancy gap ≈ 0).

### 2.1 상류 모델 — LightGBM Quantile (PP-Y18 계열)

- **피처 3축**: ① 작품 기본(width/height/depth_cm, area_cm2, log_area, aspect_ratio, has_depth, is_3d_candidate, medium/support_category, size/support_size_bucket) ② 작가 메타(생년, 팔로워, 총작품수 등 — 외부 출처라 cold 작가도 보유 가능) ③ **검색 피처(search_all) + 외부 상호작용**: 작가 검색 결과수, 소스군(gallery_museum/market/news/social 등) 비율, 미술 맥락 카운트와 그 상호작용 — Cold에서 가장 강한 외부 신호.
- 분위수 4개(q10/q40/q50/q90)를 각각 학습. **대표 점 예측 = q50**, `quantile_width = q90 − q10`이 행 단위 불확실성 신호가 된다.
- 검색 피처 유무의 가치: search-free 변형(v0.2)은 0.4852로, 검색 포함 체인(0.4098) 대비 MdAPE +0.075 — 검색 신호가 Cold base에서 가장 큰 단일 기여.

### 2.2 1차 보정 — qwidth 구간 OOF median 보정 (PP-Y18, `qwidth_bin_oof_min30_cap0.25`)

```
보정값(행) = clip( median( validation OOF 잔차 | qwidth bin(행) ), ±0.25 )   (bin 표본 ≥ 30)
대표' = q50 예측 + 보정값
```
- **로직**: 불확실성 폭(qwidth)이 큰 구간은 잔차가 0이 아니라 계통적으로 치우친다(주로 과소예측). 구간별 잔차 *중앙값*만 OOF로 학습해 가산 — 개별 행이 아닌 구간 단위라 과적합 위험이 낮다.
- 효과: PP-Y2 기준 0.4421/1.048/3.354 → **0.4247/0.991/3.305**. (artist holdout 반복검증 통과, PP-Y21)

### 2.3 2차 방어 — guard (PP-QR4, 과대예측 하향 블렌드)

```
발동조건: qwidth ≥ 1.4612 (val q67)  AND  (대표' − q40) ≥ 0.0772 (val q50)  AND  q40 < 대표'
발동 시:  대표'' = 0.5 × 대표' + 0.5 × q40        (미발동 행은 그대로)
```
- **로직**: "불확실성이 크고 + 대표가 하위 분위수(q40)보다 한참 높은" 행 = 과대예측 위험 행. 그 행만 q40 방향으로 절반 이동시켜 큰 오차의 위쪽 꼬리를 자른다. 임계값은 전부 validation의 label-free 분위수(정답 미사용) — 운영 재현 가능.
- 효과: 0.4247/0.991/3.305 → **0.4178/0.964/2.538** (p95 -23%). row/artist 반복검증 양쪽 통과한 Cold 최초의 견고 방어층.

### 2.4 3차 방어 — 작가단위 검색 delta (PP-H23/H28, frozen lookup)

```
작가 세그먼트 = 검색결과 중 gallery_museum 소스 비율 기준:
  ratio = 0          → none → delta = −0.0313
  0 < ratio ≤ 임계   → low  → delta = −0.20
  ratio > 임계       → high → delta = +0.20
  (delta = validation 잔차의 세그먼트별 중앙값, cap ±0.2 — 작가 상수로 동결)
최종 로그가격 = 대표'' + delta(작가)        / 미커버 작가 → 상수 −0.0313 (v0.4 활성 결정)
```
- **로직**: 갤러리·미술관 소스에 많이 노출되는 작가는 체계적으로 과소예측(+0.2 상향), 검색은 되지만 미술기관 노출이 없는 작가는 과대예측(-0.2 하향), 검색 자체가 빈약하면 전역 하향 bias(-0.031)만 보정. 즉 **검색층의 본질 = 전역 bias 보정 + 기관 노출 신호에 의한 양방향 가격대 보정** (PP-CSRCH1에서 분해 확인).
- 효과: 0.4178/0.964/2.538 → **0.4098/0.8493/2.3465** (guard와 가산적, base 대비 누적 p95 -29%).

### 2.5 정책층 — v0.4 (점 예측 불변)

- **신뢰도 tier**(정답 미사용): low = qwidth ≥ val q90 OR 모델 gap(|y18−v0.2|) ≥ val q90 / high = qwidth ≤ q33 AND gap ≤ q50 AND 검색 커버 / 나머지 medium. test p95 분리: high(8.2%) 0.99 vs low(29.2%) 2.99.
- **2단 검수**: v0.3 플래그(qwidth≥q67 OR 미커버, 재현율 축) OR low tier(정밀 축).
- 표시: high=점+좁은 범위 / medium=q10~q90 범위 / low=넓은 범위+우선 검수. 금지 동결: v0.2 단독 tier 표시(과신 역전), tier 확장(test p95 붕괴).

## 3. raw-input 환경 최고 — v0.5 이종 blend의 로직 (PP-CBOOST1~3)

검색 신호를 못 쓰는 환경에서 v0.2를 대체하는 p95 방어 옵션(사용자 채택).

```
B = LightGBM Quantile(12 운영 피처, 900 est) × 5-seed 예측 평균 (q10/q40/q50/q90)
C = 선형 HuberRegressor 6구성(α∈{1e-4,1e-3} × ε∈{1.2,1.35,1.5} × 피처셋) 예측 평균
    피처: 크기 8종 + 비교군 사다리 통계 8종 + grp_price_proxy
최종 대표 = 0.7 × B_q50 + 0.3 × C  →  q40 guard(blend 전 B 기준 임계값) 적용
```
- **비교군 사다리(작가 미사용)**: ① medium_support_bucket×size_bucket(표본≥30) → ② medium+support+size(≥30) → ③ medium×size(≥50) → ④ 전체 train. 첫 매칭 그룹의 가격 통계(중앙값/Q25/Q75/IQR, 면적단가 중앙값/IQR, 표본수 log, 매칭레벨)를 피처화. `grp_price_proxy = 면적단가 중앙값 + log_area` = 비교군 기반 직접 가격 추정치.
- **leakage 차단**: C 학습 시 train 행의 그룹 통계는 5-fold 자기 fold 제외로 계산(자기 가격이 자기 피처에 새지 않음). 추론은 full-train 동결 사다리 테이블(JSON).
- **왜 작동하나**: 17개 실험 중 유일하게 재현된 레버 = **계열 다양성**. 트리(전역 분할)와 선형(전역 계수+명시 비교군 통계)은 오차 구조가 달라, 30% 블렌드만으로 test MAPE -3.5%/p95 -13%. 같은 통계를 트리의 *피처*로 넣으면 무가치(CGRP1 — 트리는 categorical 분기로 기학습)지만 *별도 선형 모델의 본체*로 쓰면 가치가 생긴다.
- 정직한 한계: MdAPE 반복 비악화 확률 0.12~0.28(구조적 center-vs-tail) → all-metric 후보가 아닌 **p95 방어 목적별** 채택.

## 4. 실험 전체 기록 (17건)

| # | 실험 | 판정 | 한 줄 결론 |
|---|---|---|---|
| 1 | PP-CBASE1 | 인프라 | 이중 base lock, 게이트(artist holdout) 정의, 정책 JSON 재현 검증 |
| 2 | PP-PCOLD1 | 인프라 | pseudo-cold 평가셋. **신규 작가 검색 lookup 커버리지 0.0 발견** |
| 3 | PP-CDIAG1 | 진단 | 위험 구간(qwidth_extreme 과소예측, gap_extreme) — 단 test 전이 약함 |
| 4 | PP-CCONF1 | **채택** | research tier p95 분리(0.99 vs 2.99) / v0.2 단독 tier 과신 기각 |
| 5 | PP-CIMG1 | 기각 | CLIP 이미지: 작가 간 일반화 신호 0 (OOF 상관 0.06~0.08) |
| 6 | PP-CSRCH1 | 보류→채택 | delta 분해(상수+outlier 5.6%). 상수 fallback = v0.4 활성 |
| 7 | PP-CCORR1 | 기각 | 잔차 보정: 잔차 역예측, guard 되돌림 — 보정 경로 폐쇄 |
| 8 | PP-COLD-ARTIFACT4 | **동결** | v0.4 정책층 (재현 검증 3종 통과) |
| 9 | PP-CGRP1 | 기각 | 그룹 통계는 트리 base에 무가치 (선형과의 차이 규명) |
| 10 | PP-CTXT1 | 기각 | 제목 텍스트: 상관 0.039 — 콘텐츠 신호 축 종결 |
| 11 | PP-CCONF2 | 기각 | tier 확장: val/holdout 통과 후 **test p95 0.99→4.4 붕괴** |
| 12 | PP-CCORR2 | 기각 | meta/라우팅: 후보 동계열·고상관 — 다양성 부재 규명 |
| 13 | PP-CBOOST1 | 유망 | 이종 blend 최초 val+test 동방향 개선 (시드/HPO는 기각) |
| 14 | PP-CBOOST2 | 강한 보류 | price proxy로 MdAPE 비악화 달성, 게이트만 미통과 |
| 15 | PP-CBOOST3 | 종결 | MAPE 확률 0.91~0.98 확립, MdAPE 트레이드오프 구조적 확인 |
| 16 | PP-CMIX1 | 기각 | 작가 가중·kNN 3원 blend — v0.5가 프런티어 확정 |
| 17 | PP-CSRCH2 | **보류(종결)** | 수집 파일럿: **상수가 수집 delta를 전 지표에서 이김** — 수집 ROI 없음 |
| + | PP-COLD-ARTIFACT5 | **동결** | v0.5 blend 직렬화 (CBOOST3 재현 diff 4.4e-16) |

## 5. 확립된 원칙 (재실험 방지용)

1. **val→test 작가 구성 이동이 최대 리스크** — validation 내부의 어떤 검증도 완전히 감지 못함. fixed test 최종 1회 확인이 과신 후보 3건을 실제로 걸렀다.
2. **콘텐츠 신호(이미지·텍스트)는 Cold 점 예측에 닫힘** — 가격 신호가 작가 내 유사성을 탄다.
3. **다양성이 유일한 조합 레버** — 동계열 조합(meta/routing/kNN)은 전멸, 이종 계열(트리+선형)만 작동.
4. **명시 그룹 통계: 트리 피처로는 무가치, 선형 본체로는 유효.**
5. **검색층 = 전역 bias 보정 + 기관 노출 양방향 보정.** 수집된 delta 공식은 신규(warm) 작가에 미전이 — 재적합은 실제 cold 트래픽 잔차 필요.
6. 금지 3건: 0604 사용 / v0.2 단독 tier 표시 / tier 확장.

## 6. 재개 조건과 진입점

- 재개 조건: ① 실제 cold 운영 트래픽 잔차 확보(검색 보정맵 재적합 + tier 재검증) ② 거래 시점 등 신규 데이터.
- 진입점: `experiments/track6/COLD_EXPERIMENT_HANDOFF_2026-06-10.md` → `docs/track6/experiments/cold_improvement_roadmap.md`. base 재생성: `run_pp_cbase1_cold_base_lock.py`, v0.5 재생성: `freeze_cold_prediction_artifact_v0_5.py`.
