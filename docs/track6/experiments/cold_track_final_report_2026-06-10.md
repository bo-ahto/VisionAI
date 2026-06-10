# Cold 가격 예측 트랙 종합 보고서

- 작성일: 2026-06-10
- 범위: Cold(unseen 작가) 가격 예측 개선 트랙 전체 — 로드맵 수립부터 잔여 경로 전수 검증·운영 동결까지 (실험 11건 + artifact 1종, 커밋 11개)
- 브랜치: `exp/track6-price-prediction` (`10c74ae`~`84964f9`)
- 지표 표기: MdAPE / MAPE / p95_APE

## 1. 요약 (Executive Summary)

Warm에서 검증된 Codex 운영 체계(base lock → 게이트 → 진단 → 타겟 실험 → 동결)를 Cold에 이식해 하루에 전 로드맵을 완주했다. **결론: 현재 보유 데이터에서 Cold 점 예측의 모든 개선 경로(보정층·콘텐츠 신호·base 피처·tier 확장)가 전수 검증 끝에 소진됐고, 운영 종착점은 "v0.3 점 예측 + v0.4 정책층"이다.** 유일하게 남은 개선 경로는 새 데이터(검색 수집 확대, 거래 시점)이며 그 기대 효과는 정량화되어 있다.

성과는 두 종류다: ① **채택·동결된 것** — 신뢰도 tier/표시/2단 검수 정책(v0.4), 미커버 작가 상수 fallback(활성), pseudo-cold 외부 검증 축. ② **닫힌 것을 확정한 것** — 9건의 기각 실험이 각각 "왜 안 되는지"의 구조적 근거를 남겨, 향후 같은 방향의 재시도를 막는다.

## 2. 대원칙 (전 실험 공통)

1. **0604 신규 라벨은 Warm 시험 제출 전용 — Cold에서 전면 사용 금지** (사용자 지시).
2. 외부 검증 축 = artist 반복 holdout + pseudo-cold 평가셋 (0604 대체).
3. test로 후보/경계값 선택 금지 — fixed test는 최종 확인 1회.
4. 재현성: 실험별 전용 폴더(`experiments/track6/PP-*/` = artifacts/outputs/reports) + 단일 실행 스크립트 + 동결 경계값 manifest. CSV는 비추적(스크립트 재생성).

## 3. 인프라 구축 (Phase 0 ~ 1)

### PP-CBASE1 — 이중 base lock (`10c74ae`)

| base | 정의 | test |
|---|---|---|
| `COLD_BASE_RESEARCH_V1` | v0.3 체인 = PP-Y18 + guard(PP-QR4) + 작가단위 검색 delta(PP-H28) | **0.4098 / 0.8493 / 2.3465** |
| `COLD_BASE_OPERATIONAL_V1` | v0.2 search-free 직렬화 파이프라인 방어 서빙값 (raw-input 실행 가능) | 0.4852 / 1.1771 / 4.1223 |

- 평가 데이터: validation cold 2,753행(작가 172) / test cold 3,099행(작가 200). 작가 쏠림 정량화(작가당 중앙값 5~6행, 최대 275~366행) → **artist holdout이 1차 게이트여야 하는 근거**.
- 채택 게이트: 작가 80%/70% holdout 각 ≥200회 — MAPE/p95 개선확률 ≥0.90, MdAPE ≥0.50 + fixed test 1회.
- v0.3/v0.2 정책 JSON 지표 재현 검증 통과(오차 <5e-4).

### PP-PCOLD1 — pseudo-cold 평가셋 (`8910037`)

- train 거래량 하위(행수 3~10) 작가를 seed 3개로 각 ~210작가/1,206행 마스킹 → unseen 작가 시뮬레이션.
- **핵심 발견: 마스킹(신규) 작가의 v0.3 검색 lookup 커버리지 = 0.0** — 검색층의 p95 -29% 이점이 진짜 신규 작가에게 전혀 전이되지 않음(100% guard fallback). 검색 커버리지 확대가 신규 작가 서빙 품질의 전제 조건임을 정량 확인.
- pseudo-cold는 real cold보다 어려움(defense 0.577 vs 0.482 MdAPE) → 절대 레벨 비교 금지, base 대비 delta + seed 방향 일치로만 사용.

### PP-CDIAG1 — 잔차 진단 (`667d156`)

- 위험 구간(validation): `gap_extreme`(운영 base MAPE 2.02배, 과대예측), `qwidth_extreme`(1.77배, 과소예측 +0.284), `guard_on`(1.67배), `artist_rows_3_9`(p95 2.08배).
- APE 상관: qwidth **+0.215**(최강 위험 신호), 검색 delta **-0.159**(검색 신호 있는 곳이 정확), 작가 행수 -0.157.
- 정직한 한계: 위험 구간의 test 전이가 약함(ratio 0.60~0.94) → 가설로만 취급.

