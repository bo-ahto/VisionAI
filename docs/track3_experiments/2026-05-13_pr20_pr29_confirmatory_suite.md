# 2026-05-13 PR20 ~ PR29 확증 실험 기록

- 실험 ID: `PR20_PR29_confirmatory_suite`
- 날짜: 2026-05-13
- 단계: 확증 실험
- 상태: 종결
- 기록 유형:
- 묶음 실험
- 관련 계획 문서:
- [`docs/track3_experiment_plan_v1.md`](/Users/bo/VisionAI/docs/track3_experiment_plan_v1.md:1)
- 관련 결과 파일:
- [`data/track3_pr20_size_redundancy_results.json`](/Users/bo/VisionAI/data/track3_pr20_size_redundancy_results.json)
- [`data/track3_pr21_size_confirm_results.json`](/Users/bo/VisionAI/data/track3_pr21_size_confirm_results.json)
- [`data/track3_pr22_new_features_results.json`](/Users/bo/VisionAI/data/track3_pr22_new_features_results.json)
- [`data/track3_pr23_f1_combo_results.json`](/Users/bo/VisionAI/data/track3_pr23_f1_combo_results.json)
- [`data/track3_pr24_catboost_results.json`](/Users/bo/VisionAI/data/track3_pr24_catboost_results.json)
- [`data/track3_pr25_blend_results.json`](/Users/bo/VisionAI/data/track3_pr25_blend_results.json)
- [`data/track3_pr26_baseline_cache.json`](/Users/bo/VisionAI/data/track3_pr26_baseline_cache.json)
- [`data/track3_pr27_cold_regime_results.json`](/Users/bo/VisionAI/data/track3_pr27_cold_regime_results.json)
- [`data/track3_pr28_knn_results.json`](/Users/bo/VisionAI/data/track3_pr28_knn_results.json)
- [`data/track3_pr29_knn_confirm_results.json`](/Users/bo/VisionAI/data/track3_pr29_knn_confirm_results.json)

## 1. 목적

- mini 신호가 실제 운영 confirm까지 유지되는지 확인
- 기존 개선안을 확증 또는 기각

## 2. 연결 가설

- H1
- H4
- H5
- H7

## 3. 사용 데이터

- 데이터 버전:
- `release_split regenerated on 2026-05-13`
- 학습 데이터:
- `data/release_split/track3_train.csv`
- 검증 데이터:
- mini hold-out / frozen benchmark
- 최종 확인 데이터:
- `data/release_split/track3_test_warm.csv`
- `data/release_split/track3_test_cold.csv`
- 데이터 나누기 기준:
- mini 신호 확인 후 `release_split confirm`

## 4. 사용 변수

- 핵심 변수:
- `medium_category`
- `support_category`
- `depth_cm`
- `width_cm`
- `height_cm`
- `log_area`
- `estimated_ho`
- `orientation`
- 추가 변수:
- `medium_support_combo`
- 크기 단순화 조합
- KNN retrieval feature
- blend gate
- 제외 변수:
- 최종 운영 입력에서 `source_platform` 제외

## 5. 사용 모델

- baseline:
- Cold LAD
- Warm tuned LightGBM
- variant:
- size simplification
- new feature combo
- CatBoost
- rare-artist blend
- frozen benchmark + KNN fallback
- 주요 설정값:
- confirm은 `release_split` 우선
- KNN confirm은 `knn10_a50`, `knn10_a70` 등 비교

## 6. 변경된 요소

- mini에서 신호가 있었던 개선안들을 운영 confirm 기준으로 재평가
- 크기 단순화, 신규 파생 피처, CatBoost, blend, KNN fallback 확인

## 7. 성공 기준

- Warm:
- 기존 tuned LightGBM 대비 악화 없을 것
- Cold:
- 기존 LAD 대비 median APE 개선
- 보조 기준:
- mini 신호가 release_split confirm까지 유지될 것

## 8. 실행 내용

