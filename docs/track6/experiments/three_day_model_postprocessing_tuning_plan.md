# Track6 모델 선정 요약 및 3일 후처리/튜닝 실행 계획

- 목적: 현재까지의 Track6 실험 결과를 상사 보고용으로 요약하고, 3영업일 기준으로 후처리 실험과 튜닝 계획을 실행 가능한 단위로 정리한다.
- 기준 문서:
  - `a_to_j_optimal_feature_model_analysis.md`
  - `final_model_decision_and_enhancement_plan.md`
  - `postprocessing_enhancement_validation_plan.md`
- 기준 데이터:
  - Track6 고정 split
  - train / validation / test 분리 유지
  - label은 학습 target과 성능 계산에만 사용
- 진행 원칙:
  - 모델 후보는 현재 실험 결과 기준으로 고정한다.
  - 3일 동안은 신규 모델 탐색보다 모델별 피처 영향도 검증과 예측 정확도 개선 후보정에 집중한다.
  - 후처리 전에 핵심 피처 그룹 제거 실험을 먼저 수행한다.
  - validation에서 보정 기준을 정하고 test에서 한 번만 최종 확인한다.
  - Warm / Cold 결과는 합치지 않고 별도 판단한다.

## 1. 현재 모델 선정 요약

### Warm 후보

- 적용 상황:
  - 학습 데이터에 같은 작가가 있는 경우
  - 작가명 기반 가격대 학습이 가능한 경우

- 1차 후보 모델:
  - `Huber`

- 핵심 피처:
  - `width_cm`
  - `height_cm`
  - `depth_cm`
  - `area_cm2`
  - `log_area`
  - `aspect_ratio`
  - `has_depth`
  - `is_3d_candidate`
  - `medium_category`
  - `support_category`
  - `medium_support_bucket`
  - `is_extreme_aspect_ratio`
  - `artist_key`

- 현재 성능 기준:
  - Test MdAPE: 약 `0.2241`
  - Test p95_APE: 약 `2.0209`
  - Test RMSE_log: 약 `0.6093`

- 해석:
  - Warm은 `artist_key`가 작가별 가격 기준선 역할을 함
  - 실제 크기와 재료/지지체 정보가 작가 기준선 이후에도 추가 설명력을 가짐
  - 작가 학습 작품 수는 최종 입력 피처라기보다 저이력 작가 라우팅/신뢰도 판단에 활용
  - Huber는 이상치가 많은 가격 데이터에서 선형 모델보다 안정적으로 작동

### Cold 후보

- 적용 상황:
  - 학습 데이터에 한 번도 등장하지 않은 작가의 경우
  - 작가명을 모델 피처로 사용할 수 없는 경우

- 1차 후보 모델:
  - `CatBoost`

- 보조 비교 후보:
  - `LightGBM`
  - `Quantile-LAD`
  - `HistGradientBoosting`

