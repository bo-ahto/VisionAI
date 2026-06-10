# Cold 가격 예측 실험 핸드오프

작성일: 2026-06-10

## 현재 목표

Cold(unseen 작가) 가격 예측을 Warm Codex 운영 체계(base lock → 게이트 → 진단 → 타겟 실험)로 개선한다.
로드맵: `docs/track6/experiments/cold_improvement_roadmap.md`

## 대원칙 (변경 금지)

- **0604는 Warm 시험 제출 전용 — Cold 실험 전 단계에서 사용 금지.**
- 외부 검증 축은 ① artist 반복 holdout, ② pseudo-cold 평가셋(PP-PCOLD1).
- test로 후보/경계값 선택 금지(최종 확인 1회). 보정/경계는 validation fold 내부에서만.

## 고정 기준 (PP-CBASE1, test MdAPE/MAPE/p95)

| base | 정의 | test |
|---|---|---|
| `COLD_BASE_RESEARCH_V1` | v0.3 guard+search 체인 (`research_base_pred_log`) | 0.4098 / 0.8493 / 2.3465 |
| `COLD_BASE_OPERATIONAL_V1` | v0.2 search-free 방어 서빙값 (`v02_defense_pred_log`) | 0.4852 / 1.1771 / 4.1223 |

- 고정 base 예측: `experiments/track6/PP-CBASE1_cold_base_lock/outputs/fixed_cold_base_rows.csv` (스크립트로 재생성 가능)
- 채택 게이트(1차): validation 작가 80%/70% holdout 각 ≥200회 — base 대비 MAPE ≥0.90 AND p95 ≥0.90, MdAPE ≥0.50. row subsample 보조, fixed test 최종 1회.

## 완료된 실험

| 실험 | 결과 | 다음에 주는 좌표 |
|---|---|---|
| `PP-CBASE1` (Phase 0) | 이중 base lock + 정책 JSON 재현 검증 통과. 작가 쏠림 정량화(중앙값 5~6행, 최대 275~366행) | 모든 후속 실험의 고정 기준 |
| `PP-PCOLD1` (Phase 0.5) | pseudo-cold 평가셋(seed 3개, 각 ~210작가/1,206행). pseudo defense 0.5772/1.1877/4.1654 — real cold보다 어려움. **신규 작가의 검색 lookup 커버리지 0.0** | 절대 레벨 비교 금지, base 대비 delta + seed 3개 방향 일치로만 사용. 검색 커버리지 확대는 신규 작가 서빙의 전제 조건 |
| `PP-CDIAG1` (Phase 1) | 위험 구간(validation): gap_extreme(운영 2.02배), qwidth_extreme(1.77배/과소예측), guard_on, artist_rows_3_9. APE 상관: qwidth +0.215, 검색 delta -0.159, 작가 행수 -0.157. **위험 구간의 test 전이 약함(0.60~0.94) → 가설 취급** | Phase 2~3 타겟: qwidth_extreme+저행수 작가(이미지 선택 적용), 검색 커버리지(점 예측+fallback 양쪽 유효), qwidth는 표시 정책으로 |
| `PP-CCONF1` (Phase 2-1) | research tier(qwidth+gap+검색커버)는 test p95 분리 유지(high 0.99 vs low 2.99), pseudo-cold seed 3개 방향 일치 → **표시 정책 채택 권고**(high=좁은 범위/low=넓은 범위+우선 검수, v0.3 플래그와 OR 2단 검수). **operational tier(v0.2 qwidth 단독)는 test 역전(high tier MAPE 2.10/p95 8.40/범위적중 53.8%) → 기각** | raw-input 환경 신뢰도 신호는 추가 입력 확보 전 제공 금지. low tier(29.2%)는 v0.3 플래그(45.2%)보다 정밀한 우선 검수 축 |
| `PP-CIMG1` (Phase 2-2) | **기각** — CLIP PCA 저차원 residual은 artist-grouped OOF에서 신호 소멸(MAPE 개선 1/72, 게이트 진입 0). OOF 보정값 vs 잔차 상관 0.06~0.08 = 작가 경계 일반화 신호 없음 | 이미지의 가격 신호는 같은 작가 내 시각 유사성이 주성분 → Cold 점 예측 보정 부적합. 용도 전환 후보(신뢰도 보조 신호)로만 유지. IMG-P4식 test 관찰 개선은 강한 검증에서 사라짐 |