## 4. 신호·정책 검증 (Phase 2)

### PP-CCONF1 — 신뢰도 tier 정책: **채택** (`003c5ce`)

- research tier(qwidth + 모델 gap + 검색 커버, 정답 미사용)는 **test에서도 p95 분리 유지**: high 8.2% `0.3828/0.6811/0.9904` vs low 29.2% `0.5549/0.7824/2.9877` (전체 2.35). pseudo-cold seed 3개 방향 일치.
- **operational tier(v0.2 qwidth 단독)는 기각** — test 역전(high tier가 MAPE 2.10/p95 8.40/범위 적중률 53.8%로 최악) = unseen 작가에서 "자신 있게 틀리는" 과신 신호. **raw-input 단독 환경 신뢰도 표시 금지** 원칙 확립.
- low tier(29.2%)는 기존 v0.3 검수 플래그(45.2%)보다 정밀 → OR 결합 2단 검수 채택.

### PP-CIMG1 — 이미지 임베딩: 기각 (`4c8b39e`)

- CLIP PCA(32) 저차원 residual, 커버리지 92~93%. OOF 보정 vs 잔차 상관 **0.083/0.060** — 작가 경계를 넘으면 예측력 사실상 0. 격자 72개 중 개선 1개(노이즈). IMG-P4의 test 관찰 개선은 같은 작가 내 시각 유사성의 산물로, artist-grouped 검증에서 소멸.

### PP-CSRCH1 — 검색 delta 그룹 일반화: 보류(목적별) (`8bf116f`)

- **검색 delta의 정체 규명: 전역 하향 bias 상수(-0.0313, 25/50/75분위 동일) + outlier 작가 5.6%.**
- 상수만으로 미커버 작가에서 검색층 **p95 이득의 ~57%, MAPE 이득의 22.5% 회수** (test 미커버 시나리오 0.9640→0.9381/2.5377→2.4287). holdout MAPE/p95 개선확률 0.97~1.0이나 MdAPE 0.41~0.46으로 게이트 미통과(center-vs-tail 트레이드오프).
- 그룹/메타 일반화 후보 전멸 = **per-artist delta는 실수집으로만 획득 가능** → 수집 확대의 가치(나머지 MAPE 이득 77.5%)가 정확히 정량화됨.

## 5. 보정 경로 종결 (Phase 3) — PP-CCORR1: 기각 (`08ad9ad`)

- 저차원 Huber residual / 위험 구간 segment median 모두 OOF 개선 0개. 보정값이 잔차를 **역예측**(-0.109/-0.090)하고 guard 이동량과 음의 상관(-0.31/-0.25) = 새 정보가 아니라 기존 방어층 되돌림.
- 결론: 정답 미사용 신호(qwidth/gap/검색delta/크기/매체)의 정보는 guard/search/tier 층이 이미 소진. **현재 피처로 점 예측 추가 보정 경로 폐쇄.**

## 6. 운영 동결 (Phase 4) — PP-COLD-ARTIFACT4: v0.4 (`f290f0b`, `b12ed90`)

`models/track6/cold_prediction_v0.4/` — 점 예측은 v0.3 그대로, 정책층 추가:

1. research tier 경계/규칙 동결 + 표시 정책(high=점+좁은 범위 / medium=표준 q10~q90 / low=넓은 범위+우선 검수)
2. 2단 검수(v0.3 플래그 OR low tier)
3. 금지 명문화: v0.2 단독 tier 제공 금지, 0604 사용 금지
4. **미커버 작가 상수 fallback(delta=-0.0313): 2026-06-10 사용자 결정으로 활성화** — p95 방어 우선, 대가(MdAPE 0.4178→0.4262) config 명시
5. 재현 검증 3종을 freeze 스크립트가 매회 수행: CCONF1 tier 재현 mismatch 0행 / CSRCH1 미커버 시나리오 재현 1.1e-16 / full lookup ≡ v0.3 defense 5.3e-15

## 7. 잔여 경로 전수 검증 — 3건 전부 기각 (`ece4149`, `84964f9`)

