# Track 6 실험 계획서 - 보고용 요약

- 목적: 작품 1건의 정보를 보고 가격을 예측하는 Warm / Cold 모델 기준을 최종 보고용으로 재정리
- 핵심 방향: 모델을 먼저 고르는 것이 아니라, 데이터셋과 평가 기준을 먼저 고정한 뒤 실험을 진행
- 적용 범위: 데이터 클렌징, split 구성, 누수 방지, 피처 검증, 모델 비교, 최종 후보 선정, 신뢰도 정책
- 작성 기준: Track3/4/5에서 발견한 문제를 Track6에서 보완하는 방식으로 정리

## 1. Track6를 새로 진행한 이유

- Track3 문제:
  - Warm / Cold 구분은 했지만 일부 평가가 1작가 1작품 중심이라 검증 안정성이 부족할 수 있었음
  - Warm 성능이 작가명 피처에 과하게 의존했는지 별도 확인이 필요했음
- Track4 문제:
  - 데이터 통합과 클렌징은 진행했지만 Warm test 규모가 작아 성능 변동성이 컸음
  - 크롤링 원본 컬럼 값의 품질 검증이 더 필요했음
- Track5 문제:
  - split 구조는 개선했지만 평가 안정성과 누수 차단 기준을 더 명확히 할 필요가 있었음
- Track6 목표:
  - 작가 한글명, 동명이인, Warm/Cold 분리, label 누수 방지, test 최종 확인을 모두 반영한 최종 실험 체계 구축

## 2. 최종 목표

- 작품 1건의 정보를 입력받아 가격을 예측하는 모델 구축
- 이미 학습 데이터에 등장한 작가와 처음 보는 작가를 분리 평가
- 실제 운영에서 다시 만들 수 있는 피처만 사용
- 실험 결과와 최종 모델 선택 이유를 문서와 대시보드로 설명 가능하게 관리
- 단일 가격 예측이 위험한 경우 신뢰도 경고 또는 가격 범위 정책을 함께 검토

## 3. 예측 상황 정의

- Warm:
  - 예측 대상 작가가 학습 데이터에 존재하는 경우
  - 작가 식별값과 train 기준 작가 이력 피처를 사용할 수 있음
  - Warm / Cold 구분은 작품 수가 아니라 학습 데이터에 작가가 있는지 여부로 결정
- Cold:
  - 예측 대상 작가가 학습 데이터에 없는 경우
  - `artist_key`, `artist_name_ko`, `artist_name_ko_orig` 기준으로 모두 train과 겹치지 않아야 함
  - 작가명, 작가 이력, 작가 가격 통계 피처는 사용하지 않음
- Low-history Warm:
  - train에 작가가 존재하지만 작품 수가 적은 경우
  - train 기준 작가 작품 수가 1~4개인 경우
  - 모델 라우팅상 Warm에 가깝지만 신뢰도 경고 후보로 별도 관리
- Stable Warm:
  - Warm 작가 중 train에 최소 5개 이상의 작품이 남는 경우
  - Track6 공식 Warm validation/test는 평가 안정성을 위해 Stable Warm 중심으로 구성
  - `5개` 기준은 Warm / Cold를 나누는 기준이 아니라 Warm 평가 안정성을 위한 기준

## 4. 데이터셋 구성 계획

- 입력 후보 데이터:
  - `data/track6/track6_feature_candidates_name_corrected.csv`
- split 출력:
  - `data/track6_split/track6_train.csv`
  - `data/track6_split/track6_val_warm.csv`
  - `data/track6_split/track6_test_warm.csv`
  - `data/track6_split/track6_val_cold.csv`
  - `data/track6_split/track6_test_cold.csv`
