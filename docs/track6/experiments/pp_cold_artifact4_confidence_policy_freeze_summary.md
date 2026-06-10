# PP-COLD-ARTIFACT4 Cold 신뢰도/표시 정책 동결 요약

- 실험 ID: `PP-COLD-ARTIFACT4` (Cold 로드맵 Phase 4)
- 실행일: 2026-06-10
- 목적: Phase 2에서 검증 완료된 정책층을 운영 artifact로 동결해 이후 실험의 기준을 고정한다. **점 예측 정책은 v0.3 그대로** — 이번 동결은 신뢰도/표시/검수 층만 추가.
- freeze 스크립트: `scripts/track6/freeze_cold_prediction_artifact_v0_4.py`
- 번들: `models/track6/cold_prediction_v0.4/`

## 동결 내용

1. **신뢰도 tier (PP-CCONF1 채택 권고)**: research tier 경계(validation 분위수, qw_q33=0.7349/qw_q90=2.1573/gap_q50=0.1532/gap_q90=0.4253)와 규칙 동결. 근거: test p95 분리 high 0.9904(8.2%) vs low 2.9877(29.2%).
2. **표시 정책**: high=점 예측+좁은 범위 / medium=점 예측+표준 q10~q90 범위 / low=넓은 범위 우선+우선 검수.
3. **2단 검수**: `review_flag_v03`(재현율 축, qwidth≥1.4612 OR 미커버) OR `priority_review`(정밀 축, low tier).
4. **금지 명문화**: v0.2 qwidth 단독 tier 제공 금지(PP-CCONF1 test 역전/과신), 0604 사용 금지.
5. **미커버 상수 delta fallback (PP-CSRCH1, 기본 off 옵션)**: delta=-0.031295(validation 작가 중앙값, cap 0.2). 활성화 시 미커버 작가 p95 방어 모드(holdout 개선확률 0.97~1.0, 대가 MdAPE 소폭 악화). 게이트 미통과로 **기본 off** — 활성화는 서비스 목적에 따른 의사결정.

## 재현 검증 (freeze 스크립트가 매회 수행)

| 검증 | 결과 |
| --- | --- |
| PP-CCONF1 tier 배정 재현 (validation+test 5,852행) | mismatch **0행** (review flag도 0행) |
| PP-CSRCH1 미커버 시나리오 test 지표 재현 (빈 lookup) | max abs diff **1.1e-16** |
| full lookup 시 fallback 출력 ≡ v0.3 defense | max abs diff **5.3e-15** |

## 번들 구성

```
models/track6/cold_prediction_v0.4/
├── README.md
├── config/confidence_tier_policy_v0_4.json   ← 동결 경계/규칙/fallback 옵션
├── config/cold_model_policy_v0_4.json        ← 정책 요약/검증 수치/근거 실험
├── config/search_delta_lookup_v0_4.json      ← v0.3 lookup 복사(자체 완결)
├── predict/apply_cold_confidence_policy_v0_4.py  ← 독립 정책 적용기
├── evidence/PP-CCONF1_tier_metrics.csv, PP-CSRCH1_fixed_test_metrics.csv (비추적, 재생성)
├── reports/cold_artifact_release_v0_4.md
└── manifest/MANIFEST.sha256
```

적용기 입력: `quantile_width_log`, `y18_qwidth_pred_log`, `v02_defense_pred_log`, `artist_key` (+fallback 모드 시 `guard_pred_log`). 출력: `confidence_tier`, `display_policy`, 2단 검수 플래그 (+옵션 `cold_defense_with_uncovered_fallback_log`).

## Cold artifact 현황

| 버전 | 내용 | test (MdAPE/MAPE/p95) |
| --- | --- | --- |
| v0.1 | guard only 후처리 | 0.4178 / 0.964 / 2.538 |
| v0.2_operational | search-free raw-input 실행형 | 0.4852 / 1.177 / 4.122 (defense) |
| v0.3 | guard+search 2단 방어 (점 예측 최고) | 0.4098 / 0.849 / 2.347 |
| **v0.4** | **v0.3 + 신뢰도/표시/검수 정책층** | 점 예측 동일, tier·검수·fallback 옵션 추가 |

## 남은 의사결정 (변동 없음)

① 상수 fallback 활성화 여부(서비스 목적), ② 검색 수집 확대(2-3b, cold 트래픽 전망), ③ Phase 3 PP-CCORR 진행 여부.