| 경로 | 실험 | 결과 | 구조적 근거 |
|---|---|---|---|
| 비교군 그룹 가격 통계 base 투입 (PP-Y 라인 미검증 갭) | PP-CGRP1 | 기각 | validation 전 지표 악화(bootstrap 0.02~0.37). Warm에서 강력했던 건 base가 선형 Huber였기 때문 — 트리 base는 categorical 분기로 동일 정보 기학습. test-only MAPE/p95 개선은 원칙상 채택 불가 기록 |
| 제목 텍스트(TF-IDF+SVD) | PP-CTXT1 | 기각 | OOF 상관 0.039. 이미지에 이어 **콘텐츠 신호 축 전체 종결** — 콘텐츠의 가격 신호는 작가 내 유사성이 주성분 |
| high tier 커버리지 확대 | PP-CCONF2 | 기각 | validation(share 50%/p95 0.95)과 artist holdout(0.98~1.0)을 전부 통과하고도 **fixed test에서 p95 4.40~4.76 붕괴**(동결 경계는 0.99). v0.4 경계가 유일한 안전 설정 — tier 확장 금지 원칙화 |

## 8. 최종 서빙 스택과 artifact 현황

```
입력(raw 12피처 + artist_key)
  ├─ 점 예측: v0.3 체인 [PP-Y18 대표 → guard(PP-QR4) → 검색 delta(커버 작가)
  │                      → 미커버 작가는 guard + 상수 delta(-0.0313, v0.4 활성)]
  └─ 정책층: v0.4 [confidence tier(high/medium/low) → 표시 정책 → 2단 검수 플래그]
```

| artifact | 내용 | test |
|---|---|---|
| v0.1 | guard only 후처리 | 0.4178 / 0.964 / 2.538 |
| v0.2_operational | search-free raw-input 실행형 | 0.4852 / 1.177 / 4.122 |
| v0.3 | guard+search 2단 방어 (점 예측 최고) | **0.4098 / 0.849 / 2.347** |
| v0.4 | v0.3 + 신뢰도/표시/검수 정책층 + 미커버 fallback(활성) | 점 예측 동일 |

## 9. 확립된 원칙·교훈

1. **val→test 작가 구성 이동이 Cold 최대 리스크.** validation 내부의 어떤 검증(artist holdout 포함)도 이를 완전히 감지하지 못함 — fixed test 최종 확인 단계가 과신 후보 3건(operational tier, CCONF2 확대 tier, CGRP1 test-only 신호)을 실제로 걸렀다.
2. **콘텐츠 신호(이미지·텍스트)는 Cold 점 예측에 닫힘** — 가격 신호가 작가 내 유사성을 타기 때문(상관 0.04~0.08).
3. **검색층의 분해**: 절반 이상은 bias 상수(이전 가능), 나머지는 outlier 작가 식별(수집으로만 가능).
4. **트리 base에는 명시적 그룹 통계가 무가치** (선형 base인 Warm과 반대).
5. 금지 원칙 3건 동결: 0604 사용 금지 / v0.2 단독 신뢰도 표시 금지 / tier 확장 금지.

## 10. 남은 경로와 권고

- **검색 수집 확대 (유일한 정량화된 점 예측 개선 경로)**: 미커버 작가 MAPE 0.938→0.849 방향. outlier 작가 식별이 본질. cold 운영 트래픽 전망과 함께 착수 판단.
- **거래 시점 수집** (데이터 과제): recency 신호 — Warm SVCSHRINK 라인과 공유되는 과제.
- 그 외 실험 재개는 비권고 — **추가 데이터 확보 전까지 Cold 트랙 휴면.** 재개 시 진입점: `experiments/track6/COLD_EXPERIMENT_HANDOFF_2026-06-10.md` → `docs/track6/experiments/cold_improvement_roadmap.md`.

## 11. 커밋·산출물 색인

| 커밋 | 내용 |
|---|---|
| `10c74ae` | 로드맵 + PP-CBASE1 이중 base lock |
| `8910037` | PP-PCOLD1 pseudo-cold 평가셋 |
| `667d156` | PP-CDIAG1 잔차 진단 + 핸드오프 신설 |
| `003c5ce` | PP-CCONF1 신뢰도 tier (채택) |
| `4c8b39e` | PP-CIMG1 이미지 (기각) |
| `8bf116f` | PP-CSRCH1 검색 delta 일반화 (보류/수집 가치 정량화) |
| `f290f0b` | PP-COLD-ARTIFACT4 v0.4 동결 |
| `b12ed90` | v0.4 미커버 fallback 활성화 (사용자 결정) |
| `08ad9ad` | PP-CCORR1 잔여 보정 (기각, Phase 3 종결) |
| `ece4149` | PP-CGRP1 그룹 통계 base (기각) |
| `84964f9` | PP-CTXT1/PP-CCONF2 (기각, 잔여 경로 소진) |

실험별 상세는 `docs/track6/experiments/pp_c*.md` 요약 문서와 각 실험 폴더의 `reports/result_report.md`, 모든 결과 표는 `postprocessing_experiment_matrix.md`에 등재됨.