- split 구성 원칙:
  - validation/test를 먼저 충분히 확보
  - 남은 데이터를 train으로 구성
  - Warm 평가는 train에 작가가 존재하는 작품으로 구성
  - 공식 Warm validation/test는 Stable Warm 기준으로 구성
  - Low-history Warm은 Warm이지만 별도 위험 구간으로 관리
  - Cold 평가 작가는 train과 작가 ID/한글명/원본명 기준으로 모두 분리
  - test는 최종 확인용으로만 사용
- 현재 split 규모:
  - train: 26,560건 / 1,787명
  - val_warm: 523건 / 178명
  - test_warm: 607건 / 207명
  - val_cold: 2,793건 / 160명
  - test_cold: 3,240건 / 200명

## 5. 데이터 검증 계획

- 작가명 검증:
  - 한글 작가명 보정
  - 동명이인 후보 확인
  - Cold 작가가 train과 한글명 기준으로 겹치지 않는지 확인
- split 검증:
  - Warm 평가 작가가 train에 존재하는지 확인
  - Stable Warm 평가셋은 train 최소 작품 수 5개 이상을 만족하는지 확인
  - Low-history Warm은 Warm/Cold 분류 기준이 아니라 신뢰도 위험 구간으로 따로 표시
  - Cold 작가가 train과 겹치지 않는지 확인
  - train/eval 동일 작품 후보 겹침 확인
- 컬럼 품질 검증:
  - 가격 컬럼 결측 여부 확인
  - 크기, 재료, 지지체, 작가명 컬럼의 이상값 확인
  - 학습에 쓰면 안 되는 source, URL, gallery tier 계열 컬럼 관리
- feature/label 분리 검증:
  - feature 파일에는 입력값만 보관
  - label 파일에는 정답 가격만 별도 보관
  - 모델 예측 단계에서는 label 파일을 읽지 않음
  - 평가 단계에서만 예측 결과와 label을 결합

## 6. 누수 방지 원칙

- 가격 관련 컬럼은 feature 파일에서 제거
- `price`, `krw`, `usd`, `sold`, `estimate` 등 가격성 컬럼은 label 또는 감사용으로만 관리
- Cold feature에는 작가 식별값과 작가 이력 피처를 넣지 않음
- validation label은 후보 선택에 사용 가능
- test label은 최종 후보를 고정한 뒤 최종 확인에만 사용
- test 결과를 보고 모델이나 피처를 다시 고르면 안 됨
- split이 바뀌면 해당 split 기반 실험은 다시 실행

## 7. 기본 피처 계획

- 운영 입력값:
  - `width_cm`
  - `height_cm`
  - `depth_cm`
  - `medium_category`
  - `support_category`
- 크기 파생 피처:
  - `area_cm2`
  - `log_area`
  - `aspect_ratio`
  - `has_depth`
  - `is_3d_candidate`
- 크기 파생 피처를 둔 이유:
  - 운영 입력은 가로/세로/깊이지만, 모델에는 크기의 대표값이 필요함
  - `area_cm2`는 가로와 세로를 곱해 만든 면적값으로 별도 입력값이 아님
  - `log_area`는 가격처럼 한쪽으로 치우친 크기 분포를 완화하기 위한 변환값
  - `aspect_ratio`는 같은 면적이라도 정사각형/가로형/세로형 차이를 보기 위한 값
  - 가로/세로와 면적을 함께 쓰는 것은 중복 가능성이 있으므로 T6-E005에서 피처 조합별로 검증함
  - 최종 운영에서는 성능과 설명 가능성을 기준으로 필요한 크기 표현만 유지
- Warm 전용 피처:
  - `artist_key`
  - `artist_works_log`
  - `artist_works_count_train`
- 추가 검증 피처:
  - `size_bucket`
  - `shape_bucket`
  - `medium_size_bucket`
  - `support_size_bucket`
  - `medium_shape_bucket`
  - `is_large_2d`
  - `is_large_3d`
- 제외 피처:
  - 데이터 출처
  - URL
  - 이미지 URL
  - gallery tier
  - 운영 입력에서 만들 수 없는 가격/거래 후행 정보