## 다음 작업 (Phase 2, 착수 전 결정 필요)

1. **PP-CSRCH1 — 검색 delta 커버리지 확대 설계**: 현 lookup은 cold split 372작가 frozen. 신규 작가 커버 0% (PCOLD1 정량 확인). 수집 확대는 비용이 들어 **cold 운영 트래픽 전망 확인 후 착수 결정** (로드맵 §3). 선행으로 "수집 없이 가능한 것" 검증 가치: 검색 delta를 작가 단위가 아니라 작가 메타/매체/가격대 그룹 단위로 일반화해 미커버 작가에 전이하는 후보.
2. **PP-CIMG1 — 이미지 임베딩 선택 적용**: IMG-P4 결론(전 구간 X, 고위험 구간 한정 residual 보정) + CDIAG1 위험 구간(qwidth_extreme, artist_rows_3_9)을 결합. pseudo-cold(PCOLD1)를 외부 검증 축으로 사용. 데이터 준비 상태는 `audit_track6_image_multimodal_readiness.py` 참고.
2. ~~PP-CIMG1~~ 완료 — 기각 (위 표 참조).
3. ~~PP-CCONF1~~ 완료 — 채택 권고 (위 표 참조).
4. ~~PP-CSRCH1(a)~~ 완료 — 보류(목적별). **delta = 전역 bias 상수 + outlier 5.6%** 구조 확인. 상수만으로 미커버 작가 p95 이득 ~57% 회수(MAPE 22.5%), holdout MAPE/p95 개선확률 0.97~1.0이나 MdAPE 0.41~0.46으로 게이트 미통과. 그룹/메타 일반화는 상수와 동일 = per-artist 신호는 수집으로만 획득 가능.

## Phase 2 완료 — 의사결정 대기 (사용자 판단 필요)

1. **상수 delta(-0.0313)를 미커버 작가 "p95 방어 모드"로 v0.3 정책 fallback에 반영할지** — MAPE/p95 방어 근거 강함(0.97~1.0), 대가는 MdAPE 소폭 악화. 서비스 목적(큰 오차 회피 vs 중앙 정확도)의 선택.
2. **검색 수집 확대(2-3b) 착수 여부** — 기대 효과 정량화됨: 미커버 작가 MAPE 0.9381→0.8493 방향(outlier 작가 식별이 본질). cold 운영 트래픽 전망과 함께 판단.
3. ~~Phase 3 (PP-CCORR1)~~ **완료 — 기각**: 저차원 Huber/segment median 모두 OOF 개선 0개, 보정값이 잔차 역예측(-0.09~-0.11) + guard 층 되돌림(-0.25~-0.31). **현재 피처로 Cold 점 예측 추가 보정 경로 닫힘.**

## 트랙 결론 (2026-06-10)

Cold 로드맵 Phase 0~4 전체 완료. 합리적 종착점 도달:
- **점 예측**: v0.3 (guard+search, test 0.4098/0.8493/2.3465)
- **정책층**: v0.4 (신뢰도 tier/표시/2단 검수 + 미커버 상수 fallback 활성)
- **잔여 개선 경로 = 새 정보뿐**: ① 검색 수집 확대(미커버 MAPE 0.938→0.849 방향, cold 트래픽 전망 필요) ② 거래 시점 등 신규 데이터 과제
- 추가 데이터/트래픽 확보 전까지 **Cold 실험 트랙 휴면 권고**. 재개 시 이 핸드오프와 `cold_improvement_roadmap.md`부터 확인.

## 추가 검증 (2026-06-10 후속): 잔여 경로 ①③④ 전부 기각 — 트랙 결론 확정

| 경로 | 실험 | 판정 |
|---|---|---|
| ① 비교군 그룹 가격 통계 base 투입 (PP-Y 미검증 갭) | `PP-CGRP1` | 기각 — validation 악화(bootstrap 0.02~0.37). 트리 base는 동일 정보 기학습 |
| ③ 제목 텍스트(TF-IDF+SVD) residual | `PP-CTXT1` | 기각 — OOF 상관 0.039, 콘텐츠 신호 축 종결 |
| ④ high tier 커버리지 확대 | `PP-CCONF2` | 기각 — val/holdout 통과처럼 보였으나 **test p95 0.99→4.4 붕괴**. v0.4 동결 경계 유지 필수, tier 확장 금지 |