- 실행 스크립트:
- `pr20_size_redundancy.py`
- `pr21_size_v0_v1_confirm.py`
- `pr22_new_features_ablation.py`
- `pr23_f1_combo_confirm.py`
- `pr24_catboost_warm.py`
- `pr25_rare_artist_blend.py`
- `pr26_frozen_cold_benchmark.py`
- `pr27_cold_regime_analysis.py`
- `pr28_knn_retrieval_blend.py`
- `pr29_knn_release_split_confirm.py`
- 산출물:
- `data/track3_pr20_size_redundancy_results.json`
- `data/track3_pr21_size_confirm_results.json`
- `data/track3_pr22_new_features_results.json`
- `data/track3_pr23_f1_combo_results.json`
- `data/track3_pr24_catboost_results.json`
- `data/track3_pr25_blend_results.json`
- `data/track3_pr26_baseline_cache.json`
- `data/track3_pr27_cold_regime_results.json`
- `data/track3_pr28_knn_results.json`
- `data/track3_pr29_knn_confirm_results.json`

## 9. 결과

### F1 크기 변수 단순화

- Cold confirm
- `V0_all 0.3237`
- `V1_log_ho 0.3217`
- Warm confirm
- `V0_all 0.2055`
- `V1_log_ho 0.2277`
- 결론
- Cold 일부 동등 신호는 있었지만 Warm에서 악화
- `V0 유지`

### F2 신규 파생 피처

- mini 단계에서 강한 후보 없음
- confirm
- Cold
- `V0_base 0.3237`
- `V0+combo 0.3372`
- Warm
- `V0_base 0.2055`
- `V0+combo 0.1911`
- 결론
- Warm 일부 이득만으로는 부족
- Cold 악화 때문에 운영 채택 실패

### F3 CatBoost vs LightGBM

- Warm LGB
- `0.2012 ± 0.0056`
- Warm CatBoost
- `0.2679 ± 0.0060`
- 결론
- `LightGBM 유지`

### F4 rare-artist blend

- baseline
- `0.2012 ± 0.0056`
- 모든 blend variant
- 채택 실패
- 결론
- `Warm 100% 유지`

### F5 / F6 frozen benchmark + KNN fallback

- frozen benchmark baseline
- `0.4504`
- KNN mini
- `0.4288`, `0.4352`
- release split confirm
- `V0 0.3237`
- `knn10_a50 0.3628`
- `knn10_a70 0.3598`
- 결론
- KNN fallback 기각
- frozen benchmark 인프라만 유지 가치 있음

### Warm 요약

- 사용 변수 요약:
- 기본 Warm 변수 + feature combo / CatBoost / blend 후보
- 핵심 결과:
- `LightGBM` 유지
- CatBoost와 blend 계열 모두 confirm 실패

### Cold 요약

- 사용 변수 요약:
- 기본 Cold 변수 + 크기 단순화 / feature combo / KNN fallback 후보
- 핵심 결과:
- 크기 단순화, KNN fallback 모두 confirm 실패
- frozen benchmark는 인프라 가치만 있음

## 10. 해석

- mini 단계 신호가 confirm까지 이어지지 않는 경우가 많았음
- 운영 구조를 바꾸려면 mini가 아니라 `release_split confirm`을 통과해야 함
- 현재 운영 구조 `Cold = LAD`, `Warm = tuned LightGBM`는 여전히 유지가 맞음

## 11. 결론

- 상태:
- 종결
- 핵심 결론:
- mini에서 좋아 보여도 confirm에서 유지되지 않는 경우가 많았음
- 현재 운영 구조인 `Cold = LAD`, `Warm = tuned LightGBM`를 바꿀 근거는 확보되지 않음
- 채택 / 보류 / 중단:
- 중단
- 이유:
- confirm 단계에서 운영 대체안으로 채택할 근거를 확보하지 못함
- 참고 상태:
- 종결

## 12. 다음 액션

- 전체 구조 교체보다 slice 한정 보완 실험 우선
- 특히 `Cold 2D` 한정 fallback 가설을 다음 우선순위로 둠
