# Cold 가격 예측 개선 로드맵

- 작성일: 2026-06-10
- 목적: Warm에서 검증된 Codex 실험 운영 체계(base lock → 게이트 → 진단 → 타겟 실험 → 핸드오프)를 Cold에 이식하되, Cold의 본질(unseen 작가 일반화)에 맞게 검증 축을 재설계한다.
- 적용 범위: `data/track6_split` Cold scope (validation 2,753행 / test 3,099행).

## 0. 대원칙

### 0.1 0604 분리 원칙

**0604 신규 라벨은 Warm 시험 제출 전용 데이터다. Cold 실험에서는 어떤 용도로도 사용하지 않는다.**

- Cold 후보 선택, 스트레스 테스트, 재검증 우선순위 결정에 0604를 쓰지 않는다.
- Warm에서 0604가 하던 외부 검증 역할은 Cold에서는 ① artist 반복 holdout과 ② pseudo-cold 평가셋(Phase 0.5)이 대신한다.

### 0.2 절대 규칙 (Warm과 동일)

- test로 후보를 선택하지 않는다. test는 최종 확인 1회만.
- residual/보정/라우팅 학습은 validation에서 OOF로만 한다.
- 운영 입력 불가 피처(외부 검색 API 등)는 라우팅/보정의 **입력 기준**으로 쓰지 않는다. 단 frozen snapshot lookup(v0.3 검색 delta)은 정직한 한계를 명시하고 사용 가능.
- 실험은 `experiments/track6/<ID>_<slug>/` 전용 폴더에 저장하고 `postprocessing_experiment_matrix.md`를 갱신한다.

### 0.3 Warm과 다른 점 (검증 설계에 반영)

| 항목 | Warm | Cold | 반영 |
|---|---|---|---|
| 본질 | 작가 이력 보간 | unseen 작가 일반화 | row OOF는 낙관적 → **artist 반복 holdout이 1차 게이트** (PP-QR4에서 segment 후보가 row 0.97/artist 0.22로 붕괴한 전례) |
| 표본 | val 519 / test 607 | val 2,753 / test 3,099 | 표본은 오히려 충분. 문제는 작가 단위 의존 |
| 외부 검증 축 | 0604 라벨 | 없음 (0604는 Warm 전용) | pseudo-cold 평가셋으로 대체 |
| base | 70:30 단일 | v0.2(실행형)/v0.3(정확도형) 분열 | 이중 base lock (Phase 0) |
| 개선 단계 | 보정 saturation | 굵은 신호 유효 (검색 보정 p95 -29%) | 미세 보정보다 신호 추가 우선 |

## 1. 이중 base 정의 (Phase 0에서 고정)

| base | 구성 | test (MdAPE/MAPE/p95) | 용도 |
|---|---|---|---|
| **연구 base** `COLD_BASE_RESEARCH_V1` | v0.3 체인 = PP-Y18 대표 + guard(PP-QR4) + 작가단위 검색 delta(PP-H28, 미커버→guard fallback) | 0.4098 / 0.8493 / 2.3465 | 정확도 개선 실험의 기준. residual target은 이 값 기준 |
| **운영 base** `COLD_BASE_OPERATIONAL_V1` | v0.2 search-free 직렬화 파이프라인의 방어 적용 서빙값 (12 운영 피처, LGB Quantile q50 대표 + q40 guard blend) | 0.4852 / 1.1771 / 4.1223 (참고: 대표 q50 단독 0.4823 / 1.2424 / 4.3806) | raw-input 운영 가능성 기준. 모든 후보는 이 base 대비 개선폭도 함께 보고 |

- 모든 후속 실험은 **두 base 대비 성적을 모두 보고**한다. 연구 base만 이기고 운영 base로 내릴 수 없는 후보는 "후처리층 한정 후보"로 분류한다.
- residual target: `actual_log - cold_research_base_pred_log` (연구 트랙), `actual_log - cold_operational_base_pred_log` (운영 트랙).

## 2. Cold 채택 게이트 (Warm 3중 게이트의 Cold 변형)

후보가 운영/대표 교체 후보로 승격하려면 아래를 모두 통과해야 한다.

1. **artist 반복 holdout (1차)**: validation cold에서 작가 단위 80% / 70% holdout 각 ≥200회 반복. base 대비 **MAPE 개선확률 ≥ 0.90 AND p95 개선확률 ≥ 0.90**, MdAPE 개선확률 ≥ 0.50(비악화).
2. **row 반복 subsample (보조)**: row 80% subsample ≥200회, 같은 기준. artist 게이트보다 우선순위 낮음 — artist 통과 + row 미통과는 보류, artist 미통과는 기각.
3. **fixed test 최종 확인 (1회)**: 3지표 비악화 + 목적 지표 개선. test bootstrap ≥400회 개선확률은 보고용.
4. **0604 사용 금지**: 어느 단계에서도 사용하지 않음 (§0.1).

지표 표기는 Warm과 동일하게 `MdAPE / MAPE / p95_APE` (+ RMSE_log, within_30, over_50pct_error_rate 보고).

## 3. Phase 로드맵