종합: 현재 데이터의 잔여 경로(보정/콘텐츠/base 피처/tier 확장) 전수 소진. **유일한 개선 경로 = ② 검색 수집 확대**(미커버 MAPE 0.938→0.849 정량화) + 거래 시점 수집. 요약: `docs/track6/experiments/pp_ctxt1_cconf2_cold_path_rejection_summary.md`, `pp_cgrp1_cold_group_price_stats_base_summary.md`
4. ~~Phase 4 (운영 반영)~~ **완료 — PP-COLD-ARTIFACT4**: `models/track6/cold_prediction_v0.4/` 동결 (tier/표시/2단 검수 + 상수 fallback, 재현 검증 3종 통과: tier mismatch 0 / CSRCH1 재현 1.1e-16 / v0.3 defense 일치 5.3e-15). **상수 fallback은 2026-06-10 사용자 결정으로 활성화(enabled=true) 동결** — 미커버(신규) 작가 p95 방어 우선, 대가(MdAPE 0.4178→0.4262)는 config note 명시. 남은 의사결정은 ②검색 수집 확대 ③Phase 3 CCORR 두 건.

## 재시작 후 바로 확인할 파일

```text
docs/track6/experiments/cold_improvement_roadmap.md
experiments/track6/PP-CBASE1_cold_base_lock/reports/cold_base_lock.md
experiments/track6/PP-CDIAG1_cold_residual_diagnosis/outputs/risk_segments.csv
experiments/track6/PP-PCOLD1_pseudo_cold_eval_set/outputs/pseudo_cold_metrics.csv
```

base 예측 CSV 재생성: `python3 scripts/track6/run_pp_cbase1_cold_base_lock.py`


## 추가 (PP-CCORR2): Warm식 모델 특성 보정도 기각

V2식 meta-stack(현행 후보 6종)과 PP148식 위험 구간 라우팅 모두 게이트 진입 0. meta OOF 상관 0.824 < base 단독 0.844 — Cold 후보들은 동일 계열·고상관이라 의견차에 정보가 없음(후보 다양성 전제 불성립). 트랙 결론 변동 없음.


## 추가 (PP-CBOOST1): base 학습 축 — 이종 blend 유망 보류

시드 앙상블·HPO 기각. **이종 계열(선형 Huber+그룹통계) blend w0.4가 세션 최초 val+test 동방향 개선**(val MAPE -4%, test MAPE -3.5%/p95 4.22→3.92)이나 게이트 미통과(MdAPE 희생, p95 prob 0.77). Cold 재개 시 1순위 = PP-CBOOST2 (C 강화 + MdAPE-guard blend + pseudo-cold 검증, 통과 시 v0.2 교체+재lock).


## 추가 (PP-CBOOST2): 이종 blend 안정화 — 보류(강한 후보)

C 강화(grp_price_proxy)로 `w0.3` blend가 validation MdAPE 비악화 + MAPE/p95 개선, pseudo-cold 3/3, fixed test 3지표 전부 개선(MAPE 1.2138→1.1787, p95 4.22→3.66) 달성. bootstrap 게이트만 미통과(0.87/0.76/0.25). **Cold 재개 1순위 = PP-CBOOST3** (C 앙상블 분산 축소 + w 미세 grid + artist holdout 직접 게이트 → 통과 시 v0.2 교체 + CBASE 재lock + guard/tier 재적합).


## 추가 (PP-CBOOST3): CBOOST 라인 종결

C 앙상블/적응 w로도 MdAPE 비악화 확률(0.12~0.28) 불변 — 구조적 트레이드오프 확정, all-metric 교체 불가. MAPE 개선은 0.91~0.98로 확립. **후보 확정: 이종 blend w0.3 = MAPE/p95 방어 목적별 후보**(test MAPE -3.5%/p95 -13%, 대가 MdAPE 미세 악화). 채택 여부는 서비스 목적 의사결정(채택 시 ARTIFACT5로 v0.2 옵션 동결). 추가 안정화 실험 비권고. Cold 최종 좌표: 전 지표 개선=검색 수집 확대 / 수집 없는 목적별 개선=이 blend / 현행=v0.3+v0.4.
