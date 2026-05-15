# H2 H3 H4 기본 변수와 파생 변수 재확인 기록

- 실험 ID: `H2_H3_H4_feature_foundation_confirm`
- 날짜: 2026-05-13
- 단계: 가설 종결 확인
- 상태: 종결
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 가설 문서:
- [`docs/track3_hypothesis_list_v1.md`](/Users/bo/VisionAI/docs/track3_hypothesis_list_v1.md:1)
- 관련 결과 파일:
- `data/track3_phase1_cold_results.json`
- `data/track3_phase2_cold_results.json`
- `data/track3_phase1_warm_results.json`
- `data/track3_phase2_warm_results.json`
- `data/track3_pr7_results.json`
- `data/track3_pr22_new_features_results.json`
- `data/track3_pr23_f1_combo_results.json`
- `data/track3_h3_artist_feature_confirm_results.json`
- 기록 유형:
- 묶음 실험

## 1. 목적

- H2, H3, H4를 현재 실험 근거 기준으로 종결 가능한지 확인
- H2:
- 작가 정보 없이 작품 구조 정보만으로 Cold baseline이 성립하는지 확인
- H3:
- Warm에서 작가 정보가 실제 성능 개선을 만드는지 확인
- H4:
- 운영 가능한 파생 피처가 실제로 채택할 만큼 성능 개선을 주는지 확인

## 2. 가설

- H2
- 작가 정보 없이도 작품 구조 정보만으로 Cold 예측이 가능할 것이다
- H3
- Warm에서는 작가 정보를 포함할 때 성능이 좋아질 것이다
- H4
- 운영 가능한 파생 피처가 추가 성능 개선을 줄 것이다

## 3. 사용 데이터

- 공통 학습 데이터:
- `data/track3_unified_v1_train.csv`
- `data/release_split/track3_train.csv`
- Warm 최종 확인:
- `data/release_split/track3_test_warm.csv`
- Cold 최종 확인:
- `data/release_split/track3_test_cold.csv`
- split 기준:
- Cold는 작가 단위 분리
- Warm은 학습에 남아 있는 작가의 신규 작품
- 집계 변수:
- `artist_works_log`는 train 기준으로만 계산

## 4. 실행 스크립트

- H2 관련:
- `scripts/track3/train_linear_cold.py`
- `scripts/track3/train_tree_cold.py`
- H3 관련:
- `scripts/track3/train_linear_warm.py`
- `scripts/track3/train_tree_warm.py`
- `scripts/track3/h3_artist_feature_confirm.py`
- H4 관련:
- `scripts/track3/pr7_feature_engineering.py`
- `scripts/track3/pr22_new_features_ablation.py`
- `scripts/track3/pr23_f1_combo_confirm.py`

## 5. H2 결과

- 확인 질문:
- 작가 정보 없이 작품 구조 정보만으로 Cold 예측 baseline이 가능한가
- 사용 변수:
- `medium_category`
- `support_category`
- `has_depth`
- `log_area`
- `estimated_ho`
- `orientation`
- 작가 정보:
- `artist_name_ko` 미사용

### Cold 선형 결과

- `Quantile_q05`
- `median APE 0.429`
- `MAPE 0.659`
- `RMSE(log) 0.801`
- `Within-30% 0.349`
- `Huber`
- `median APE 0.438`
- `OLS / Ridge / Lasso`
- `median APE 0.543 ~ 0.544`

### Cold 비선형 결과

- `LightGBM`
- `median APE 0.473`
- `XGBoost`
- `median APE 0.491`
- `CatBoost`
- `median APE 0.475`

### H2 해석

- 작가 정보 없이도 Cold baseline은 성립함
- 단순 median baseline보다 구조 변수 모델이 훨씬 나음
- 현재 Cold에서는 복잡한 비선형 모델보다 robust 선형 계열이 더 안정적임
- 다만 고가 작품, source별 편차, 특정 재료 구간 같은 약점 slice는 남아 있음

### H2 결론

- 채택 / 보류 / 중단:
- 채택
- 참고 상태:
- H2 검증 완료
- 후속:
- Cold baseline 자체는 종결
- 약점 slice 보완은 H7/H8/H13/H14/H15에서 따로 다룸

## 6. H3 결과

- 확인 질문:
- Warm에서 작가 정보가 실제 성능 개선을 만드는가
- 비교 방식:
- release split `test_warm`에서 작가 정보 제외/포함 비교

### Warm 모델 결과

- Warm 선형 최고:
- `Quantile_q05 median APE 0.314 ± 0.000`
- Warm 비선형 최고:
- `LightGBM median APE 0.119 ± 0.002`
- `CatBoost median APE 0.185 ± 0.009`

