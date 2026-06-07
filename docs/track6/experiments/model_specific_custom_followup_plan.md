# 모델 구조별 커스텀 보정 후속 실행 계획

- 작성일: 2026-06-03
- 목적: 지금까지의 실험 결과를 바탕으로 모델 구조별 약점에 맞춘 보정이 충분했는지 확인하고, 추가 개선 가능성이 큰 후보를 실제 실행 가능한 단위로 나눈다.
- 기준: validation에서 기준을 정하고 test는 선택 후 확인용으로만 사용한다.

## 1. 현재 판단

- Warm은 `PP-V6 fine_blend_mape_guarded`가 현재 대표 후보로 가장 안정적이다.
- Warm `PP-WMAPE` CatBoost residual 보정은 validation 성능이 강하지만 validation-test 차이가 커서, 대표 후보로 바로 교체하지 않고 반복 안정성 검증이 필요하다.
- Cold는 단순 CatBoost leaf 보정보다 LightGBM/Quantile이 만든 q-width 기반 보정이 더 안정적인 신호를 보였다.
- Cold 검색 보정은 일부 MAPE/p95 개선 신호가 있으나 provider agreement가 낮아, 전체 적용보다 제한 적용 또는 신뢰도 정책 적용이 맞다.
- 서비스 비교군 통계 피처는 모델 입력과 API 표시값 모두에 중요하지만, train/validation/test 누수를 막는 기준을 먼저 정해야 한다.

## 2. 추가 실행 우선순위

| 우선순위 | 실험 ID | 대상 | 핵심 질문 | 실행 방식 | 채택 기준 |
|---:|---|---|---|---|---|
| 1 | `PP-I7-W` | Warm `PP-V6/V8/WMAPE` | CatBoost residual 보정이 실제로 대표 후보를 대체할 만큼 안정적인가? | `PP-V6`, `PP-V8`, `PP-WMAPE` 행 단위 예측을 모아 test row/artist bootstrap으로 비교 | MdAPE 악화가 작고 MAPE/p95 개선 확률이 높으면 목적별 후보 |
| 2 | `PP-I7-C` | Cold `PP-H23/H26` 검색 보정 | 검색 보정을 전체가 아니라 신뢰 가능한 구간에만 적용하면 더 안전한가? | `recommended_action`, `qwidth_bin` 조건별로 검색 보정 적용 범위를 제한 | validation에서 선택한 제한 정책이 test에서 MAPE/p95 개선을 유지 |
| 3 | `PP-SVC1` | Warm/Cold 공통 | 서비스 비교군 통계 피처가 정확도와 API 설명력을 개선하는가? | train 기준 비교군별 호당가 중앙값/범위/매체별 분포/N을 만들고 validation/test에 join | 누수 없이 MdAPE/MAPE 개선 또는 신뢰도 구간 분리 |
| 4 | `PP-FINAL-NARROW` | 최종 후보 | 최종 후보만 좁은 설정 재튜닝하면 개선이 남아 있는가? | Warm 1개, Cold 1개 후보에 한해 좁은 grid로 재실행 | 개선폭이 작아도 validation/test 방향 일치 |

## 3. PP-I7-W 상세 계획

- 비교 기준 후보:
  - 기준: `PP-V6 fine_blend_mape_guarded`
  - 배포 단순화: `PP-V8 compact_blend_mape_guarded`
  - 추가 보정: `PP-WMAPE wmape_catboost_residual_v8_compact_blend_mape_guarded`
  - 추가 보정: `PP-WMAPE wmape_catboost_residual_h29_h29_v8_compact_mape_gallery_median_cap0p05`
- 검증 방법:
  - validation/test 기본 지표를 다시 정규화한다.
  - test row bootstrap으로 샘플 구성 변화에 따른 개선 확률을 본다.
  - test artist bootstrap으로 작가 구성 변화에 따른 개선 확률을 본다.
- 판단:
  - `PP-WMAPE`가 MAPE/p95는 개선하지만 MdAPE가 커지면 대표 후보가 아니라 방어 후보로 분류한다.
  - artist bootstrap에서 개선 확률이 낮으면 과적합 또는 특정 작가 구성 의존 가능성으로 본다.

## 4. PP-I7-C 상세 계획

- 비교 기준 후보:
  - 기준: `PP-Y2` 계열 baseline pred_log
  - 검색 후보: `h23_gallery_museum_median_cap0.2`
  - 검색 후보: `h23_news_median_cap0.2`
  - 검색 후보: `h23_exhibition_median_cap0.2`
  - 위험 후보: `h26_risk_qwidth_action_median_cap0.2`
- 제한 적용 조건:
  - 전체 적용
  - `recommended_action == candidate_for_h14_h18`인 경우만 적용
  - `qwidth_bin == risk`인 경우만 적용
  - `qwidth_bin in caution/risk`인 경우만 적용
  - `candidate_for_h14_h18`이면서 caution/risk인 경우만 적용
- 판단:
  - 전체 적용보다 제한 적용이 MdAPE 악화를 줄이고 MAPE/p95 개선을 유지하면 서비스 후보로 남긴다.
  - provider agreement가 낮은 구간은 점 예측 직접 보정보다 신뢰도 하향/수동 검수 플래그로 우선 사용한다.

## 5. PP-SVC1 서비스 비교군 통계 피처 계획

- 생성 피처:
  - 같은 비교군의 호당가 중앙값
  - 같은 비교군의 호당가 분위 범위
  - 같은 비교군의 매체별 호당가 중앙값
  - 같은 비교군의 유효 표본 수 N
  - 비교군 coverage 등급
- 비교군 후보:
  - 작가 + 매체 + 크기 구간
  - 작가 + 크기 구간
  - 매체 + 지지체 + 크기 구간
  - Cold fallback용 전체 작품 조건 구간
- 누수 방지:
  - validation/test의 비교군 통계는 train 데이터로만 계산한다.
  - Warm validation/test 작가의 자기 라벨은 통계 계산에 포함하지 않는다.
  - 표본 수가 부족하면 상위 비교군으로 fallback한다.
- 활용:
  - 모델 피처로 사용한다.
  - 서비스 API 표시값으로도 사용한다.
  - 신뢰도 등급과 가격 범위 폭 산출에 사용한다.

## 6. 이번 실행 범위

- 이번 실행에서는 `PP-I7-W`, `PP-I7-C`를 먼저 수행한다.
- `PP-SVC1`은 비교군 정의와 누수 방지 로직이 필요하므로 별도 실행 스크립트로 분리한다.
- `PP-FINAL-NARROW`는 `PP-I7` 결과까지 본 뒤 최종 후보가 확정되면 실행한다.