- 핵심 피처:
  - CatBoost 최종 피처셋: `base_medium_shape`
    - `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `medium_category`, `support_category`, `shape_bucket`, `medium_shape_bucket`
  - LightGBM 보조 피처셋: `base_support_size`
    - `width_cm`, `height_cm`, `depth_cm`, `area_cm2`, `log_area`, `aspect_ratio`, `has_depth`, `is_3d_candidate`, `medium_category`, `support_category`, `size_bucket`, `support_size_bucket`

- 현재 성능 기준:
  - Cold CatBoost Test MdAPE: 약 `0.4843`
  - Cold CatBoost Test p95_APE: 약 `4.4183`
  - Cold LightGBM Test MdAPE: 약 `0.4797`
  - Cold LightGBM Test p95_APE: 약 `5.0569`

- 해석:
  - Cold는 작가명을 쓸 수 없어 Warm보다 예측 난이도가 높음
  - 작품 기본 피처만으로는 정확도 한계가 있음
  - CatBoost는 대칭 트리 구조상 `size + depth/3D + medium/shape` 조합 경로를 중심으로 해석해야 함
  - LightGBM은 leaf-wise 구조상 `size/support bucket`과 tail risk를 중심으로 해석해야 함
  - 단일 가격만 제공하기에는 p95_APE가 커서 후처리와 신뢰도 정책이 필요

## 2. 3일 업무 목표

- 1차 목표:
  - 후처리 전에 모델별 핵심 피처 그룹의 실제 성능 기여도 검증

- 2차 목표:
  - 선정된 Warm / Cold 모델의 예측값 자체를 더 정확하게 만드는 후보정 검증

- 3차 목표:
  - Cold처럼 오차가 큰 구간에서 가격 범위와 신뢰도 표시 기준 정리

- 4차 목표:
  - 추가 데이터 수집이 실제 정확도 개선으로 연결되는지 확인할 실험 설계 확정

- 3일 내 하지 않는 것:
  - 전체 데이터셋 재구성
  - 대규모 신규 크롤링
  - 완전한 운영 배포 코드 작성
  - 모델 후보 전체 재탐색

## 3. 3일 실행 계획

### Day 1: 기준 모델/피처셋 고정과 PRE-PP 착수

- 목표:
  - Warm / Cold 기준 모델을 명확히 고정
  - 최종 artifact 기준 피처셋으로 문서와 실험 기준을 통일
  - 후처리 전 baseline 예측값을 생성
  - 보정 실험 전 모델별 피처 영향도 검증을 시작

- 작업:
  - 최신 종합 분석 기준으로 후보 모델 확정
    - Warm: `Huber`
    - Cold 1순위: `CatBoost`
    - Cold 보조: `LightGBM`
  - 최종 artifact 기준 피처셋 확인
    - Warm Huber: `base_existing_combo`
    - Cold CatBoost: `base_medium_shape`
    - Cold LightGBM: `base_support_size`
  - validation / test 예측값 생성
  - 예측값과 실제값 기준 오차 테이블 생성
  - slice별 오차 분석 테이블 생성
    - 가격대
    - 호수/크기 구간
    - 재료/지지체
    - 작가 학습 작품 수
    - 작가 메타 정보량
  - PRE-PP 핵심 group-drop ablation 착수
    - CatBoost `depth/3D` 제거
    - CatBoost `medium_shape_bucket` 제거
    - LightGBM `support_size_bucket` 제거
    - LightGBM `size_bucket` 제거

- 산출물:
  - `baseline_predictions.csv`
  - `baseline_slice_metrics.csv`
  - `pre_pp_group_drop_metrics.csv`
  - Warm / Cold 기준 모델 확정 메모
  - Day 1 결과 HTML

- 판단 기준:
  - baseline 성능이 기존 종합 문서 수치와 재현되어야 함
  - group-drop 결과가 후처리 segment 후보와 연결되어야 함
  - 재현이 안 되면 후처리 실험 전 원인 확인

### Day 2: PRE-PP 결과 반영 후 후보정 실험

- 목표:
  - group-drop 결과로 후처리 segment 우선순위를 확정
  - 단일 예측 가격 자체를 더 정확하게 만들 수 있는지 검증
  - 가격 범위 표시보다 먼저 정확도 개선 후보정을 검증

- 선행 확인:
  - CatBoost에서 `depth/3D` 또는 `medium_shape_bucket` 제거 시 성능이 악화되면 해당 기준을 segment 보정 후보로 유지
  - LightGBM에서 `size_bucket` 또는 `support_size_bucket` 제거 시 p95가 악화되면 tail 안정화 기준으로 유지
  - 제거해도 성능이 유지되는 피처 그룹은 후처리 우선순위를 낮춤

- 우선 실험:
  - `PP1 구간별 편향 보정`
  - `PP4 예측값 캘리브레이션`
  - `PP5 신뢰도 기반 모델 라우팅`
  - `PP2 잔차 보정 모델`은 OOF 예측이 준비된 경우에만 실행
  - `PP3 모델 앙상블/블렌딩`은 CatBoost/LightGBM baseline이 재현된 뒤 실행

- 작업:
  - PP1:
    - validation 기준 구간별 residual 계산
    - PRE-PP에서 유지된 피처 그룹 중심으로 보정값 생성
    - Warm: 전체/pred_bin/size/medium_support 구간
    - CatBoost: depth/3D, medium_shape, leaf/segment fallback
    - LightGBM: pred_bin, size_bucket, support_size_bucket tail 안정화
    - test에 확정 보정값 1회 적용
  - PP2:
    - OOF 교차 예측이 없으면 보류
    - 기준 예측값의 잔차를 target으로 보정 모델 학습
    - Ridge / Huber / LightGBM 후보 비교
  - PP3:
    - Warm: Huber + Ridge/Linear 블렌딩 검토
    - Cold: CatBoost + LightGBM / Quantile-LAD 블렌딩 검토
  - PP4:
    - 가격대별 과대/과소 예측 보정
    - linear calibration / 구간별 median residual 비교
  - PP5:
    - 저신뢰 구간에 대체 모델 또는 보정식 적용
    - Cold 고위험 구간 p95_APE 개선 여부 확인

- 산출물:
  - 후보정 전후 성능표
  - PRE-PP 결과와 후처리 기준 연결표
  - 후보정별 validation/test 비교표
  - 채택/보류/중단 판단표
  - Day 2 결과 HTML

- 판단 기준:
  - MdAPE가 낮아져야 함
  - RMSE_log가 악화되지 않아야 함
  - p95_APE가 크게 악화되면 보류
  - test에서만 좋아지는 후보정은 채택하지 않음

### Day 3: 결과 분석, 튜닝 계획, 보고 정리

- 목표:
  - 3일간 실험 결과를 바탕으로 채택 가능한 후처리 후보 선정
  - 후속 튜닝과 추가 데이터 수집 계획 확정
  - 상사 보고용 HTML/Markdown 문서 생성

- 작업:
  - PRE-PP group-drop 결과 종합
  - PP1~PP5 결과 종합
  - Warm / Cold별 채택 후보 정리
  - Cold 신뢰도/가격 범위 정책 초안 작성
  - 추가 데이터 고도화 계획 정리
    - PP10 외부 작가 DB
    - PP11 검색/소셜 인지도 지표
  - 튜닝 계획 작성
    - 모델 하이퍼파라미터 튜닝
    - 후보정 보정값 튜닝
    - 위험 구간 라우팅 기준 튜닝
    - 검색/소셜 피처 수집 파일럿

- 산출물:
  - 3일 실험 종합 리포트
  - Warm / Cold 최종 후보정 후보표
  - 후속 튜닝 계획서
  - 추가 수집 우선순위표
  - 보고용 HTML

- 판단 기준:
  - Warm은 단일 가격 제공 가능 여부 확정
  - Cold는 단일 가격 + 범위/신뢰도 병행 여부 확정
  - 추가 수집이 필요한 항목은 성능 개선 가설과 연결되어야 함

## 4. 후처리 실험별 목적

| 실험 | 목적 | 성공 기준 |
|---|---|---|
| PRE-PP group-drop ablation | 후처리 전에 핵심 피처 그룹의 실제 성능 기여 확인 | 제거 시 MdAPE/p95 변화가 후처리 기준과 연결됨 |
| PP1 구간별 편향 보정 | 반복적으로 높게/낮게 예측하는 구간 보정 | MdAPE 개선, p95_APE 악화 없음 |
| PP2 잔차 보정 모델 | 1차 모델의 남은 오차를 2단계 모델로 보정 | validation/test 모두 개선 |
| PP3 앙상블/블렌딩 | 여러 모델 예측을 결합해 흔들림 감소 | p95_APE 또는 RMSE_log 개선 |
| PP4 예측값 캘리브레이션 | 가격대별 과대/과소 예측 보정 | 가격대별 MdAPE 균형 개선 |
| PP5 모델 라우팅 | 조건별 최적 모델 선택 | 고위험 구간 p95_APE 개선 |
| PP6/PP7 가격 범위 | 예측값 주변 범위 제공 | coverage와 범위 폭이 실무적으로 납득 가능 |
| PP10 외부 작가 DB | 추가 작가 정보가 정확도 개선에 기여하는지 확인 | baseline 대비 MdAPE 개선 |
| PP11 검색/소셜 지표 | 검색/소셜 인지도 지표의 성능 기여 확인 | 성능 개선 + 동명이인 오염률 낮음 |

## 5. 데이터 고도화와 정확도 개선 연결

- 데이터 고도화는 수집 자체가 목적이 아님
- 반드시 아래 흐름으로 검증해야 함
  - 데이터 수집
  - 작가 매칭
  - 피처 생성
  - 기준 모델 재학습
  - baseline 대비 성능 비교
  - 후보정 적용 전후 비교
  - 채택/보류 판단

- PP10:
  - 전시/수상/기관/갤러리 소속 정보 수집
  - 작가 경력과 시장 신뢰도 피처 생성
  - Cold 성능 개선 여부 확인

- PP11:
  - 네이버/구글 검색 결과 수, 검색 관심도, 소셜 언급량 수집
  - 작가 인지도와 시장 관심도 피처 생성
  - 동명이인 오염률과 재수집 변동성 확인
  - 성능 개선이 확인될 때만 모델 피처 후보로 채택

## 6. 튜닝 계획

### 모델 튜닝

- Warm:
  - Huber regularization 강도 조정
  - 수렴 조건 조정
  - 작가명 교차항 후보 재검증
  - 저이력 작가 구간 별도 평가

- Cold:
  - CatBoost depth / learning_rate / iterations / l2_leaf_reg 조정
  - LightGBM depth / learning_rate / num_leaves 조정
  - p95_APE 방어 목적의 conservative tuning
  - LightGBM / Quantile-LAD와 앙상블 비교
  - CatBoost `depth/3D`, `medium_shape_bucket` segment 민감도 확인
  - LightGBM `size_bucket`, `support_size_bucket` tail 민감도 확인

### 후보정 튜닝

- 구간별 보정값:
  - 평균 residual 대신 median residual 우선 검토
  - sample 수 부족 구간은 상위 구간 보정값 사용

- 잔차 보정 모델:
  - 단순 모델부터 적용
  - 복잡한 모델은 과적합 여부 확인 후 채택

- 라우팅:
  - 저신뢰 구간 기준을 단순하게 유지
  - 성능 개선보다 설명 가능성을 함께 고려

## 7. 보고 시 핵심 메시지

- 현재 모델 선정은 완료 단계
  - Warm: `Huber`
  - Cold 1순위: `CatBoost`
  - Cold 보조: `LightGBM`

- 다음 3일의 핵심은 모델 재탐색이 아님
  - 선정된 모델의 예측값을 얼마나 더 정확하게 만들 수 있는지 검증

- 데이터 고도화는 정확도 개선과 직접 연결해 검증
  - 수집 성공률만 보지 않음
  - baseline 대비 성능 개선을 반드시 확인

- Cold는 단일 가격만으로는 위험
  - 후보정
  - 가격 범위
  - 신뢰도 등급
  - 고위험 구간 라우팅
  - 위 항목을 같이 검증해야 함

## 8. 최종 산출물 목록

- 3일 실행 결과 요약 HTML
- 후보정 전후 성능 비교표
- Warm / Cold 최종 후보정 후보표
- 추가 수집 피처 우선순위표
- 튜닝 계획서
- 운영 적용 전 체크리스트
