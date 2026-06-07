# Track6 남은 실험 실행 업데이트

- 작성일: 2026-06-03
- 목적: 남은 실험 여부를 재점검하고, 바로 실행 가능한 검증 실험을 진행한 뒤 후속 판단을 정리한다.

## 1. 실행한 남은 실험

| 실험 ID | 실험명 | 실행 위치 | 목적 | 상태 |
|---|---|---|---|---|
| `PP-Y21` | Cold PP-Y18 추가 split/seed 안정성 검증 | `experiments/track6/PP-Y21_cold_y18_split_seed_stability` | `PP-Y18 qwidth_bin` 후보가 특정 test 구성에서만 좋아진 것인지 확인 | 실행 완료 |
| `PP-H22` | Naver x Python 검색 Provider 일치도 검증 | `experiments/track6/PP-H22_provider_agreement_stability` | 외부 검색 provider가 작가별로 일관된 신호를 주는지 확인 | 실행 완료 |

## 2. PP-Y21 결과

### 2.1 Test 기준

| 후보 | MdAPE | MAPE | p95_APE | 판단 |
|---|---:|---:|---:|---|
| `PP-Y2` 기준선 | 0.4421 | 1.0484 | 3.3537 | 기존 기준 |
| `PP-Y18 qwidth_bin_oof_min30_cap0.25` | 0.4247 | 0.9910 | 3.3053 | 대표/평균/큰오차 균형 후보 |
| `PP-Y18 external_x_qwidth_oof_min30_cap0.25` | 0.4239 | 1.0003 | 3.3553 | MdAPE 최저 참고 후보 |
| `PP-Y18 pred_x_qwidth_oof_min30_cap0.35` | 0.4438 | 1.1083 | 2.8025 | p95 방어 전용, 대표 후보 보류 |

### 2.2 반복 holdout 안정성

| 후보 | artist holdout MdAPE 개선확률 | artist holdout MAPE 개선확률 | artist holdout p95 개선확률 | 판단 |
|---|---:|---:|---:|---|
| `qwidth_bin_oof_min30_cap0.25` | 0.8625 | 0.9875 | 0.9625 | 채택 후보 |
| `external_x_qwidth_oof_min30_cap0.25` | 0.8625 | 0.9875 | 0.8750 | 채택 후보 |
| `pred_x_qwidth_oof_min30_cap0.35` | 0.8125 | 0.5500 | 0.4500 | 보류 |
| `pred_x_qwidth_oof_min30_cap0.15` | 0.8500 | 0.6250 | 0.4625 | 보류 |

해석:

- `qwidth_bin_oof_min30_cap0.25`는 row holdout과 artist holdout 모두에서 개선 방향이 유지됐다.
- 특히 MAPE와 p95 개선 확률이 높아 Cold 개선 후보로 올릴 수 있다.
- 단, 이번 검증은 기존 예측값을 고정한 평가 구성 안정성 검증이다. 완전한 재학습 split 검증은 아니다.
- 따라서 서비스 문서에는 `PP-Y2` 기준선과 함께 `PP-Y18/PP-Y21 검증 통과 후보`로 명시하는 것이 안전하다.

## 3. PP-H22 결과

### 3.1 Provider 수집 현황

| provider | result rows | artist count | template count |
|---|---:|---:|---:|
| `naver_api_blog` | 1,723 | 80 | 5 |
| `naver_api_news` | 1,530 | 80 | 5 |
| `naver_api_webkr` | 1,884 | 80 | 5 |
| `python_ddg` | 12,818 | 428 | 5 |
| `python_ddg_art_context` | 12,833 | 428 | 5 |

### 3.2 Provider agreement 등급

| 등급 | 작가 수 | agreement 중앙값 | source similarity 중앙값 | context similarity 중앙값 | 판단 |
|---|---:|---:|---:|---:|---|
| low | 69 | 0.3843 | 0.1733 | 0.5481 | 직접 점 예측 피처 사용 부적합 |
| medium | 9 | 0.5326 | 0.5175 | 0.8152 | 수동 검수/신뢰도 보조 후보 |

해석:

- Python provider는 커버리지는 넓지만 일반 웹 결과가 많이 섞여 Naver 공식 API와 source group이 크게 달랐다.
- 현재 agreement score는 가격점 예측 피처로 직접 쓰기에는 낮다.
- 대신 provider disagreement는 동명이인/무관 결과 위험을 알려주는 수동 검수 우선순위와 신뢰도 하향 기준으로 쓸 수 있다.

### 3.3 예측 오차와 연결

| 후보 | slice | MdAPE | MAPE | p95_APE | 해석 |
|---|---|---:|---:|---:|---|
| `PP-Y2` 기준선 | agreement low | 0.3800 | 1.5782 | 4.6289 | low agreement 구간은 평균/큰오차 위험이 큼 |
| `h23_news_median_cap0.2` | agreement low | 0.3344 | 1.3644 | 4.6202 | MdAPE는 개선되지만 p95 위험은 큼 |
| `h23_gallery_museum_median_cap0.2` | agreement low | 0.3476 | 1.2996 | 3.6086 | low agreement 구간에서 p95 완화가 상대적으로 좋음 |

판단:

- 검색 provider agreement는 현재 `가격을 직접 올리고 내리는 피처`보다 `위험 구간 식별 피처`로 적합하다.
- 운영에서는 agreement low 작가를 수동 검수 후보로 올리고, 가격 범위는 넓게 표시하는 정책이 적합하다.

## 4. 최신 남은 실험 판단

| 항목 | 상태 | 판단 |
|---|---|---|
| Warm 정확도/MAPE 추가 실험 | 대부분 완료 | `PP-WMAPE`, `PP-H29`, `PP-V6/V8` 결과를 최종 정책에 반영하는 단계 |
| Cold `PP-Y18` 추가 검증 | `PP-Y21` 완료 | `qwidth_bin_oof_min30_cap0.25`는 Cold 개선 후보로 유지 가능 |
| 검색 provider agreement | `PP-H22` 완료 | 점 예측 직접 피처보다 수동 검수/신뢰도 하향 기준으로 사용 |
| Google JSON API | 보류 | 접근 권한 해결 시 별도 `PP-H21-G`로 재검증 |
| H25 수동 검수 | 남음 | 자동 실험이 아니라 데이터 품질 검수 작업 |
| 신규 갤러리/수상/기관 DB | 조건부 | 새 표준 데이터가 들어오면 `PP-G/PP-X` 계열 재검증 |

## 5. 다음 작업

1. 최종 후보 문서/API 정책 문서에 `PP-Y21` 결과를 반영한다.
2. Cold는 `PP-Y2` 기준선과 `PP-Y18 qwidth_bin_oof_min30_cap0.25` 개선 후보를 함께 보고한다.
3. 검색 피처는 `h23_news`, `h23_gallery_museum` 보정 후보와 `PP-H22 provider disagreement`를 분리해서 쓴다.
4. 서비스에서는 provider agreement가 낮은 작가에 대해 단일 가격 확정도를 낮추고 가격 범위/수동 검수 정책으로 연결한다.