### 작가 정보 직접 비교

- `no_artist`
- `median APE 0.4105`
- `Within-30% 0.3905`
- `artist_name`
- `median APE 0.2510`
- `Within-30% 0.5567`
- `artist_works`
- `median APE 0.3133`
- `Within-30% 0.4837`
- `artist_both`
- `median APE 0.2347`
- `Within-30% 0.5792`

### H3 해석

- 작가 정보를 넣으면 Warm 성능이 명확히 좋아짐
- `artist_name_ko`와 `artist_works_log`를 함께 쓰는 경우가 작가 정보 제외 모델보다 가장 좋음
- 작가명 자체는 운영에서 Warm 상황일 때만 사용 가능함
- Cold에서는 신규 작가이므로 작가명 피처를 쓰지 않음

### H3 결론

- 채택 / 보류 / 중단:
- 채택
- 참고 상태:
- H3 검증 완료
- 후속:
- Warm 모델에서는 작가 정보 유지
- 다만 작가 DB 기반 추가 피처는 H10에서 별도 검증

## 7. H4 결과

- 확인 질문:
- 운영 가능한 파생 피처를 추가하면 성능 개선이 반복적으로 확인되는가
- 주요 후보:
- `aspect_ratio`
- `medium_ho_bucket`
- `medium_support_combo`
- `artist_works_log`
- `max_side_cm`
- `is_square_like`
- `log_area_depth`

### PR7 결과

- Cold baseline:
- `median APE 0.429`
- Cold `all`:
- `median APE 0.391`
- 단, `source_platform` 포함 효과가 섞여 있어 운영 채택 근거로는 제한적임
- Warm baseline:
- `median APE 0.115`
- Warm `popularity`
- `median APE 0.103`
- Warm `all`
- `median APE 0.104`

### PR22 결과

- `V0_base`
- Cold `0.4743 ± 0.1029`
- Warm `0.2012 ± 0.0056`
- `F1_combo`
- Cold `0.4776 ± 0.0884`
- Warm `0.1981 ± 0.0053`
- `F2_maxside`
- Cold `0.4753 ± 0.1050`
- Warm `0.2020 ± 0.0100`
- `F3_square`
- Cold `0.4756 ± 0.1015`
- Warm `0.2002 ± 0.0089`
- `F4_area_depth`
- Cold `0.4709 ± 0.1035`
- Warm `0.2024 ± 0.0089`
- 판정:
- release split confirm 후보 없음

### PR23 결과

- Cold `V0_base`
- `median APE 0.3237`
- Cold `V0+combo`
- `median APE 0.3372`
- Warm `V0_base`
- `median APE 0.2055`
- Warm `V0+combo`
- `median APE 0.1911`
- 판정:
- Cold 악화와 tail 지표 불안정 때문에 `medium_support_combo` 채택 실패
- 최종 `V0_base` 유지

### H4 해석

- 파생 피처가 전혀 의미 없다는 결론은 아님
- Warm에서는 `artist_works_log`가 반복적으로 유효함
- `aspect_ratio`는 개선 폭이 작아 보조 후보에 가까움
- `medium_support_combo`, `max_side`, `square`, `area_depth`는 현재 기준 채택 근거가 약함
- `source_platform`은 성능 개선 신호가 있지만 실제 운영 입력에서 알기 어려워 학습 피처로 쓰지 않음

### H4 결론

- 채택 / 보류 / 중단:
- 부분 채택
- 참고 상태:
- H4 검증 완료
- 유지:
- `artist_works_log`
- 보조 후보:
- `aspect_ratio`
- 중단 또는 보류:
- `source_platform`
- `medium_support_combo`
- `max_side_cm`
- `is_square_like`
- `log_area_depth`
- 후속:
- 파생 피처를 넓게 늘리지 않음
- H13/H14/H15처럼 약점 구간을 설명하는 목적형 피처만 별도 가설로 검증

## 8. 최종 정리

- H2:
- 검증 완료
- Cold는 작가 정보 없이 작품 구조 변수만으로 baseline 가능
- H3:
- 검증 완료
- Warm은 작가 정보 포함이 명확히 유리함
- H4:
- 검증 완료
- 파생 피처는 일부만 유지하고, 무분별한 확장은 중단

## 9. 다음 액션

- H2/H3/H4는 현재 기준으로 종결
- 다음 우선순위는 아직 부분 검증 상태인 H7/H8
- 신규 피처 확장은 H13/H14/H15에서 가설 단위로만 진행