| Phase | 실험 ID | 내용 | 산출물 | 상태 |
|---|---|---|---|---|
| **0** | `PP-CBASE1` | 이중 base lock: 고정 base 예측 CSV(validation/test), champion 비교표(PP-Y2/Y18/guard/v0.3/v0.2), residual target·게이트 manifest 고정. v0.3/v0.2 지표 재현 검증 포함 | `experiments/track6/PP-CBASE1_cold_base_lock/` | 진행 |
| **0.5** | `PP-PCOLD1` | pseudo-cold 평가셋: 거래량 하위 warm 작가를 train에서 마스킹해 cold화. search-free 파이프라인(v0.2식) 재학습으로 평가 가능 범위 확인. 선택 bias(warm 작가≠진짜 cold 분포) 문서화. **외부 검증 축으로만 사용, 후보 선택 금지** | pseudo-cold row/라벨/예측 CSV + bias 감사 | 대기 |
| **1** | `PP-CDIAG1` | 잔차 진단 (HCOEF13/23 모방): 연구/운영 base 잔차를 가격대·매체·크기·qwidth·검색 커버리지·작가메타 완성도별 분해 → Cold 위험 구간 확정 | 위험 구간 표 + 잔차 계수 감사 | 대기 |
| **2** | `PP-CSRCH*` / `PP-CIMG*` / `PP-CMETA*` | 신호 추가 (보정 미세화보다 우선): ① 검색 delta 커버리지 확대(현 372작가 frozen → 수집 확대, PP-H28에서 보정 유효 입증), ② 이미지 임베딩(IMG-P4 결론: 고불확실성 구간 한정 residual 보정으로 재설계), ③ 작가 메타/전시·갤러리(tier 품질 보강 후) | 신호별 후보 + 게이트 통과 여부 | 대기 |
| **3** | `PP-CCORR*` | 보정/방어 고도화: 저차원 residual Huber, qwidth 구간 cap. 기존 guard/search 층과 **직교성 확인 필수**(DEFENSE1 redundancy gap 방식). row-level router류 금지, segment 수준까지만 | 보정 후보 + 직교성 분해 | 대기 |
| **4** | `PP-CCONF*` | 신뢰도/범위 정책 공식화: CF1식 tier(정답 미사용 신호)를 Cold에 이식, 기존 검수 플래그(qwidth_q67/검색 미커버, test 검수율 45.2%)와 통합. 점 예측 개선 없이도 서비스 가치가 가장 빠른 축 | tier 정의 + 구간별 성능 분리표 + 표시 정책 | 대기 |

Phase 2의 수집 확대(검색 커버리지)처럼 비용이 드는 작업은 Phase 0~1 결과와 cold 운영 트래픽 전망을 보고 착수를 결정한다.

## 4. Codex 운영 방식

Warm의 `warm_huber_*goal_prompt*.md` 체계를 그대로 차용한다.

### 4.1 goal prompt에 반드시 포함할 것

1. **기준표**: 이중 base(연구/운영)의 split별 3지표 + champion 후보 (PP-CBASE1 산출물에서 복사).
2. **게이트**: §2의 artist 반복 holdout 중심 게이트 전문.
3. **금지 조건**: 0604 사용 금지 / test 후보 선택 금지 / 외부 API 입력 기준 금지 / frozen snapshot 의존 명시 의무 / row-level router 금지(Phase 3).
4. **산출물 기준**: 전용 폴더(artifacts/run_config.json, outputs/metrics.csv, reports/result_report.md), docs 요약, matrix 갱신.
5. **이어달리기 규칙**: 실험 종료 시 다음 실험 제안 + 핸드오프 갱신.

### 4.2 Cold용 goal prompt 골격

```text
목표: Cold 가격 예측의 [Phase N] [실험 ID]를 수행한다.

기준 (변경 금지):
- 연구 base COLD_BASE_RESEARCH_V1: test 0.4098/0.8493/2.3465
- 운영 base COLD_BASE_OPERATIONAL_V1: test 0.4852/1.1771/4.1223
- 고정 base 예측: experiments/track6/PP-CBASE1_cold_base_lock/outputs/fixed_cold_base_rows.csv
- residual target = actual_log - 해당 base pred_log

게이트:
- artist 80%/70% holdout 각 200회+: base 대비 MAPE>=0.90 AND p95>=0.90, MdAPE>=0.50
- row subsample은 보조. fixed test는 최종 확인 1회.

금지:
- 0604 데이터 사용 금지 (Warm 제출 전용)
- test로 후보/경계값 선택 금지
- 운영 입력 불가 피처를 보정 입력 기준으로 사용 금지
- 결과 과장 금지: 미통과 후보는 보류/기각으로 명시

산출물:
- experiments/track6/<ID>_<slug>/ (artifacts/outputs/reports)
- docs/track6/experiments/<id>_summary.md + postprocessing_experiment_matrix.md 갱신
- 종료 시 COLD_EXPERIMENT_HANDOFF 갱신 + 다음 실험 1개 제안
```

### 4.3 핸드오프

`experiments/track6/COLD_EXPERIMENT_HANDOFF_<날짜>.md`를 Warm 핸드오프와 같은 형식(현재 1순위, 최근 실험 흐름, 다음 작업, 재시작 첫 명령)으로 유지한다.

## 5. 참조 문서

- Cold artifact 3종: `models/track6/cold_prediction_v0.1|v0.2_operational|v0.3/`
- v0.3 정책: `models/track6/cold_prediction_v0.3/config/cold_model_policy_v0_3.json`
- 방어층 검증: `docs/track6/experiments/pp_cold_defense1_guard_search_layer_combination_summary.md`
- Warm 운영 체계 원형: `experiments/track6/PP-WBASE1_warm_base_lock/reports/warm_base_lock.md`, `experiments/track6/WARM_EXPERIMENT_HANDOFF_2026-06-09.md`
- 검색 보정 근거: `docs/track6/experiments/pp_h28_cold_search_provider_agreement_gated_correction_summary.md`
- 이미지 파일럿: `docs/track6/experiments/IMG-P4_cold_clip_multimodal_pilot.md`