## 8. 실험 진행 순서

- 1단계: Track6 split 생성 및 검증
  - 목적: Track3/4/5의 평가 문제를 줄인 최종 기준 데이터셋 확보
  - 관련 실험: T6-E001, T6-E001B, T6-E001C
- 2단계: 구조-only baseline 확인
  - 목적: 작가 정보 없이 작품 구조 정보만으로 어느 정도 예측 가능한지 확인
  - 관련 실험: T6-E002
- 3단계: Warm 작가 피처 효과 확인
  - 목적: Warm에서 작가 식별값이 실제로 성능을 개선하는지 확인
  - 관련 실험: T6-E003
- 4단계: Cold 모델 후보 비교
  - 목적: 신규 작가 상황에서 어떤 모델 계열이 안정적인지 확인
  - 관련 실험: T6-E004
- 5단계: 운영 가능 피처 조합 실험
  - 목적: 가로/세로/면적/로그면적 등 크기 표현과 재료/지지체 조합 피처가 성능 개선에 도움이 되는지 확인
  - 목적: 중복 피처가 성능을 높이는지, 아니면 복잡도만 늘리는지 확인
  - 관련 실험: T6-E005
- 6단계: validation 기준 후보 고정
  - 목적: test를 보기 전에 Warm/Cold 후보를 확정
  - 관련 실험: T6-E006
- 7단계: test 최종 확인
  - 목적: validation에서 고른 후보가 holdout test에서도 유지되는지 확인
  - 관련 실험: T6-E007
- 8단계: 신뢰도/위험 구간 분석
  - 목적: 단일 가격만 보여주기 위험한 구간을 식별
  - 관련 실험: T6-E008
- 9단계: 최종 artifact 생성
  - 목적: 최종 후보 모델과 피처 목록을 manifest로 고정
  - 관련 실험: T6-E009

## 9. 가설별 실험 계획

| 가설 ID | 목표 | 검증 내용 | 판단 기준 |
|---|---|---|---|
| T6-H1 | 최종 split 기준 고정 | Cold 이름 중복, Warm train 작품 수, 컬럼 품질, feature/label 분리 검증 | split pass, 누수 컬럼 0 |
| T6-H2 | 기본 예측 가능성 확인 | 작가 피처 없이 구조-only baseline 평가 | median APE가 단순 기준보다 개선 |
| T6-H3 | Warm 성능 개선 | 작가 식별값과 작가 이력 피처 ablation | Warm median APE 개선 |
| T6-H4 | Cold 성능 개선 | Huber, Ridge, Quantile, LightGBM, XGBoost, CatBoost 비교 | Cold median/p95 개선 |
| T6-H5 | 운영 가능 피처 선정 | 크기 표현과 size/shape/material 조합 피처 비교 | median 또는 p95 개선 |
| T6-H6 | 모델 안정성 확인 | validation 후보를 test에 적용 | test 성능 급락 없음 |
| T6-H7 | 신뢰도/가격 범위 정책 | 위험 slice별 오차 확인 | 위험 구간이 전체 대비 명확히 높음 |
| T6-H8 | 최종 후보 확정 | 모델 artifact와 manifest 생성 | 파일 누락 없이 재현 가능 |

## 10. 평가 지표

- median APE:
  - 대표 오차
  - 낮을수록 좋음
  - 최우선 판단 기준
- p95 APE:
  - 큰 오차 위험
  - 낮을수록 좋음
  - 신뢰도 정책 판단에 중요
- Within-30:
  - 실제 가격의 30% 이내로 맞춘 비율
  - 높을수록 좋음
- Within-50:
  - 실제 가격의 50% 이내로 맞춘 비율
  - 높을수록 좋음
- RMSE(log):
  - 로그 가격 기준 모델 안정성
  - 낮을수록 좋음

## 11. 모델 후보 계획

- Warm 후보:
  - CatBoost
  - LightGBM / XGBoost 계열 비교 가능
  - 작가 식별값과 작품 구조 피처를 함께 사용
- Cold 후보:
  - HistGradientBoosting quantile
  - Huber
  - Ridge
  - LightGBM
  - XGBoost
  - CatBoost
- 최종 선택 방식:
  - Warm은 Warm validation median APE 기준으로 후보 선정
  - Cold는 median APE와 p95 APE를 분리해서 판단
  - validation에서 후보를 고정한 뒤 test에서 최종 확인

## 12. 현재 실험 결과 요약

- Warm validation 후보:
  - CatBoost + `base_medium_size`
  - validation median APE: `0.2665`
- Cold validation 대표 오차 후보:
  - HistGradientBoosting quantile + `base`
  - validation median APE: `0.3782`
- Cold validation 큰 오차 참고 후보:
  - Huber + `base_size_shape`
  - validation p95 APE: `1.3835`
- test 확인 결과:
  - Warm test median APE: `0.3407`
  - Cold 대표 모델 test median APE: `0.3799`
  - Cold tail 참고 모델 test median APE: `0.3563`
- 해석:
  - median 기준 성능은 test에서도 크게 무너지지 않음
  - p95 큰 오차는 여전히 커서 신뢰도/위험 구간 표시가 필요

## 13. 위험 구간 관리 계획

- 위험 후보:
  - Cold 3D 작품
  - Cold 극단 형태 작품
  - Cold 비균형 형태 작품
  - Warm 저이력 작가 작품
  - Warm 대형/소형 극단 크기 작품
- 관리 방식:
  - 단일 가격만 제공하지 않음
  - 신뢰도 낮음 문구 후보로 표시
  - 가격 범위 또는 참고 범위를 함께 제공하는 정책 검토
- 현재 분석 결과:
  - test 기준 위험 후보 11개 slice 확인
  - Cold 3D는 대표적인 고위험 구간으로 확인

## 14. 최종 산출물

- 실험 대시보드:
  - `docs/track6/dashboard/experiment_dashboard.html`
- 가설 상태표:
  - `docs/track6/tables/hypothesis_table.md`
- 실험 결과표:
  - `docs/track6/tables/experiment_results_table.md`
- 개별 실험 기록:
  - `docs/track6/experiments/`
- 최종 manifest:
  - `data/track6/artifacts/track6_artifact_manifest.json`
- 최종 후보 모델:
  - `data/track6/artifacts/track6_warm_catboost_base_medium_size.cbm`
  - `data/track6/artifacts/track6_cold_hist_quantile_base.joblib`
  - `data/track6/artifacts/track6_cold_huber_base_size_shape.joblib`

## 15. 최종 운영안 초안

- 작가가 학습 데이터에 있으면 Warm 모델 사용
- 작가가 학습 데이터에 없으면 Cold 모델 사용
- train 기준 작가 작품 수가 1~4개이면 Warm이지만 Low-history Warm으로 표시
- train 기준 작가 작품 수가 5개 이상이면 Stable Warm으로 표시
- `5개` 기준은 Warm/Cold 라우팅 기준이 아니라 신뢰도 구간 기준
- Warm 모델:
  - CatBoost 기반
  - 작가 식별값 + 작품 구조 피처 + 재료/크기 조합 피처 사용
- Cold 모델:
  - 대표 가격 예측은 HistGradientBoosting quantile 후보 사용
  - 큰 오차 위험 참고는 Huber 후보를 함께 관리
- 신뢰도 경고:
  - Cold 3D
  - Cold 극단 형태
  - Cold 비균형 형태
  - Warm 저이력 작가
- 후속 작업:
  - 서비스 입력 스키마와 피처 생성 로직 연결
  - Warm/Cold 라우팅 구현
  - 신뢰도 경고 문구와 가격 범위 표시 정책 확정
